# ABOUTME: Tests for HTTP client — auth headers, error translation, status polling
# ABOUTME: Uses httpx MockTransport to test without hitting real APIs

import json
import time

import httpx
import pytest

from reka.client import RekaClient
from reka.output import ApiError


def make_response(status_code: int, body: dict) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        json=body,
    )


class MockTransport(httpx.BaseTransport):
    def __init__(self, responses: list[httpx.Response]):
        self._responses = list(responses)
        self._index = 0

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        resp = self._responses[self._index]
        self._index += 1
        # Store last request for inspection
        self.last_request = request
        return resp


class TestRekaClient:
    def make_client(self, transport):
        return RekaClient(
            base_url="https://api.example.com",
            token="reka_test",
            timeout=5,
            http_client=httpx.Client(transport=transport),
        )

    def test_sets_api_key_header(self):
        transport = MockTransport([make_response(200, {"results": []})])
        client = self.make_client(transport)
        client.get("/v1/videos")
        assert transport.last_request.headers["x-api-key"] == "reka_test"

    def test_successful_get_returns_parsed_body(self):
        transport = MockTransport([make_response(200, {"video_id": "abc"})])
        client = self.make_client(transport)
        result = client.get("/v1/videos/abc")
        assert result == {"video_id": "abc"}

    def test_404_raises_api_error_with_exit_code_4(self):
        body = {"error": {"type": "not_found_error", "message": "not found"}}
        transport = MockTransport([make_response(404, body)])
        client = self.make_client(transport)
        with pytest.raises(ApiError) as exc_info:
            client.get("/v1/videos/missing")
        assert exc_info.value.exit_code == 4

    def test_401_raises_api_error_with_exit_code_2(self):
        body = {"error": {"type": "authentication_error", "message": "bad key"}}
        transport = MockTransport([make_response(401, body)])
        client = self.make_client(transport)
        with pytest.raises(ApiError) as exc_info:
            client.get("/v1/videos")
        assert exc_info.value.exit_code == 2

    def test_500_raises_api_error_with_exit_code_7(self):
        body = {"error": {"type": "server_error", "message": "boom"}}
        transport = MockTransport([make_response(500, body)])
        client = self.make_client(transport)
        with pytest.raises(ApiError) as exc_info:
            client.get("/v1/videos")
        assert exc_info.value.exit_code == 7

    def test_429_raises_api_error_with_exit_code_6(self):
        body = {"error": {"type": "rate_limit_error", "message": "slow down"}}
        transport = MockTransport([make_response(429, body)])
        client = self.make_client(transport)
        with pytest.raises(ApiError) as exc_info:
            client.get("/v1/videos")
        assert exc_info.value.exit_code == 6

    def test_non_json_error_body_still_raises(self):
        transport = MockTransport([
            httpx.Response(500, text="Internal Server Error")
        ])
        client = self.make_client(transport)
        with pytest.raises(ApiError) as exc_info:
            client.get("/v1/videos")
        assert exc_info.value.exit_code == 7


class TestWaitForStatus:
    def make_client(self, transport):
        return RekaClient(
            base_url="https://api.example.com",
            token="reka_test",
            timeout=5,
            http_client=httpx.Client(transport=transport),
        )

    def test_returns_immediately_when_already_terminal(self):
        transport = MockTransport([
            make_response(200, {"status": "indexed", "video_id": "abc"}),
        ])
        client = self.make_client(transport)
        result = client.wait_for_status(
            poll_fn=lambda: client.get("/v1/videos/abc"),
            status_field="status",
            terminal_states={"indexed", "index_failed"},
            timeout=10,
            interval=0,
        )
        assert result["status"] == "indexed"

    def test_polls_until_terminal_state(self):
        transport = MockTransport([
            make_response(200, {"status": "indexing", "video_id": "abc"}),
            make_response(200, {"status": "indexing", "video_id": "abc"}),
            make_response(200, {"status": "indexed", "video_id": "abc"}),
        ])
        client = self.make_client(transport)
        result = client.wait_for_status(
            poll_fn=lambda: client.get("/v1/videos/abc"),
            status_field="status",
            terminal_states={"indexed", "index_failed"},
            timeout=10,
            interval=0,
        )
        assert result["status"] == "indexed"

    def test_raises_timeout_error_when_exceeded(self):
        # timeout=0 means the deadline is already past after the first poll
        transport = MockTransport([
            make_response(200, {"status": "indexing"}),
        ])
        client = self.make_client(transport)
        with pytest.raises(ApiError) as exc_info:
            client.wait_for_status(
                poll_fn=lambda: client.get("/v1/videos/abc"),
                status_field="status",
                terminal_states={"indexed"},
                timeout=0,
                interval=0,
            )
        assert exc_info.value.exit_code == 8
