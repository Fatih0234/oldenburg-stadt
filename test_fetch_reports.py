"""Tests for fetch_reports fallback behavior.

Verifies that the API client retries through a proxy when direct
access is blocked (403) or fails, and that it exhausts all options
before giving up.
"""

import pytest
import requests

from fetch_reports import fetch_with_fallback, PROXY_TEMPLATES, API_URL


# ── helpers ──────────────────────────────────────────────────────────

def _ok_response(data=None):
    """Build a minimal successful JSON response."""
    data = data or {"reports": [{"id": 1}], "totalCnt": 1}
    resp = requests.Response()
    resp.status_code = 200
    resp._content = __import__("json").dumps(data).encode()
    return resp


def _status_response(code):
    """Build a response with the given HTTP status code."""
    resp = requests.Response()
    resp.status_code = code
    resp._content = b""
    return resp


# ── tests ────────────────────────────────────────────────────────────

class TestFetchWithFallback:
    """Behavior of the fetch_with_fallback retry logic."""

    def test_direct_success_skips_proxy(self, monkeypatch):
        """When the API responds 200, no proxy is contacted."""
        calls = []

        def mock_get(url, **kwargs):
            calls.append(url)
            return _ok_response()

        monkeypatch.setattr("fetch_reports.requests.get", mock_get)

        result = fetch_with_fallback({"limit": 1, "offset": 0})

        assert result == {"reports": [{"id": 1}], "totalCnt": 1}
        assert len(calls) == 1, "should call exactly once (direct only)"
        assert API_URL in calls[0]

    def test_403_falls_back_to_proxy(self, monkeypatch):
        """Direct 403 triggers proxy fallback, which succeeds."""
        calls = []

        def mock_get(url, **kwargs):
            calls.append(url)
            if API_URL in url:
                return _status_response(403)
            return _ok_response()

        monkeypatch.setattr("fetch_reports.requests.get", mock_get)

        result = fetch_with_fallback({"limit": 1, "offset": 0})

        assert result["totalCnt"] == 1
        assert len(calls) == 2, "should try direct then proxy"
        assert "codetabs" in calls[1]

    def test_network_error_falls_back_to_proxy(self, monkeypatch):
        """A connection error on direct access triggers proxy fallback."""
        calls = []

        def mock_get(url, **kwargs):
            calls.append(url)
            if API_URL in url:
                raise requests.ConnectionError("refused")
            return _ok_response()

        monkeypatch.setattr("fetch_reports.requests.get", mock_get)

        result = fetch_with_fallback({"limit": 1, "offset": 0})

        assert result["totalCnt"] == 1
        assert len(calls) == 2

    def test_timeout_falls_back_to_proxy(self, monkeypatch):
        """A timeout on direct access triggers proxy fallback."""
        calls = []

        def mock_get(url, **kwargs):
            calls.append(url)
            if API_URL in url:
                raise requests.Timeout("timed out")
            return _ok_response()

        monkeypatch.setattr("fetch_reports.requests.get", mock_get)

        result = fetch_with_fallback({"limit": 1, "offset": 0})

        assert result["totalCnt"] == 1
        assert len(calls) == 2

    def test_all_methods_fail_exits(self, monkeypatch):
        """When direct and all proxies fail, the process exits with code 1."""
        def mock_get(url, **kwargs):
            return _status_response(403)

        monkeypatch.setattr("fetch_reports.requests.get", mock_get)

        with pytest.raises(SystemExit) as exc_info:
            fetch_with_fallback({"limit": 1, "offset": 0})

        assert exc_info.value.code == 1

    def test_proxy_network_error_tries_next(self, monkeypatch):
        """If a proxy raises a network error, the next one is tried."""
        proxy_calls = []

        def mock_get(url, **kwargs):
            if API_URL in url:
                return _status_response(403)
            # First proxy raises, second succeeds
            proxy_calls.append(url)
            if len(proxy_calls) == 1:
                raise requests.ConnectionError("proxy down")
            return _ok_response()

        # Use two proxies for this test
        monkeypatch.setattr("fetch_reports.requests.get", mock_get)
        monkeypatch.setattr(
            "fetch_reports.PROXY_TEMPLATES",
            [
                "https://proxy-a.example.com/{url}",
                "https://proxy-b.example.com/{url}",
            ],
        )

        result = fetch_with_fallback({"limit": 1, "offset": 0})

        assert result["totalCnt"] == 1
        assert len(proxy_calls) == 2
        assert "proxy-a" in proxy_calls[0]
        assert "proxy-b" in proxy_calls[1]

    def test_proxy_returns_non_200_skips_to_next(self, monkeypatch):
        """A proxy returning a non-200 status is skipped."""
        proxy_calls = []

        def mock_get(url, **kwargs):
            if API_URL in url:
                return _status_response(403)
            proxy_calls.append(url)
            if len(proxy_calls) == 1:
                return _status_response(500)
            return _ok_response()

        monkeypatch.setattr("fetch_reports.requests.get", mock_get)
        monkeypatch.setattr(
            "fetch_reports.PROXY_TEMPLATES",
            [
                "https://proxy-a.example.com/{url}",
                "https://proxy-b.example.com/{url}",
            ],
        )

        result = fetch_with_fallback({"limit": 1, "offset": 0})

        assert result["totalCnt"] == 1
        assert len(proxy_calls) == 2

    def test_direct_500_falls_back_to_proxy(self, monkeypatch):
        """A 500 on direct access (not just 403) triggers fallback."""
        calls = []

        def mock_get(url, **kwargs):
            calls.append(url)
            if API_URL in url:
                return _status_response(500)
            return _ok_response()

        monkeypatch.setattr("fetch_reports.requests.get", mock_get)

        result = fetch_with_fallback({"limit": 1, "offset": 0})

        assert result["totalCnt"] == 1
        assert len(calls) == 2
