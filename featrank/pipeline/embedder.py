"""sentence-transformers wrapper with disk-based embedding cache."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Sequence

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer

from featrank.config import settings


class Embedder:
    """Embed text with sentence-transformers.

    Embeddings are cached to disk keyed by (model_name, sha256(text)).
    Recomputing embeddings for the same inputs is never required.
    """

    def __init__(
        self,
        model_name: str | None = None,
        cache_dir: str | None = None,
        batch_size: int | None = None,
    ) -> None:
        self.model_name = model_name or settings.embedding_model
        self.cache_dir = Path(cache_dir or settings.cache_dir)
        self.batch_size = batch_size or settings.embedding_batch_size
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info(f"[embedder] Loading model: {self.model_name}")
            t0 = time.perf_counter()
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"[embedder] Model loaded in {time.perf_counter() - t0:.2f}s")
        return self._model

    def _cache_key(self, text: str) -> str:
        digest = hashlib.sha256(f"{self.model_name}:{text}".encode()).hexdigest()
        return digest

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.npy"

    def _load_cached(self, key: str) -> np.ndarray | None:
        path = self._cache_path(key)
        if path.exists():
            return np.load(str(path))
        return None

    def _save_cached(self, key: str, embedding: np.ndarray) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        np.save(str(self._cache_path(key)), embedding)

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        """Return (N, dim) float32 array of embeddings."""
        t0 = time.perf_counter()
        texts = list(texts)
        n = len(texts)

        embeddings: list[np.ndarray | None] = [None] * n
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        for i, text in enumerate(texts):
            cached = self._load_cached(self._cache_key(text))
            if cached is not None:
                embeddings[i] = cached
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        cache_hits = n - len(uncached_indices)
        logger.info(
            f"[embedder] {n} texts — {cache_hits} cache hits, "
            f"{len(uncached_indices)} to compute"
        )

        if uncached_texts:
            computed = self.model.encode(
                uncached_texts,
                batch_size=self.batch_size,
                show_progress_bar=len(uncached_texts) > 50,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            for idx, emb in zip(uncached_indices, computed):
                self._save_cached(self._cache_key(texts[idx]), emb)
                embeddings[idx] = emb

        result = np.stack(embeddings)  # type: ignore[arg-type]
        logger.info(
            f"[embedder] Done — shape={result.shape}, "
            f"elapsed={time.perf_counter() - t0:.2f}s"
        )
        return result.astype(np.float32)
