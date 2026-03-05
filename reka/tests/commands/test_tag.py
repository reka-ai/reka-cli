# ABOUTME: Tests for the tag command
# ABOUTME: Covers tagging an indexed video and verifying the structured response

import json

import pytest
from typer.testing import CliRunner

from reka.main import app

runner = CliRunner()
BASE_ARGS = ["--token", "reka_test"]

SAMPLE_TAG_RESULT = {
    "Description": "A barbershop scene with customers getting haircuts.",
    "Violence": False,
    "Profanity": False,
    "AdultContent": False,
    "Drugs": False,
    "Alcohol": False,
    "Gambling": False,
    "Political": False,
    "ExpectedCTR": 0.42,
    "ViralityScore": 0.65,
    "Keyword": ["barbershop", "haircut", "grooming"],
    "MoodTone": ["casual", "friendly"],
}


class TestTag:
    def test_sends_video_id(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, json=None, **kwargs):
            captured["path"] = path
            captured["json"] = json
            return SAMPLE_TAG_RESULT

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(app, BASE_ARGS + ["tag", "--video-id", "vid123"])
        assert result.exit_code == 0
        assert captured["path"] == "/v1/qa/indexedtag"
        assert captured["json"] == {"video_id": "vid123"}

    def test_returns_tagging_result(self, monkeypatch):
        def fake_post(self_inner, path, json=None, **kwargs):
            return SAMPLE_TAG_RESULT

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(app, BASE_ARGS + ["tag", "--video-id", "vid123"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["Description"] == "A barbershop scene with customers getting haircuts."
        assert data["Keyword"] == ["barbershop", "haircut", "grooming"]
