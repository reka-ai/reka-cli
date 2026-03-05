# ABOUTME: Tests for the images command group
# ABOUTME: Covers upload (files and URLs), list, get, delete, search

import json

import pytest
from typer.testing import CliRunner

from reka.main import app

runner = CliRunner()
BASE_ARGS = ["--token", "reka_test"]

SAMPLE_IMAGE = {
    "image_id": "img123",
    "image_url": "https://s3.example.com/img123.jpg",
    "indexing_status": 1,
    "upload_timestamp": 1700000000.0,
}
SAMPLE_IMAGES_RESPONSE = {"results": [SAMPLE_IMAGE]}


class TestImagesList:
    def test_returns_results_list(self, monkeypatch):
        def fake_get(self_inner, path, **kwargs):
            return SAMPLE_IMAGES_RESPONSE

        monkeypatch.setattr("reka.client.RekaClient.get", fake_get)
        result = runner.invoke(app, BASE_ARGS + ["images", "list"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data == [SAMPLE_IMAGE]

    def test_passes_limit_and_offset(self, monkeypatch):
        captured = {}

        def fake_get(self_inner, path, params=None, **kwargs):
            captured["params"] = params
            return {"results": []}

        monkeypatch.setattr("reka.client.RekaClient.get", fake_get)
        runner.invoke(app, BASE_ARGS + ["images", "list", "--limit", "5", "--offset", "10"])
        assert captured["params"]["limit"] == 5
        assert captured["params"]["offset"] == 10


class TestImagesGet:
    def test_returns_single_image(self, monkeypatch):
        def fake_get(self_inner, path, **kwargs):
            return SAMPLE_IMAGE

        monkeypatch.setattr("reka.client.RekaClient.get", fake_get)
        result = runner.invoke(app, BASE_ARGS + ["images", "get", "img123"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["image_id"] == "img123"


class TestImagesDelete:
    def test_deletes_image_and_returns_response(self, monkeypatch):
        def fake_delete(self_inner, path, **kwargs):
            return {"status": "success", "message": "Images deleted successfully"}

        monkeypatch.setattr("reka.client.RekaClient.delete", fake_delete)
        result = runner.invoke(app, BASE_ARGS + ["images", "delete", "img123"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "success"


class TestImagesUploadUrls:
    def test_uploads_urls_with_correct_metadata_structure(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, data=None, files=None, **kwargs):
            captured["data"] = data
            captured["files"] = files
            return {"results": [SAMPLE_IMAGE]}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(
            app,
            BASE_ARGS + ["images", "upload", "--urls", "https://example.com/a.jpg,https://example.com/b.jpg"],
        )
        assert result.exit_code == 0
        # metadata field should be a JSON string
        metadata = json.loads(captured["data"]["metadata"])
        assert len(metadata["requests"]) == 2
        assert metadata["image_urls"] == [
            "https://example.com/a.jpg",
            "https://example.com/b.jpg",
        ]
        # URL uploads have no files
        assert not captured["files"]

    def test_returns_upload_results(self, monkeypatch):
        def fake_post(self_inner, path, **kwargs):
            return {"results": [SAMPLE_IMAGE]}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(
            app,
            BASE_ARGS + ["images", "upload", "--urls", "https://example.com/a.jpg"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["results"][0]["image_id"] == "img123"

    def test_exits_1_without_files_or_urls(self):
        result = runner.invoke(app, BASE_ARGS + ["images", "upload"])
        assert result.exit_code != 0


class TestImagesSearch:
    def test_sends_query_to_search_endpoint(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, json=None, **kwargs):
            captured["path"] = path
            captured["json"] = json
            return {"results": []}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(
            app,
            BASE_ARGS + ["images", "search", "--query", "red car"],
        )
        assert result.exit_code == 0
        assert "/search" in captured["path"]
        assert captured["json"]["query"] == "red car"

    def test_passes_max_results(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, json=None, **kwargs):
            captured["json"] = json
            return {"results": []}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        runner.invoke(
            app,
            BASE_ARGS + ["images", "search", "--query", "car", "--max-results", "5"],
        )
        assert captured["json"]["max_results"] == 5
