# ABOUTME: Tests for the search command group
# ABOUTME: Covers embedding search and hybrid search

import json

import pytest
from typer.testing import CliRunner

from reka.main import app

runner = CliRunner()
BASE_ARGS = ["--token", "reka_test"]

SAMPLE_SEARCH_RESPONSE = {
    "results": [
        {
            "video_id": "abc123",
            "video_chunk_id": "chunk1",
            "score": 0.95,
            "start_timestamp": 10.0,
            "end_timestamp": 15.0,
            "user_id": "user1",
        }
    ]
}


class TestSearch:
    def test_embedding_search_returns_results(self, monkeypatch):
        def fake_post(self_inner, path, **kwargs):
            return SAMPLE_SEARCH_RESPONSE

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(app, BASE_ARGS + ["search", "--query", "person at desk"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["results"][0]["video_id"] == "abc123"

    def test_passes_video_ids_to_request(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, json=None, **kwargs):
            captured["json"] = json
            return {"results": []}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        runner.invoke(
            app,
            BASE_ARGS + ["search", "--query", "test", "--video-ids", "abc,def"],
        )
        assert captured["json"]["video_ids"] == ["abc", "def"]

    def test_passes_max_results_to_request(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, json=None, **kwargs):
            captured["json"] = json
            return {"results": []}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        runner.invoke(app, BASE_ARGS + ["search", "--query", "test", "--max-results", "5"])
        assert captured["json"]["max_results"] == 5

    def test_report_flag_sets_generate_report(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, json=None, **kwargs):
            captured["json"] = json
            return {"results": []}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        runner.invoke(app, BASE_ARGS + ["search", "--query", "test", "--report"])
        assert captured["json"]["generate_report"] is True

    def test_exits_1_without_query(self):
        result = runner.invoke(app, BASE_ARGS + ["search"])
        assert result.exit_code != 0


class TestSearchHybrid:
    def test_hybrid_search_hits_correct_endpoint(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, **kwargs):
            captured["path"] = path
            return {"results": []}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        runner.invoke(app, BASE_ARGS + ["search", "hybrid", "--query", "test"])
        assert "/hybrid" in captured["path"]
