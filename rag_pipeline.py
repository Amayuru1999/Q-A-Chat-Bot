from ask_pdf import initialize_rag_system, _make_llm

qa_chain_general = initialize_rag_system()  # default llama-based pipeline

# Math pipeline: reuses same retriever but with Qwen model
qa_chain_math = None
try:
    llm_math = _make_llm(model_type="math")
    qa_chain_math = initialize_rag_system()
    qa_chain_math.combine_documents_chain.llm_chain.llm = llm_math
except Exception as e:
    print(f"Math model not available: {e}")

def rag_pipeline(query, mode="general"):
    """Invoke RAG with chosen model"""
    chain = qa_chain_math if mode == "math" and qa_chain_math else qa_chain_general
    if not chain:
        return "RAG system is not initialized properly."
    try:
        result = chain.invoke({"query": query})
        return result["result"]
    except Exception as e:
        return f"Error: {e}"