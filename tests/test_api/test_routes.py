"""Integration tests for FastAPI routes."""

from __future__ import annotations

from fastapi.testclient import TestClient

from featrank.api.main import app

client = TestClient(app)


class TestHealth:
    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "model_loaded" in data


class TestIngest:
    def test_ingest_returns_job_id(self):
        payload = {
            "requests": [
                {"id": "1", "text": "dark mode support", "source": "intercom"},
                {"id": "2", "text": "csv export needed", "source": "zendesk"},
            ]
        }
        resp = client.post("/ingest", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert data["request_count"] == 2

    def test_ingest_empty_list(self):
        resp = client.post("/ingest", json={"requests": []})
        assert resp.status_code == 200
        assert resp.json()["request_count"] == 0


class TestCluster:
    def test_cluster_with_inline_requests(self):
        requests = [
            {"id": str(i), "text": f"feature request number {i}", "source": "test"}
            for i in range(10)
        ]
        resp = client.post("/cluster", json={"requests": requests})
        assert resp.status_code == 200
        data = resp.json()
        assert "clusters" in data
        assert "noise_count" in data

    def test_cluster_missing_both_fields_returns_422(self):
        resp = client.post("/cluster", json={})
        assert resp.status_code == 422


class TestRank:
    def _make_cluster(self, cluster_id: int, label: str, count: int):
        req = {
            "id": "1",
            "text": "sample",
            "source": "test",
            "cluster_id": cluster_id,
            "embedding": [0.1] * 10,
            "cleaned_text": "sample",
        }
        return {
            "cluster_id": cluster_id,
            "label": label,
            "requests": [req] * count,
            "request_count": count,
            "unique_users": count,
            "total_mrr": float(count * 100),
            "sample_requests": ["sample"],
        }

    def test_rank_returns_ranked_list(self):
        clusters = [
            self._make_cluster(0, "dark mode", 30),
            self._make_cluster(1, "csv export", 10),
        ]
        resp = client.post("/rank", json={"clusters": clusters})
        assert resp.status_code == 200
        data = resp.json()
        assert "ranked" in data
        assert len(data["ranked"]) == 2
        assert data["ranked"][0]["priority_rank"] == 1
