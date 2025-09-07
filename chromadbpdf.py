import os
import io
import re
import uuid
import logging
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

import fitz  # PyMuPDF
from PIL import Image
import torch

from dotenv import load_dotenv
load_dotenv(override=True)

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------- Local OCR config ----------------
# Choose OCR engine via env:
#   OCR_BACKEND=tesseract|paddle (default: tesseract)
#   OCR_DPI=220 (render DPI for scanned pages)
#   OCR_LANG=eng (Tesseract languages, e.g., "eng+deu")
#   PADDLE_LANG=en (PaddleOCR language code)
#   PADDLE_USE_ANGLE=1|0 (angle classification)
OCR_BACKEND = os.getenv("OCR_BACKEND", "tesseract").strip().lower()
OCR_DPI = int(os.getenv("OCR_DPI", "220"))
OCR_LANG = os.getenv("OCR_LANG", "eng")
PADDLE_LANG = os.getenv("PADDLE_LANG", "en")
PADDLE_USE_ANGLE = bool(int(os.getenv("PADDLE_USE_ANGLE", "1")))

# Try import OCR backends
_has_pytesseract = False
_has_paddle = False
try:
    import pytesseract
    _has_pytesseract = True
except Exception:
    logging.info("pytesseract not available — install it for Tesseract OCR.")

try:
    from paddleocr import PaddleOCR
    _has_paddle = True
except Exception:
    if OCR_BACKEND == "paddle":
        logging.info("PaddleOCR not available — `pip install paddleocr paddlepaddle` for Paddle OCR.")

# ---------------- Helpers ----------------
def normalize_ws(text: str) -> str:
    text = re.sub(r"[ \t\u00A0]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def render_page_png(page: fitz.Page, dpi: int = OCR_DPI) -> bytes:
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    return pix.tobytes("png")

# ---------------- OCR backends ----------------
_paddle_ocr: Optional["PaddleOCR"] = None

def _ensure_paddle():
    global _paddle_ocr
    if _paddle_ocr is None and _has_paddle:
        logging.info(f"Initializing PaddleOCR(lang={PADDLE_LANG}, angle_cls={PADDLE_USE_ANGLE})")
        _paddle_ocr = PaddleOCR(use_angle_cls=PADDLE_USE_ANGLE, lang=PADDLE_LANG, show_log=False)
    return _paddle_ocr

def ocr_with_tesseract(img_bytes: bytes) -> str:
    if not _has_pytesseract:
        return ""
    try:
        img = Image.open(io.BytesIO(img_bytes))
        txt = pytesseract.image_to_string(img, lang=OCR_LANG)
        return normalize_ws(txt or "")
    except Exception as e:
        logging.warning(f"Tesseract OCR failed: {e}")
        return ""

def ocr_with_paddle(img_bytes: bytes) -> str:
    if not _has_paddle:
        return ""
    try:
        import numpy as np
        ocr_engine = _ensure_paddle()
        if ocr_engine is None:
            return ""
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        arr = np.array(img)
        result = ocr_engine.ocr(arr, cls=PADDLE_USE_ANGLE)
        lines = []
        if result:
            for page in result:
                if not page:
                    continue
                for line in page:
                    if len(line) >= 2 and line[1]:
                        lines.append(line[1][0])
        return normalize_ws("\n".join(lines))
    except Exception as e:
        logging.warning(f"PaddleOCR failed: {e}")
        return ""

def ocr_png_locally(img_bytes: bytes) -> str:
    """Try requested backend first, then fall back to the other if available."""
    if OCR_BACKEND == "paddle":
        text = ocr_with_paddle(img_bytes)
        if text:
            return text
        return ocr_with_tesseract(img_bytes)
    else:
        text = ocr_with_tesseract(img_bytes)
        if text:
            return text
        return ocr_with_paddle(img_bytes)

# ---------------- Extraction ----------------
def extract_text_from_pdf(pdf_path: str) -> List[Tuple[int, str]]:
    """
    Extract text from a PDF, page by page.
    - Uses PyMuPDF text first.
    - Falls back to LOCAL OCR if the page text is empty/very short (scanned).
    """
    try:
        doc = fitz.open(pdf_path)
        text_pages = []
        for page_num, page in enumerate(doc, start=1):
            text = (page.get_text("text") or "").strip()

            # If likely scanned / low text, try OCR
            if len(text) < 25:
                try:
                    img_bytes = render_page_png(page, dpi=OCR_DPI)
                    ocr_text = ocr_png_locally(img_bytes)
                    if len(ocr_text) > len(text):
                        text = ocr_text
                except Exception as e:
                    logging.warning(f"OCR fallback failed for page {page_num} in {pdf_path}: {e}")

            if text.strip():
                text_pages.append((page_num, text.strip()))
        doc.close()
        return text_pages
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path}: {e}")
        return []

