# ABOUTME: Tests for the videos command group
# ABOUTME: Covers upload, list, get, and delete using CLI test runner

import json

import httpx
import pytest
from typer.testing import CliRunner

from reka.main import app

runner = CliRunner()

BASE_ARGS = ["--token", "reka_test", "--env", "staging"]


def make_transport(responses: list[httpx.Response]):
    class T(httpx.BaseTransport):
        def __init__(self):
            self._responses = list(responses)
            self._index = 0

        def handle_request(self, request):
            resp = self._responses[self._index]
            self._index += 1
            return resp

    return T()


def json_resp(status_code: int, body: dict) -> httpx.Response:
    return httpx.Response(status_code, json=body)


SAMPLE_VIDEO = {
    "video_id": "abc123",
    "metadata": {"video_name": "clip.mp4"},
    "status": "indexed",
}

SAMPLE_VIDEOS_RESPONSE = {"results": [SAMPLE_VIDEO]}


class TestVideosList:
    def test_outputs_results_as_json(self, monkeypatch):
        def fake_get(self_inner, path, **kwargs):
            return SAMPLE_VIDEOS_RESPONSE

        monkeypatch.setattr("reka.client.RekaClient.get", fake_get)
        result = runner.invoke(app, BASE_ARGS + ["videos", "list"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data == [SAMPLE_VIDEO]

    def test_exits_2_on_auth_error(self, monkeypatch):
        def fake_get(self_inner, path, **kwargs):
            from reka.output import ApiError
            raise ApiError(exit_code=2, error={"type": "authentication_error", "message": "bad key"})

        monkeypatch.setattr("reka.client.RekaClient.get", fake_get)
        result = runner.invoke(app, BASE_ARGS + ["videos", "list"])
        assert result.exit_code == 2


class TestVideosGet:
    def test_returns_single_video(self, monkeypatch):
        def fake_get(self_inner, path, **kwargs):
            return SAMPLE_VIDEO

        monkeypatch.setattr("reka.client.RekaClient.get", fake_get)
        result = runner.invoke(app, BASE_ARGS + ["videos", "get", "abc123"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["video_id"] == "abc123"

    def test_exits_4_on_not_found(self, monkeypatch):
        def fake_get(self_inner, path, **kwargs):
            from reka.output import ApiError
            raise ApiError(exit_code=4, error={"type": "not_found_error", "message": "not found"})

        monkeypatch.setattr("reka.client.RekaClient.get", fake_get)
        result = runner.invoke(app, BASE_ARGS + ["videos", "get", "missing"])
        assert result.exit_code == 4


class TestVideosDelete:
    def test_outputs_delete_response(self, monkeypatch):
        def fake_delete(self_inner, path, **kwargs):
            return {"status": "success", "message": "Videos deleted successfully"}

        monkeypatch.setattr("reka.client.RekaClient.delete", fake_delete)
        result = runner.invoke(app, BASE_ARGS + ["videos", "delete", "abc123"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "success"


class TestVideosUploadUrl:
    def test_upload_via_url_without_wait(self, monkeypatch):
        def fake_post(self_inner, path, **kwargs):
            return {"video_id": "new123", "status": "download_initiated"}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(
            app,
            BASE_ARGS + ["videos", "upload", "--url", "https://example.com/v.mp4", "--name", "test"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["video_id"] == "new123"

    def test_upload_with_wait_polls_until_indexed(self, monkeypatch):
        post_calls = []
        get_calls = []

        def fake_post(self_inner, path, **kwargs):
            post_calls.append(1)
            return {"video_id": "new123", "status": "download_initiated"}

        def fake_get(self_inner, path, **kwargs):
            get_calls.append(1)
            if len(get_calls) < 3:
                return {"video_id": "new123", "status": "indexing"}
            return {"video_id": "new123", "status": "indexed"}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        monkeypatch.setattr("reka.client.RekaClient.get", fake_get)
        result = runner.invoke(
            app,
            BASE_ARGS + ["--wait", "videos", "upload", "--url", "https://example.com/v.mp4", "--name", "test"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "indexed"
        assert len(get_calls) == 3

    def test_upload_no_index_flag_sends_index_false(self, monkeypatch):
        captured = {}

        def fake_post(self_inner, path, data=None, **kwargs):
            captured["data"] = data
            return {"video_id": "abc", "status": "upload_initiated"}

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        runner.invoke(
            app,
            BASE_ARGS + ["videos", "upload", "--url", "https://x.com/v.mp4", "--name", "t", "--no-index"],
        )
        assert captured["data"]["index"] == "false"
