"""Composite scorer — combines all four signals into a final priority ranking."""

from __future__ import annotations

import time
from typing import Sequence

from loguru import logger

from featrank.config import settings
from featrank.schemas import FeatureCluster, PrioritizedCluster
from featrank.scoring.frequency import FrequencyScorer
from featrank.scoring.github_signal import GitHubSignalScorer
from featrank.scoring.roadmap_fit import RoadmapFitScorer
from featrank.scoring.segment_value import SegmentValueScorer


class CompositeRanker:
    """Combine the four scoring signals into a single priority_score (0-100)."""

    def __init__(
        self,
        weight_frequency: float | None = None,
        weight_segment_value: float | None = None,
        weight_github_signal: float | None = None,
        weight_roadmap_fit: float | None = None,
        github_repo: str | None = None,
        github_token: str | None = None,
    ) -> None:
        self.w_freq = weight_frequency if weight_frequency is not None else settings.weight_frequency
        self.w_seg = weight_segment_value if weight_segment_value is not None else settings.weight_segment_value
        self.w_gh = weight_github_signal if weight_github_signal is not None else settings.weight_github_signal
        self.w_road = weight_roadmap_fit if weight_roadmap_fit is not None else settings.weight_roadmap_fit

        self._freq_scorer = FrequencyScorer()
        self._seg_scorer = SegmentValueScorer()
        self._gh_scorer = GitHubSignalScorer(repo=github_repo, token=github_token)
        self._road_scorer = RoadmapFitScorer()

    def rank(
        self,
        clusters: Sequence[FeatureCluster],
        roadmap_text: str | None = None,
    ) -> list[PrioritizedCluster]:
        t0 = time.perf_counter()
        clusters = list(clusters)

        freq_scores = self._freq_scorer.score(clusters)
        seg_scores = self._seg_scorer.score(clusters)
        gh_scores = self._gh_scorer.score(clusters)
        road_scores = self._road_scorer.score(clusters, roadmap_text)

        prioritized: list[PrioritizedCluster] = []
        for i, cluster in enumerate(clusters):
            composite = (
                self.w_freq * freq_scores[i]
                + self.w_seg * seg_scores[i]
                + self.w_gh * gh_scores[i]
                + self.w_road * road_scores[i]
            ) * 100

            prioritized.append(
                PrioritizedCluster(
                    **cluster.model_dump(),
                    score_frequency=round(freq_scores[i], 4),
                    score_segment_value=round(seg_scores[i], 4),
                    score_github_signal=round(gh_scores[i], 4),
                    score_roadmap_fit=round(road_scores[i], 4),
                    priority_score=round(composite, 2),
                    priority_rank=1,
                )
            )

        prioritized.sort(key=lambda c: c.priority_score, reverse=True)
        for rank, cluster in enumerate(prioritized, start=1):
            cluster.priority_rank = rank

        logger.info(
            f"[ranker] {len(prioritized)} clusters ranked "
            f"— {time.perf_counter() - t0:.2f}s"
        )
        return prioritized
