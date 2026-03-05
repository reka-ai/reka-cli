# ABOUTME: Tests for the clip command group
# ABOUTME: Covers create, list, get, and delete for /v1/clips

import json

import pytest
from typer.testing import CliRunner

from reka.main import app

runner = CliRunner()
BASE_ARGS = ["--token", "reka_test"]

SAMPLE_HIGHLIGHT = {
    "id": "clip123",
    "status": "queued",
    "video_urls": ["https://example.com/video.mp4"],
    "prompt": "Best moments",
    "output": [],
}

SAMPLE_HIGHLIGHT_COMPLETED = {
    "id": "clip123",
    "status": "completed",
    "video_urls": ["https://example.com/video.mp4"],
    "prompt": "Best moments",
    "output": [
        {
            "title": "Top Moments",
            "video_url": "https://cdn.example.com/clip.mp4",
            "caption": "The best bits",
            "hashtags": ["clip"],
            "ai_score": 85,
        }
    ],
}

SAMPLE_HIGHLIGHTS_LIST = {"items": [SAMPLE_HIGHLIGHT]}


class TestClipCreate:
    def test_sends_video_urls(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, json=None, **kwargs):
            captured["path"] = path
            captured["json"] = json
            return SAMPLE_HIGHLIGHT

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(
            app,
            BASE_ARGS + ["clip", "create", "--video-urls", "https://example.com/video.mp4"],
        )
        assert result.exit_code == 0
        assert captured["path"] == "/v1/clips"
        assert captured["json"]["video_urls"] == ["https://example.com/video.mp4"]

    def test_sends_multiple_video_urls(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, json=None, **kwargs):
            captured["json"] = json
            return SAMPLE_HIGHLIGHT

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        runner.invoke(
            app,
            BASE_ARGS + [
                "clip", "create",
                "--video-urls", "https://example.com/a.mp4,https://example.com/b.mp4",
            ],
        )
        assert captured["json"]["video_urls"] == [
            "https://example.com/a.mp4",
            "https://example.com/b.mp4",
        ]

    def test_sends_optional_prompt(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, json=None, **kwargs):
            captured["json"] = json
            return SAMPLE_HIGHLIGHT

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        runner.invoke(
            app,
            BASE_ARGS + [
                "clip", "create",
                "--video-urls", "https://example.com/video.mp4",
                "--prompt", "Best moments",
            ],
        )
        assert captured["json"]["prompt"] == "Best moments"

    def test_returns_highlight_response(self, monkeypatch):
        def fake_post(self_inner, path, json=None, **kwargs):
            return SAMPLE_HIGHLIGHT

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(
            app,
            BASE_ARGS + ["clip", "create", "--video-urls", "https://example.com/video.mp4"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["id"] == "clip123"
        assert data["status"] == "queued"

    def test_wait_polls_until_completed(self, monkeypatch):
        call_count = {"n": 0}

        def fake_post(self_inner, path, json=None, **kwargs):
            return SAMPLE_HIGHLIGHT

        def fake_get(self_inner, path, **kwargs):
            call_count["n"] += 1
            if call_count["n"] < 2:
                return {**SAMPLE_HIGHLIGHT, "status": "processing"}
            return SAMPLE_HIGHLIGHT_COMPLETED

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        monkeypatch.setattr("reka.client.RekaClient.get", fake_get)
        monkeypatch.setattr("time.sleep", lambda _: None)

        result = runner.invoke(
            app,
            BASE_ARGS + [
                "--wait",
                "clip", "create",
                "--video-urls", "https://example.com/video.mp4",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "completed"


class TestClipList:
    def test_returns_items_list(self, monkeypatch):
        def fake_get(self_inner, path, **kwargs):
            return SAMPLE_HIGHLIGHTS_LIST

        monkeypatch.setattr("reka.client.RekaClient.get", fake_get)
        result = runner.invoke(app, BASE_ARGS + ["clip", "list"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data == [SAMPLE_HIGHLIGHT]


class TestClipGet:
    def test_returns_highlight_by_id(self, monkeypatch):
        def fake_get(self_inner, path, **kwargs):
            return SAMPLE_HIGHLIGHT_COMPLETED

        monkeypatch.setattr("reka.client.RekaClient.get", fake_get)
        result = runner.invoke(app, BASE_ARGS + ["clip", "get", "clip123"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["id"] == "clip123"
        assert data["status"] == "completed"


class TestClipDelete:
    def test_outputs_success(self, monkeypatch):
        captured = {}

        def fake_delete(self_inner, path, **kwargs):
            captured["path"] = path
            return {"success": True}

        monkeypatch.setattr("reka.client.RekaClient.delete", fake_delete)
        result = runner.invoke(app, BASE_ARGS + ["clip", "delete", "clip123"])
        assert result.exit_code == 0
        assert captured["path"] == "/v1/clips/clip123"
        data = json.loads(result.stdout)
        assert data["success"] is True
