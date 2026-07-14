"""Tests for featrank.pipeline.cleaner."""

from __future__ import annotations


from featrank.pipeline.cleaner import TextCleaner
from featrank.schemas import RawRequest


def make_req(text: str, id: str = "1") -> RawRequest:
    return RawRequest(id=id, text=text, source="test")


class TestTextCleaner:
    def setup_method(self):
        self.cleaner = TextCleaner(min_length=5)

    def test_lowercases_text(self):
        assert self.cleaner.clean("DARK MODE PLEASE") == "dark mode please"

    def test_strips_html_tags(self):
        assert self.cleaner.clean("<p>dark mode</p>") == "dark mode"

    def test_strips_urls(self):
        result = self.cleaner.clean("See https://example.com for details")
        assert "https" not in result
        assert "example.com" not in result

    def test_collapses_whitespace(self):
        result = self.cleaner.clean("dark   mode   please")
        assert "  " not in result

    def test_strips_leading_trailing_whitespace(self):
        assert self.cleaner.clean("  dark mode  ") == "dark mode"

    def test_clean_requests_drops_too_short(self):
        requests = [
            make_req("ok", "1"),
            make_req("dark mode support", "2"),
        ]
        kept, texts = self.cleaner.clean_requests(requests)
        assert len(kept) == 1
        assert kept[0].id == "2"

    def test_clean_requests_returns_same_length(self, raw_requests):
        kept, texts = self.cleaner.clean_requests(raw_requests)
        assert len(kept) == len(texts)

    def test_clean_requests_all_pass(self, raw_requests):
        kept, texts = self.cleaner.clean_requests(raw_requests)
        assert len(kept) == len(raw_requests)
