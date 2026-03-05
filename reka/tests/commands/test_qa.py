# ABOUTME: Tests for the qa command
# ABOUTME: Verifies question routing and message format construction

import json

import pytest
from typer.testing import CliRunner

from reka.main import app

runner = CliRunner()
BASE_ARGS = ["--token", "reka_test"]


class TestQA:
    def test_sends_correct_message_format(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, json=None, **kwargs):
            captured["json"] = json
            return {"chat_response": "A person is walking.", "status": "success"}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(
            app,
            BASE_ARGS + ["qa", "--video-id", "abc123", "--question", "What happens?"],
        )
        assert result.exit_code == 0
        assert captured["json"]["video_id"] == "abc123"
        assert captured["json"]["messages"] == [{"role": "user", "content": "What happens?"}]

    def test_returns_response_as_json(self, monkeypatch):
        def fake_post(self_inner, path, json=None, **kwargs):
            return {"chat_response": "A car drives by.", "status": "success"}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(
            app,
            BASE_ARGS + ["qa", "--video-id", "abc123", "--question", "Describe the video"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["chat_response"] == "A car drives by."

    def test_exits_1_without_required_args(self):
        result = runner.invoke(app, BASE_ARGS + ["qa", "--video-id", "abc123"])
        assert result.exit_code != 0

    def test_hits_qa_chat_endpoint(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, **kwargs):
            captured["path"] = path
            return {"chat_response": "ok", "status": "success"}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        runner.invoke(
            app,
            BASE_ARGS + ["qa", "--video-id", "abc", "--question", "What?"],
        )
        assert "/qa/chat" in captured["path"]
