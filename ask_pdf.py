import logging
import os
import pickle
from dotenv import load_dotenv

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

# Re-ranking
from sentence_transformers import CrossEncoder

logging.basicConfig(level=logging.INFO)

# ---------- LLM provider selection (LOCAL by default) ----------
# Tries Ollama first (local), but you can force OpenAI with LLM_PROVIDER=openai
# Env vars:
#   LLM_PROVIDER=ollama|openai (default: ollama)
#   OLLAMA_BASE_URL (default: http://localhost:11434)
#   OLLAMA_MODEL (default: llama3.1:8b)
#   OPENAI_API_KEY (only if LLM_PROVIDER=openai)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

_openai_available = False
try:
    from langchain_openai import ChatOpenAI
    _openai_available = True
except Exception:
    pass

# ChatOllama lives in either langchain_ollama (new) or langchain_community.chat_models (older).
_chatollama = None
try:
    from langchain_ollama import ChatOllama  # newer package
    _chatollama = ChatOllama
except Exception:
    try:
        from langchain_community.chat_models import ChatOllama  # fallback
        _chatollama = ChatOllama
    except Exception:
        _chatollama = None


#  Load or initialize embeddings
def load_or_initialize_embeddings():
    if os.path.exists("academic_embeddings.pkl"):
        logging.info("Loading cached embeddings...")
        with open("academic_embeddings.pkl", "rb") as f:
            embeddings = pickle.load(f)
        return embeddings
    else:
        logging.info("Initializing new academic embeddings...")
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        with open("academic_embeddings.pkl", "wb") as f:
            pickle.dump(embeddings, f)
        return embeddings


#  Cross-encoder re-ranking
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query, docs):
    """Re-rank retrieved documents by semantic relevance."""
    if not docs:
        return []
    pairs = [[query, d.page_content] for d in docs]
    scores = cross_encoder.predict(pairs)
    sorted_docs = [doc for _, doc in sorted(zip(scores, docs), reverse=True)]
    return sorted_docs


def _make_llm():
    """
    Create the chat LLM.
    - Default: LOCAL via Ollama (no API key required).
    - If LLM_PROVIDER=openai and key present: use OpenAI.
    """
    load_dotenv(override=True)

    if LLM_PROVIDER == "openai":
        if not _openai_available:
            raise RuntimeError("LLM_PROVIDER=openai but langchain-openai is not installed.")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("LLM_PROVIDER=openai requires OPENAI_API_KEY.")
        logging.info("Using OpenAI chat model (cloud).")
        return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.1, max_tokens=1024)

    # Otherwise use Ollama locally
    if _chatollama is None:
        raise RuntimeError(
            "Ollama selected but ChatOllama not available. Install either 'langchain-ollama' "
            "or upgrade langchain-community to a version that includes ChatOllama."
        )

    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    logging.info(f"Using LOCAL Ollama model: {model} @ {base_url}")
    # You can pass extra params like num_ctx if needed, e.g., num_ctx=8192
    return _chatollama(base_url=base_url, model=model, temperature=0.1)


#  Initialize  RAG system
def initialize_rag_system():
    load_dotenv(override=True)

    embeddings = load_or_initialize_embeddings()

    # Connect to ChromaDB
    persist_directory = "./academic_db"
    if not os.path.exists(persist_directory):
        logging.error("Academic database not found! Please run chromadbpdf.py first to process your documents.")
        return None

    vector_db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name="academic_docs",
    )

    try:
        coll_count = vector_db._collection.count()
    except Exception:
        coll_count = 0

    if coll_count == 0:
        logging.error("No documents found in ChromaDB!")
        return None

    logging.info(f"Found {coll_count} documents in ChromaDB")

    # Load all docs for BM25 keyword search (note: this can be heavy for large collections)
    logging.info("Loading documents for BM25 keyword search...")
    all_docs = vector_db.similarity_search("placeholder", k=coll_count)
    if not all_docs:
        logging.error("Could not load any documents for BM25; check your Chroma collection.")
        return None

    bm25_retriever = BM25Retriever.from_documents(all_docs)
    bm25_retriever.k = 5

    # Dense retriever
    dense_retriever = vector_db.as_retriever(search_kwargs={"k": 5})

    # Hybrid retrieval
    hybrid_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, dense_retriever],
        weights=[0.5, 0.5],
    )

    # Create LLM (local by default)
    llm = _make_llm()

    # Multi-query retrieval
    multi_query_retriever = MultiQueryRetriever.from_llm(
        retriever=hybrid_retriever,
        llm=llm,
    )

    # Contextual compression
    compressor = LLMChainExtractor.from_llm(llm)
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=multi_query_retriever,
    )

    # Student-friendly prompt with citations
    prompt_template = """
    You are a helpful academic assistant for university students. Use ONLY the provided academic documents to answer questions.

    Guidelines:
    - Provide clear, educational explanations suitable for students
    - Include source citations in square brackets after each relevant fact
    - If the question is about concepts not in the documents, explain what you can from the available material
    - Use examples and analogies when helpful for understanding
    - If unsure or information is incomplete, say: "Based on the available materials, [your answer]. For more complete information, you may need to consult additional resources."
    - Be encouraging and supportive in your tone

    Context from academic materials:
    {context}

    Student's question:
    {question}

    Helpful answer:
    """
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

    # Retrieval QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=compression_retriever,
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=True,
    )

    logging.info("Academic Study Assistant RAG System initialized")
    return qa_chain


#  Ask questions loop
def ask_questions(qa_chain):
    logging.info("🎓 Academic Study Assistant Ready!")
    logging.info("Ask me anything about your course materials!")
    logging.info("Type 'exit' to quit")

    while True:
        question = input("\nEnter your question: ").strip()
        if question.lower() in ["exit", "quit", "q"]:
            break

        try:
            # Retrieve
            logging.info("Retrieving documents...")
            result = qa_chain.invoke({"query": question})

            # Re-rank docs
            reranked_docs = rerank(question, result.get("source_documents", []))

            # Display answer
            logging.info("\n Answer:")
            logging.info(result.get("result", ""))

            # Show top sources
            logging.info("\n📖 Sources:")
            for i, doc in enumerate(reranked_docs[:3], 1):
                source = doc.metadata.get("source", "Unknown")
                content_type = doc.metadata.get("content_type", "document")
                page_num = doc.metadata.get("page_number", "?")
                logging.info(f"{i}. {source} (Page {page_num}) - {content_type}")

        except Exception as e:
            logging.error(f" Error: {e}")


def main():
    qa_chain = initialize_rag_system()
    if qa_chain:
        ask_questions(qa_chain)

if __name__ == "__main__":
    main()