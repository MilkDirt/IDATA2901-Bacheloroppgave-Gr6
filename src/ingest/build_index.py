"""
Document ingestion pipeline (PDF -> chunks -> embeddings -> FAISS index).

This script:
1) Loads PDF files from settings.data_dir
2) Extracts text page-by-page
3) Splits text into overlapping chunks
4) Creates embeddings for each chunk using NTNU's OpenAI-compatible API
5) Stores the vectors in a FAISS index + writes metadata to JSONL

Run:
    python -m src.ingest.build_index

Output:
    vectorstore/index.faiss
    vectorstore/meta.jsonl
"""

from __future__ import annotations

import os
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

import httpx
import numpy as np
import faiss
from pypdf import PdfReader
from openai import OpenAI

from src.config import settings, validate_settings


# ---- Tuning knobs for stability (NTNU endpoint can be slow/busy) ----
EMBED_BATCH_SIZE = 8
BATCH_SLEEP_SECONDS = 0.2
HTTP_TIMEOUT_SECONDS = 120.0
MAX_RETRIES = 5


@dataclass(frozen=True)
class ChunkMeta:
    """
    Metadata stored for each chunk in the vector store.

    We keep this so we can show sources (file + page) in the final answer.
    """
    source_file: str
    page: int
    chunk_id: int
    text: str


class PdfLoader:
    """
    Loads text from PDF pages using PyPDF.

    Note:
        If the PDF is scanned (image-only), extract_text() may return empty.
    """

    def load_pdf_text_by_page(self, pdf_path: str) -> List[Tuple[int, str]]:
        """
        Returns a list of (page_number, page_text) for pages containing text.
        Page numbers are 1-based.
        """
        reader = PdfReader(pdf_path)
        pages: List[Tuple[int, str]] = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = " ".join(text.split())  # normalize whitespace
            if text.strip():
                pages.append((i + 1, text))

        return pages


class Chunker:
    """
    Splits long text into overlapping chunks.

    Overlap helps preserve context across chunk boundaries,
    which improves retrieval quality later.
    """

    def __init__(self, chunk_size: int, overlap: int):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap."""
        if len(text) <= self.chunk_size:
            return [text]

        chunks: List[str] = []
        start = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end])

            if end >= len(text):
                break

            # Move start forward, but keep overlap
            start = max(0, end - self.overlap)

        return chunks


class Embedder:
    """
    Calls the embeddings endpoint and converts text chunks into vectors.
    """

    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Embed a batch of texts and return a (batch_size, dim) float32 matrix.
        """
        resp = self.client.embeddings.create(model=self.model, input=texts)
        vectors = [item.embedding for item in resp.data]
        return np.array(vectors, dtype=np.float32)


def ensure_dirs() -> None:
    """Ensure output directory exists."""
    os.makedirs(settings.vectorstore_dir, exist_ok=True)


def iter_pdf_paths(data_dir: str) -> Iterable[str]:
    """Yield absolute paths to PDF files inside data_dir."""
    for fname in os.listdir(data_dir):
        if fname.lower().endswith(".pdf"):
            yield os.path.join(data_dir, fname)


def save_meta_jsonl(meta_path: str, meta: List[ChunkMeta]) -> None:
    """Write metadata as JSONL (one JSON object per line)."""
    with open(meta_path, "w", encoding="utf-8") as f:
        for m in meta:
            f.write(json.dumps(m.__dict__, ensure_ascii=False) + "\n")


def build_index() -> None:
    """
    Main entry point: build FAISS index + metadata file from PDFs in settings.data_dir.
    """
    validate_settings()
    ensure_dirs()

    # Create OpenAI-compatible client for NTNU endpoint
    client = OpenAI(
        api_key=settings.ntnu_api_key,
        base_url=settings.ntnu_base_url,
        timeout=HTTP_TIMEOUT_SECONDS,
        max_retries=MAX_RETRIES,
        http_client=httpx.Client(timeout=HTTP_TIMEOUT_SECONDS),
    )

    pdf_loader = PdfLoader()
    chunker = Chunker(settings.chunk_size, settings.chunk_overlap)
    embedder = Embedder(client, settings.embed_model)

    # 1) Collect all chunks + metadata
    all_chunks: List[str] = []
    meta: List[ChunkMeta] = []

    for pdf_path in iter_pdf_paths(settings.data_dir):
        source_file = os.path.basename(pdf_path)
        pages = pdf_loader.load_pdf_text_by_page(pdf_path)

        for page_no, page_text in pages:
            chunks = chunker.chunk_text(page_text)
            for chunk_id, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                meta.append(
                    ChunkMeta(
                        source_file=source_file,
                        page=page_no,
                        chunk_id=chunk_id,
                        text=chunk,
                    )
                )

    if not all_chunks:
        raise RuntimeError(
            f"No PDF text found in '{settings.data_dir}'. "
            "Make sure the PDF contains selectable text (not scanned images)."
        )

    # 2) Embed chunks in batches
    vectors_list: List[np.ndarray] = []
    for i in range(0, len(all_chunks), EMBED_BATCH_SIZE):
        batch = all_chunks[i : i + EMBED_BATCH_SIZE]

        # Small delay to avoid hammering the endpoint
        time.sleep(BATCH_SLEEP_SECONDS)

        vectors = embedder.embed_texts(batch)
        vectors_list.append(vectors)

    embeddings = np.vstack(vectors_list)
    dim = embeddings.shape[1]

    # 3) Build FAISS index using cosine similarity
    # Cosine similarity can be approximated using inner product if vectors are L2-normalized.
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    # 4) Save index + metadata
    faiss_path = os.path.join(settings.vectorstore_dir, "index.faiss")
    meta_path = os.path.join(settings.vectorstore_dir, "meta.jsonl")

    faiss.write_index(index, faiss_path)
    save_meta_jsonl(meta_path, meta)

    print(f" Built index with {len(meta)} chunks")
    print(f"   Index: {faiss_path}")
    print(f"   Meta : {meta_path}")


if __name__ == "__main__":
    build_index()
