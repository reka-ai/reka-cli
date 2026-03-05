# ABOUTME: Tests for the streams command group
# ABOUTME: Covers add, delete, get, list (all POST-based endpoints)

import json

import pytest
from typer.testing import CliRunner

from reka.main import app

runner = CliRunner()
BASE_ARGS = ["--token", "reka_test"]

SAMPLE_STREAM = {
    "stream_id": "stream123",
    "stream_url": "rtsp://example.com/feed",
    "status": "active",
}


class TestStreamsAdd:
    def test_sends_stream_url(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, json=None, **kwargs):
            captured["path"] = path
            captured["json"] = json
            return {"stream_id": "stream123"}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(
            app,
            BASE_ARGS + ["streams", "add", "--url", "rtsp://example.com/feed"],
        )
        assert result.exit_code == 0
        assert "/add" in captured["path"]
        assert captured["json"]["stream_url"] == "rtsp://example.com/feed"

    def test_returns_stream_id(self, monkeypatch):
        def fake_post(self_inner, path, **kwargs):
            return {"stream_id": "stream123"}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(
            app,
            BASE_ARGS + ["streams", "add", "--url", "rtsp://example.com/feed"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["stream_id"] == "stream123"


class TestStreamsGet:
    def test_sends_stream_id(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, json=None, **kwargs):
            captured["json"] = json
            return SAMPLE_STREAM

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(app, BASE_ARGS + ["streams", "get", "stream123"])
        assert result.exit_code == 0
        assert captured["json"]["stream_id"] == "stream123"

    def test_returns_stream_data(self, monkeypatch):
        def fake_post(self_inner, path, **kwargs):
            return SAMPLE_STREAM

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(app, BASE_ARGS + ["streams", "get", "stream123"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["stream_id"] == "stream123"


class TestStreamsDelete:
    def test_sends_stream_id(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, json=None, **kwargs):
            captured["json"] = json
            return {"message": "Stream is set for deletion"}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(app, BASE_ARGS + ["streams", "delete", "stream123"])
        assert result.exit_code == 0
        assert captured["json"]["stream_id"] == "stream123"


class TestStreamsList:
    def test_returns_streams_list(self, monkeypatch):
        def fake_post(self_inner, path, json=None, **kwargs):
            return {"streams": [SAMPLE_STREAM]}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(app, BASE_ARGS + ["streams", "list"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data == [SAMPLE_STREAM]

    def test_passes_limit_and_offset(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, json=None, **kwargs):
            captured["json"] = json
            return {"streams": []}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        runner.invoke(
            app,
            BASE_ARGS + ["streams", "list", "--limit", "10", "--offset", "5"],
        )
        assert captured["json"]["limit"] == 10
        assert captured["json"]["offset"] == 5
