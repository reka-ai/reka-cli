# ABOUTME: HTTP client for the Reka Vision Agent API
# ABOUTME: Handles auth, error translation to ApiError, and async status polling

import time
from typing import Any, Callable, Optional, Set

import httpx

from reka.output import ApiError


class RekaClient:
    """Thin wrapper around httpx.Client with Reka auth and error handling."""

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: int = 30,
        verbose: bool = False,
        http_client: Optional[httpx.Client] = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout
        self._verbose = verbose
        self._http = http_client or httpx.Client(
            timeout=httpx.Timeout(timeout),
        )

    def _headers(self) -> dict:
        return {"X-Api-Key": self._token}

    def _handle_response(self, response: httpx.Response) -> Any:
        if self._verbose:
            import sys
            print(f"→ {response.request.method} {response.request.url}", file=sys.stderr)
            print(f"← {response.status_code}", file=sys.stderr)
        if response.is_success:
            return response.json()
        try:
            body = response.json()
        except Exception:
            body = {"error": {"type": "server_error", "message": response.text or "Unknown error"}}
        raise ApiError.from_response(body)

    def get(self, path: str, **kwargs) -> Any:
        try:
            resp = self._http.get(
                self._base_url + path,
                headers=self._headers(),
                **kwargs,
            )
        except httpx.TimeoutException:
            raise ApiError.timeout()
        except httpx.ConnectError as e:
            raise ApiError.connection(str(e))
        return self._handle_response(resp)

    def post(self, path: str, **kwargs) -> Any:
        try:
            resp = self._http.post(
                self._base_url + path,
                headers=self._headers(),
                **kwargs,
            )
        except httpx.TimeoutException:
            raise ApiError.timeout()
        except httpx.ConnectError as e:
            raise ApiError.connection(str(e))
        return self._handle_response(resp)

    def delete(self, path: str, **kwargs) -> Any:
        try:
            resp = self._http.delete(
                self._base_url + path,
                headers=self._headers(),
                **kwargs,
            )
        except httpx.TimeoutException:
            raise ApiError.timeout()
        except httpx.ConnectError as e:
            raise ApiError.connection(str(e))
        return self._handle_response(resp)

    def wait_for_status(
        self,
        poll_fn: Callable[[], Any],
        status_field: str,
        terminal_states: Set[str],
        timeout: float = 300,
        interval: float = 2,
    ) -> Any:
        """Poll poll_fn until status_field is in terminal_states or timeout is exceeded."""
        deadline = time.monotonic() + timeout
        while True:
            result = poll_fn()
            status = result.get(status_field)
            if status in terminal_states:
                return result
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ApiError.timeout()
            if interval > 0:
                time.sleep(min(interval, remaining))