def process_pdf(pdf_file: str, pdf_dir: str, text_splitter: RecursiveCharacterTextSplitter):
    """
    Extract and split PDF text into chunks. Adds richer metadata and stable IDs.
    """
    full_path = os.path.join(pdf_dir, pdf_file)
    pages = extract_text_from_pdf(full_path)

    # stable per-file document_id based on file path URI
    try:
        document_id = uuid.uuid5(uuid.NAMESPACE_URL, Path(full_path).resolve().as_uri()).hex
    except Exception:
        document_id = uuid.uuid4().hex

    chunks, metadata_list, ids = [], [], []
    upload_date = datetime.now().strftime("%Y-%m-%d")

    for page_num, text in pages:
        split_chunks = [c.strip() for c in text_splitter.split_text(text)]
        for i, chunk in enumerate(split_chunks):
            if len(chunk) < 30:
                continue
            chunks.append(chunk)
            metadata_list.append({
                "source": pdf_file,
                "source_path": str(Path(full_path).resolve()),
                "page_number": page_num,
                "chunk_id": i,
                "document_id": document_id,
                "document_type": "Academic Document",
                "subject": "General",
                "upload_date": upload_date,
                "content_type": (
                    "lecture_notes" if "lecture" in pdf_file.lower()
                    else "textbook" if "textbook" in pdf_file.lower()
                    else "research_paper" if "paper" in pdf_file.lower()
                    else "general"
                )
            })
            ids.append(f"{document_id}-p{page_num}-c{i}")

    return chunks, metadata_list, ids, document_id

def process_all_pdfs():
    # Config
    pdf_dir = "university_documents"
    persist_directory = "./academic_db"
    collection_name = "academic_docs"

    if not os.path.exists(pdf_dir):
        logging.error(f"Directory '{pdf_dir}' does not exist!")
        return

    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        logging.error("No PDF files found!")
        return
    logging.info(f"Found {len(pdf_files)} PDF files to process.")

    # Device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logging.info(f"Using device: {device}")

    # Embeddings (local)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": device},
    )
    logging.info("Academic embedding model loaded successfully.")

    # Text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )

    # Open or create ChromaDB
    vector_db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name=collection_name,
    )

    # Collect all chunks
    all_chunks, all_metadatas, all_ids = [], [], []

    def _work(pdf):
        return process_pdf(pdf, pdf_dir, text_splitter)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(_work, pdf_files)
        for pdf_file, (chunks, metadatas, ids, document_id) in zip(pdf_files, results):
            if not chunks:
                logging.warning(f"Skipping empty PDF (no extractable text): {pdf_file}")
                continue
            all_chunks.extend(chunks)
            all_metadatas.extend(metadatas)
            all_ids.extend(ids)
            logging.info(f"Prepared {len(chunks)} chunks from {pdf_file} (document_id={document_id}).")

    if not all_chunks:
        logging.info("No chunks to add. Exiting.")
        return

    logging.info(f"Adding {len(all_chunks)} chunks to ChromaDB (this embeds; may take a while)...")
    vector_db.add_texts(texts=all_chunks, metadatas=all_metadatas, ids=all_ids)

    try:
        collection_size = vector_db._collection.count()
    except Exception:
        collection_size = "unknown"
    logging.info(f"Finished processing. Total chunks in ChromaDB: {collection_size}")

if __name__ == "__main__":
    process_all_pdfs()