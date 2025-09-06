🎓 Academic Study Assistant

An AI-powered study assistant for university students that answers questions about your course materials using Retrieval-Augmented Generation (RAG).

⸻

✨ Features
	•	Smart Document Processing: PDFs (lectures, textbooks, papers) with optional AI OCR for scanned pages.
	•	Advanced RAG: Hybrid retrieval (BM25 + dense), multi-query expansion, contextual compression, and cross-encoder re-ranking.
	•	Friendly Web UI: Built with Streamlit.
	•	FastAPI Backend: Simple REST API for chatting and health checks.
	•	Source Awareness: Chunks include metadata (source file, page, type, etc.).

⸻

🧱 Repository Structure

Rag-Pipeline/
├── ask_pdf.py             # CLI: interactive Q&A over your docs
├── chromadbpdf.py         # Ingest PDFs -> Chroma (embeddings)
├── rag_api.py             # FastAPI server
├── rag_pipeline.py        # RAG wrapper used by the API
├── streamlit_app.py       # Streamlit front-end (web chat)
├── view_embeddings.py     # Inspect Chroma collection
├── requirements.txt       # Dependencies
└── README.md              # This file

Note: The previous student_interface.html flow has been replaced by the Streamlit app (streamlit_app.py).

⸻

🔧 Prerequisites
	•	Python 3.8+ (3.10 recommended)
	•	pip (or uv/pipx/conda)
	•	Optional: CUDA GPU (for faster embeddings)

⸻

🚀 Quick Start

1) Install dependencies

pip install -r requirements.txt

2) Configure environment

Create a .env file in the repo root:

OPENAI_API_KEY=your_openai_api_key
# Optional OCR tuning
OPENAI_OCR_MODEL=gpt-4o-mini
OCR_DPI=220

3) Add your documents

mkdir -p university_documents
# Place your PDFs inside this folder

4) Ingest documents (build embeddings)

python chromadbpdf.py

This creates/updates the Chroma database in ./academic_db/.

5) Start the API (Terminal #1)

python rag_api.py

	•	Health check: http://localhost:8000/health
	•	OpenAPI/Swagger: http://localhost:8000/docs

6) Launch the Streamlit UI (Terminal #2)

streamlit run streamlit_app.py

	•	Visit the app (usually): http://localhost:8501
	•	In the sidebar, click 🔄 Check Connection to verify the API is healthy.

That’s it — ask questions about your PDFs!

⸻

💻 Running in PyCharm (recommended)

Create two Run/Debug configurations:
	1.	API
	•	Type: Python
	•	Script path: rag_api.py
	•	Working directory: project root
	•	Environment variables: load from .env or add OPENAI_API_KEY=...
	2.	Streamlit
	•	Type: Python
	•	Module name: streamlit
	•	Parameters: run streamlit_app.py
	•	Working directory: project root

Optional third config for ingestion: chromadbpdf.py.

⸻

🧪 Alternative Interfaces
	•	CLI: python ask_pdf.py — interactive terminal Q&A.
	•	API:

# Health
curl http://localhost:8000/health

# Ask a question
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "What is supervised learning?", "student_name": "Alex"}'



API Endpoints
	•	GET / — basic info
	•	GET /health — checks RAG and returns status
	•	POST /chat — body: { message: str, student_name?: str }
	•	POST /process-documents — re-run ingestion (calls chromadbpdf.py)

⸻

🧠 How it Works (RAG flow)
	1.	Ingestion (chromadbpdf.py):
	•	Extract text via PyMuPDF; fallback to OpenAI Vision OCR for low-text pages.
	•	Split into chunks; attach rich metadata; embed with MiniLM.
	•	Store in ChromaDB under academic_docs.
	2.	Retrieval (ask_pdf.py):
	•	Hybrid retriever (BM25 + dense) → multi-query expansion → contextual compression.
	•	Re-rank with a cross-encoder for final ordering.
	3.	Generation: Student-friendly prompt with citations-style guidance.

⸻

🔐 Configuration
	•	.env variables (all optional except OPENAI_API_KEY):

OPENAI_API_KEY=...
OPENAI_OCR_MODEL=gpt-4o-mini
OCR_DPI=220


	•	Adjust text chunking or content typing in chromadbpdf.py.

⸻

🛠 Troubleshooting
	1.	“Academic database not found” / empty answers
	•	Ensure PDFs are in university_documents/ and run python chromadbpdf.py.
	2.	/health returns 503
	•	The RAG pipeline may not have initialized; check .env, ingestion, and API logs.
	3.	OpenAI errors
	•	Verify OPENAI_API_KEY and account credits; ensure your network allows outbound requests.
	4.	Port conflicts
	•	API uses 8000, Streamlit uses 8501. Free those ports or change them.
	5.	CORS / Connection status shows offline
	•	The API sets permissive CORS; confirm the API is running and reachable from your machine.
	6.	OCR slow or unavailable
	•	OCR is best-effort. You can disable by leaving OPENAI_API_KEY unset (scanned PDFs may then yield less text).
	7.	GPU not used
	•	If you have CUDA, chromadbpdf.py will switch to GPU automatically for embeddings; otherwise it uses CPU.

⸻

📊 Inspect the Vector DB

python view_embeddings.py

Shows total docs/chunks, sample text, and embedding stats.

⸻

🧩 Customization
	•	Prompt tone/behavior: Edit the prompt in ask_pdf.py.
	•	Chunking strategy: Tweak chunk_size / chunk_overlap in chromadbpdf.py.
	•	Types/metadata: Adjust content_type assignment logic per filename patterns.

⸻

📄 License

MIT