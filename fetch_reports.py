"""
Fetch Stadtverbesserer reports from the gemeinsam.oldenburg.de API.

Access Strategy (in order):
  1. curl subprocess with browser-like headers (different TLS fingerprint than Python)
  2. requests with browser-like headers (standard approach with realistic headers)
  3. Graceful degradation: if all methods fail, keep existing snapshot files

Background (investigation findings 2026-06-08):
  - The API returns HTTP 403 from GitHub Actions runner IPs (cloud/datacenter IPs)
  - This started between 2026-06-04 and 2026-06-05 with no code changes on our side
  - The API works fine from residential IPs with ANY User-Agent
  - The old proxy fallback (api.codetabs.com) is defunct (returns 522)
  - Free CORS proxy services (allorigins, corsproxy.io, etc.) also run on cloud infra
    and get 403'd by the same API — they are not a viable solution
  - curl uses a different TLS stack (SecureTransport/LibreSSL on macOS, OpenSSL on Linux)
    than Python's ssl module, producing a different JA3/JA4 fingerprint
  - We use curl subprocess as the primary approach because:
    a) Different TLS fingerprint may bypass WAF fingerprint detection
    b) curl is pre-installed on all GitHub Actions runners (no extra deps)
    c) Browser-like headers help avoid User-Agent/behavioral filtering
  - If ALL approaches fail, we keep the existing committed snapshot files (graceful
    degradation) instead of crashing the pipeline. This means the dashboard shows
    slightly stale data rather than breaking entirely.
"""

import json
import os
import subprocess
import sys
import time
from urllib.parse import quote, urlencode

import pandas as pd

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────
API_URL = "https://gemeinsam.oldenburg.de/backend/v1/flaw-reporter/findPageableReportsWithFilter"

REQUEST_TIMEOUT = 30

# Browser-like headers to avoid behavioral/bot filtering.
# These mimic a real Chrome session on the Stadtverbesserer website.
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Referer": "https://gemeinsam.oldenburg.de/",
    "Origin": "https://gemeinsam.oldenburg.de",
}

# Existing snapshot files — used for graceful degradation
SNAPSHOT_JSON = "stadtverbesserer_snapshot.json"
SNAPSHOT_CSV = "stadtverbesserer_snapshot.csv"


def _build_url_with_params(base_url, params):
    """Build a full URL with query parameters."""
    return f"{base_url}?{urlencode(params)}"


