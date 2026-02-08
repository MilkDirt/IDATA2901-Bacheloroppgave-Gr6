"""
RAG answering logic.

This module:
- Embeds user questions
- Retrieves relevant document chunks from the vector store
- Uses an LLM to generate grounded answers with citations
"""

import os
import json
from typing import List, Dict, Any

import numpy as np
import faiss
from openai import OpenAI

from src.config import settings, validate_settings


class VectorStore:
    """
    Wrapper around a FAISS vector index and its metadata.

    Responsible for performing similarity search over
    embedded document chunks.
    """

    def __init__(self, index_path: str, meta_path: str):
        self.index = faiss.read_index(index_path)
        self.meta = self._load_meta(meta_path)

    def _load_meta(self, meta_path: str) -> List[Dict[str, Any]]:
        """Load metadata associated with each vector."""
        meta = []
        with open(meta_path, "r", encoding="utf-8") as f:
            for line in f:
                meta.append(json.loads(line))
        return meta

    def search(self, query_vec: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """
        Perform similarity search in the vector index.

        Args:
            query_vec (np.ndarray): Embedded user query.
            top_k (int): Number of top matches to retrieve.

        Returns:
            List[Dict]: Matching document chunks with metadata.
        """
        q = query_vec.reshape(1, -1)
        scores, ids = self.index.search(q, top_k)

        results = []
        for score, idx in zip(scores[0], ids[0]):
            if idx == -1:
                continue
            item = dict(self.meta[idx])
            item["score"] = float(score)
            results.append(item)

        return results


class RAGAnswerer:
    """
    High-level RAG component.

    Combines:
    - Embedding model
    - Vector search
    - LLM-based answer generation
    """

    def __init__(self, client: OpenAI, vectorstore: VectorStore):
        self.client = client
        self.vectorstore = vectorstore

    def _embed_query(self, text: str) -> np.ndarray:
        """
        Convert a user question into an embedding vector.
        """
        resp = self.client.embeddings.create(
            model=settings.embed_model,
            input=[text]
        )
        vec = np.array(resp.data[0].embedding, dtype=np.float32)
        faiss.normalize_L2(vec.reshape(1, -1))
        return vec

    def answer(self, question: str) -> Dict[str, Any]:
        """
        Answer a user question using Retrieval-Augmented Generation.

        Steps:
        1. Embed the question
        2. Retrieve relevant document chunks
        3. Generate answer using the LLM

        Args:
            question (str): User question.

        Returns:
            dict: Answer text and source references.
        """
        qvec = self._embed_query(question)
        hits = self.vectorstore.search(qvec, settings.top_k)

        # Build context for the language model
        context_blocks = []
        sources = []

        for h in hits:
            context_blocks.append(
                f"[{h['source_file']} | side {h['page']}]\n{h['text']}"
            )
            sources.append({
                "source_file": h["source_file"],
                "page": h["page"],
                "score": h["score"]
            })

        context = "\n\n---\n\n".join(context_blocks)

        system_prompt = (
            "Du er en faglig assistent. "
            "Svar kun basert på KONTEXTEN. "
            "Hvis svaret ikke finnes i dokumentasjonen, si det tydelig. "
            "Avslutt svaret med kildehenvisning."
        )

        user_prompt = f"""KONTEXT:
{context}

SPØRSMÅL:
{question}
"""

        resp = self.client.chat.completions.create(
            model=settings.chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

        return {
            "question": question,
            "answer": resp.choices[0].message.content,
            "sources": sources
        }


def get_answerer() -> RAGAnswerer:
    """
    Factory method for creating a configured RAGAnswerer.
    """
    validate_settings()

    client = OpenAI(
        api_key=settings.ntnu_api_key,
        base_url=settings.ntnu_base_url
    )

    index_path = os.path.join(settings.vectorstore_dir, "index.faiss")
    meta_path = os.path.join(settings.vectorstore_dir, "meta.jsonl")

    if not os.path.exists(index_path) or not os.path.exists(meta_path):
        raise RuntimeError("Vector store not built. Run build_index first.")

    vectorstore = VectorStore(index_path, meta_path)
    return RAGAnswerer(client, vectorstore)
