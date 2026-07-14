"""Tests for featrank.pipeline.embedder."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from featrank.pipeline.embedder import Embedder


@pytest.fixture
def embedder(tmp_path: Path) -> Embedder:
    return Embedder(model_name="all-MiniLM-L6-v2", cache_dir=str(tmp_path / "cache"))


class TestEmbedder:
    def test_returns_numpy_array(self, embedder: Embedder):
        result = embedder.embed(["dark mode support", "csv export"])
        assert isinstance(result, np.ndarray)

    def test_shape_matches_input(self, embedder: Embedder):
        texts = ["dark mode", "csv export", "bulk actions"]
        result = embedder.embed(texts)
        assert result.shape[0] == 3

    def test_embeddings_are_normalized(self, embedder: Embedder):
        result = embedder.embed(["dark mode support"])
        norms = np.linalg.norm(result, axis=1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-5)

    def test_cache_is_used_on_second_call(self, embedder: Embedder):
        texts = ["dark mode support"]
        first = embedder.embed(texts)
        second = embedder.embed(texts)
        np.testing.assert_array_equal(first, second)

    def test_empty_list_raises(self, embedder: Embedder):
        with pytest.raises(Exception):
            embedder.embed([])
