# ABOUTME: Tests for the generations command group
# ABOUTME: Covers create and get (no list/delete endpoints exist)

import json

import pytest
from typer.testing import CliRunner

from reka.main import app

runner = CliRunner()
BASE_ARGS = ["--token", "reka_test"]

SAMPLE_GENERATION = {
    "id": "gen123",
    "status": "queued",
    "video_urls": [],
    "prompt": "highlight reel",
    "template": "compilation",
}


class TestGenerationsCreate:
    def test_sends_prompt_and_template(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, json=None, **kwargs):
            captured["path"] = path
            captured["json"] = json
            return SAMPLE_GENERATION

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(
            app,
            BASE_ARGS + [
                "generations", "create",
                "--prompt", "highlight reel",
                "--template", "compilation",
            ],
        )
        assert result.exit_code == 0
        assert captured["json"]["prompt"] == "highlight reel"
        assert captured["json"]["template"] == "compilation"

    def test_sends_video_ids(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, json=None, **kwargs):
            captured["json"] = json
            return SAMPLE_GENERATION

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        runner.invoke(
            app,
            BASE_ARGS + [
                "generations", "create",
                "--video-ids", "v1,v2",
            ],
        )
        assert captured["json"]["video_ids"] == ["v1", "v2"]

    def test_returns_generation_response(self, monkeypatch):
        def fake_post(self_inner, path, **kwargs):
            return SAMPLE_GENERATION

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(
            app,
            BASE_ARGS + ["generations", "create", "--prompt", "test"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["id"] == "gen123"


class TestGenerationsGet:
    def test_returns_generation_by_id(self, monkeypatch):
        def fake_get(self_inner, path, **kwargs):
            return SAMPLE_GENERATION

        monkeypatch.setattr("reka.client.RekaClient.get", fake_get)
        result = runner.invoke(app, BASE_ARGS + ["generations", "get", "gen123"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["id"] == "gen123"
        assert data["status"] == "queued"
