import logging
import os
import pickle
from dotenv import load_dotenv

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

# Re-ranking (optional, kept as-is)
from sentence_transformers import CrossEncoder

logging.basicConfig(level=logging.INFO)

# ---------- LLM provider selection (LOCAL by default) ----------
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


# -------- Embeddings cache --------
def load_or_initialize_embeddings():
    if os.path.exists("academic_embeddings.pkl"):
        logging.info("Loading cached embeddings...")
        with open("academic_embeddings.pkl", "rb") as f:
            embeddings = pickle.load(f)
        return embeddings
    logging.info("Initializing new academic embeddings...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    with open("academic_embeddings.pkl", "wb") as f:
        pickle.dump(embeddings, f)
    return embeddings


# -------- Optional cross-encoder re-ranking --------
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query, docs):
    if not docs:
        return []
    pairs = [[query, d.page_content] for d in docs]
    scores = cross_encoder.predict(pairs)
    return [doc for _, doc in sorted(zip(scores, docs), reverse=True)]


# -------- LLM factory --------
def _make_llm(model_type: str = "general"):
    """
    model_type: "general" | "math"
    """
    load_dotenv(override=True)

    if LLM_PROVIDER == "openai":
        if not _openai_available:
            raise RuntimeError("LLM_PROVIDER=openai but langchain-openai is not installed.")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("LLM_PROVIDER=openai requires OPENAI_API_KEY.")
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logging.info(f"Using OpenAI chat model: {model_name}")
        return ChatOpenAI(model=model_name, temperature=0.1, max_tokens=1024)

    if _chatollama is None:
        raise RuntimeError("Ollama not available")

    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    if model_type == "math":
        model = os.getenv("OLLAMA_MODEL_MATH", "qwen-4b-math")  # your local Ollama model name
    else:
        model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    logging.info(f"Using Ollama model: {model}")
    # Keep generation short so requests don't hang
    return _chatollama(
        base_url=base_url,
        model=model,
        temperature=0.1,
        num_predict=256,
        keep_alive="5m",
        request_timeout=30.0,
    )


# -------- RAG init (lightweight) --------
def initialize_rag_system(model_type: str = "general"):
    """
    Build a lightweight QA chain with a simple hybrid retriever.
    Pass model_type="math" to bind the math model.
    """
    load_dotenv(override=True)

    embeddings = load_or_initialize_embeddings()

    persist_directory = "./academic_db"
    if not os.path.exists(persist_directory):
        logging.error("Academic database not found! Run chromadbpdf.py first.")
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

    # Load documents once to build a BM25 retriever
    logging.info("Loading documents for BM25 keyword search...")
    all_docs = vector_db.similarity_search("placeholder", k=coll_count)
    if not all_docs:
        logging.error("Could not load any documents for BM25; check your Chroma collection.")
        return None

    # Sparse (keyword) and dense retrievers (keep k small)
    bm25 = BM25Retriever.from_documents(all_docs)
    bm25.k = 3
    dense = vector_db.as_retriever(search_kwargs={"k": 3})

    retriever = EnsembleRetriever(
        retrievers=[bm25, dense],
        weights=[0.5, 0.5],
    )

    # LLM
    llm = _make_llm(model_type=model_type)

    # Student-friendly prompt
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

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=True,
    )

    logging.info("Academic Study Assistant RAG System initialized")
    return qa_chain


# -------- (optional) CLI loop --------
def ask_questions(qa_chain):
    logging.info("🎓 Academic Study Assistant Ready!")
    logging.info("Ask me anything about your course materials!")
    logging.info("Type 'exit' to quit")

    while True:
        question = input("\nEnter your question: ").strip()
        if question.lower() in ["exit", "quit", "q"]:
            break
        try:
            result = qa_chain.invoke({"query": question})
            reranked = rerank(question, result.get("source_documents", []))
            logging.info("\nAnswer:\n" + result.get("result", ""))
            logging.info("\n📖 Sources:")
            for i, doc in enumerate(reranked[:3], 1):
                src = doc.metadata.get("source", "Unknown")
                page = doc.metadata.get("page_number", "?")
                ctype = doc.metadata.get("content_type", "document")
                logging.info(f"{i}. {src} (Page {page}) - {ctype}")
        except Exception as e:
            logging.error(f"Error: {e}")


def main():
    qa_chain = initialize_rag_system()
    if qa_chain:
        ask_questions(qa_chain)

if __name__ == "__main__":
    main()