"""Roadmap alignment scorer via cosine similarity."""

from __future__ import annotations

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer
from typing import Sequence

from featrank.config import settings
from featrank.schemas import FeatureCluster


class RoadmapFitScorer:
    """Score clusters by cosine similarity to the stated product roadmap.

    1. Embed each roadmap item
    2. Compute cluster centroid embeddings
    3. score = max(cosine_sim(cluster_centroid, roadmap_item))
    4. Normalize 0-1 across all clusters

    Returns zeros if no roadmap text is provided.
    """

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embedding_model
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _parse_roadmap(self, roadmap_text: str) -> list[str]:
        lines = [line.strip().lstrip("-*•").strip() for line in roadmap_text.splitlines()]
        return [line for line in lines if len(line) > 3]

    def score(
        self,
        clusters: Sequence[FeatureCluster],
        roadmap_text: str | None = None,
    ) -> list[float]:
        if not roadmap_text or not roadmap_text.strip():
            logger.info("[roadmap_fit] No roadmap text provided — returning zeros")
            return [0.0] * len(clusters)

        roadmap_items = self._parse_roadmap(roadmap_text)
        if not roadmap_items:
            return [0.0] * len(clusters)

        roadmap_embs = self.model.encode(
            roadmap_items, normalize_embeddings=True, convert_to_numpy=True
        )

        raw_scores: list[float] = []
        for cluster in clusters:
            embeddings = np.array([r.embedding for r in cluster.requests], dtype=np.float32)
            if embeddings.size == 0:
                raw_scores.append(0.0)
                continue
            centroid = embeddings.mean(axis=0)
            norm = np.linalg.norm(centroid)
            if norm > 0:
                centroid = centroid / norm
            sims = roadmap_embs @ centroid
            raw_scores.append(float(sims.max()))

        min_val, max_val = min(raw_scores), max(raw_scores)
        if max_val == min_val:
            return [0.0] * len(clusters)
        return [(s - min_val) / (max_val - min_val) for s in raw_scores]