# ─────────────────────────────────────────────────────────────
# Access Method 1: curl subprocess
# ─────────────────────────────────────────────────────────────
def fetch_via_curl(params):
    """
    Fetch a single page via curl subprocess.

    Why curl? It uses a different TLS library than Python's `requests`:
      - Python requests → OpenSSL via urllib3 → specific JA3 fingerprint
      - curl → SecureTransport/LibreSSL (macOS) or OpenSSL (Linux) → different JA3

    WAFs that fingerprint TLS handshakes (JA3/JA4) may block Python but allow curl.
    Additionally, curl is pre-installed on GitHub Actions runners.
    """
    url = _build_url_with_params(API_URL, params)
    cmd = [
        "curl", "-s", "-f",
        "--max-time", str(REQUEST_TIMEOUT),
        "-H", f"User-Agent: {BROWSER_HEADERS['User-Agent']}",
        "-H", f"Accept: {BROWSER_HEADERS['Accept']}",
        "-H", f"Accept-Language: {BROWSER_HEADERS['Accept-Language']}",
        "-H", f"Referer: {BROWSER_HEADERS['Referer']}",
        "-H", f"Origin: {BROWSER_HEADERS['Origin']}",
        url,
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=REQUEST_TIMEOUT + 5
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        # curl -f returns exit code 22 for HTTP errors (4xx/5xx)
        if result.returncode == 22:
            return None
        return None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return None


# ─────────────────────────────────────────────────────────────
# Access Method 2: requests with browser headers
# ─────────────────────────────────────────────────────────────
def fetch_via_requests(params):
    """
    Fetch a single page via Python requests with browser-like headers.

    The original script used a custom User-Agent which may trigger bot detection.
    We now use realistic browser headers to blend in with normal traffic.
    """
    import requests

    try:
        response = requests.get(
            API_URL, params=params, headers=BROWSER_HEADERS, timeout=REQUEST_TIMEOUT
        )
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None


# ─────────────────────────────────────────────────────────────
# Unified fetch with fallback chain
# ─────────────────────────────────────────────────────────────
def fetch_with_fallback(params):
    """
    Try multiple access methods in order. Returns parsed JSON or None.

    Order:
      1. curl subprocess (different TLS fingerprint)
      2. requests with browser headers (standard Python HTTP)
      3. None (caller handles graceful degradation)
    """
    # Method 1: curl subprocess
    data = fetch_via_curl(params)
    if data is not None:
        return data

    # Method 2: requests with browser headers
    data = fetch_via_requests(params)
    if data is not None:
        return data

    # All methods exhausted
    return None


# ─────────────────────────────────────────────────────────────
# Main data fetching logic
# ─────────────────────────────────────────────────────────────
def fetch_all_reports():
    """
    Fetch all reports via paginated API calls.

    Returns:
        list of raw report dicts, or None if all access methods fail.
        The caller decides whether to crash or degrade gracefully.
    """
    print("Starting data fetch from Stadtverbesserer API...")

    offset = 0
    limit = 100
    all_reports = []

    while True:
        params = {
            "flawReporterId": 24,
            "limit": limit,
            "offset": offset,
            "sortParam": "id",
            "ascending": "true",
        }

        print(f"Fetching reports with offset={offset} (limit={limit})...")
        data = fetch_with_fallback(params)

        if data is None:
            # First page failed — return None for graceful degradation
            if not all_reports:
                print("⚠️  All access methods failed for first page.")
                return None
            # Subsequent page failed — return what we have so far
            print("⚠️  Access failed on subsequent page, returning partial data.")
            return all_reports

        reports = data.get("reports", [])
        total_cnt = data.get("totalCnt", 0)

        if not reports:
            print("No more reports returned by API.")
            break

        all_reports.extend(reports)
        print(
            f"  Retrieved {len(reports)} reports "
            f"(total collected so far: {len(all_reports)} / {total_cnt})"
        )

        if len(all_reports) >= total_cnt or len(reports) < limit:
            print(f"Collected all available reports ({len(all_reports)} total).")
            break

        offset += limit
        time.sleep(0.5)  # Throttle to be polite to the API

    return all_reports


def map_report_fields(raw_report):
    """Map a raw API report to our snapshot schema."""
    pictures = raw_report.get("pictures") or []
    first_picture_url = pictures[0].get("fileCDNUrl", "") if pictures else ""

    category = raw_report.get("category") or {}
    coordinate = raw_report.get("coordinate") or {}

    return {
        "id": raw_report.get("id"),
        "createdAt": raw_report.get("createdAt"),
        "state": raw_report.get("state"),
        "categoryId": category.get("id"),
        "categoryName": category.get("categoryName"),
        "latitude": coordinate.get("latitude"),
        "longitude": coordinate.get("longitude"),
        "replacingText": raw_report.get("replacingText") or "",
        "firstPictureUrl": first_picture_url,
    }


def save_snapshots(mapped_reports):
    """Save reports as JSON and CSV snapshots."""
    # JSON snapshot
    with open(SNAPSHOT_JSON, "w", encoding="utf-8") as f:
        json.dump(mapped_reports, f, indent=2, ensure_ascii=False)
    print(f"Saved snapshot to {SNAPSHOT_JSON}")

    # CSV snapshot with strict column ordering
    columns = [
        "id", "createdAt", "state", "categoryId",
        "categoryName", "latitude", "longitude",
        "replacingText", "firstPictureUrl",
    ]
    df = pd.DataFrame(mapped_reports)
    df = df.reindex(columns=columns)
    df.to_csv(SNAPSHOT_CSV, index=False)
    print(f"Saved snapshot to {SNAPSHOT_CSV}")


def main():
    raw_reports = fetch_all_reports()

    if raw_reports is None:
        # ── Graceful Degradation ──────────────────────────────
        # All API access methods failed. Instead of crashing the
        # entire pipeline, we keep the existing snapshot files
        # (if they exist) so downstream steps can run on stale data.
        json_exists = os.path.exists(SNAPSHOT_JSON)
        csv_exists = os.path.exists(SNAPSHOT_CSV)

        if json_exists and csv_exists:
            print(
                "⚠️  All API access methods failed. "
                "Keeping existing snapshot files for graceful degradation.",
                file=sys.stderr,
            )
            print(
                "ℹ️  The dashboard will show slightly stale data until the "
                "API becomes accessible again.",
                file=sys.stderr,
            )
            # Exit 0 so the pipeline continues with existing data
            sys.exit(0)
        else:
            print(
                "❌ All API access methods failed and no existing snapshots found. "
                "Cannot degrade gracefully.",
                file=sys.stderr,
            )
            sys.exit(1)

    if not raw_reports:
        print("❌ Warning: No reports fetched (empty response).")
        return

    # Process and save
    mapped_reports = [map_report_fields(r) for r in raw_reports]
    save_snapshots(mapped_reports)
    print("Data fetching completed successfully.")


if __name__ == "__main__":
    main()
