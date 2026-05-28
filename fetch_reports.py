import requests
import json
import time
import sys
from urllib.parse import quote, urlencode
import pandas as pd

# API Endpoint URL
API_URL = "https://gemeinsam.oldenburg.de/backend/v1/flaw-reporter/findPageableReportsWithFilter"

# Fallback proxies for environments where direct API access is blocked (e.g., GitHub Actions)
# {url} is replaced with the fully URL-encoded API URL including query params.
PROXY_TEMPLATES = [
    "https://api.codetabs.com/v1/proxy?quest={url}",
]

REQUEST_TIMEOUT = 30


def _build_url_with_params(base_url, params):
    """Build a full URL with query parameters, URL-encoded for proxy use."""
    return quote(f"{base_url}?{urlencode(params)}")


def fetch_with_fallback(params):
    """Try direct API access first, fall back to proxies on 403."""
    headers = {
        "User-Agent": "OldenburgRadDashboardDataPipeline/1.0 (contact: fatih.karahan@example.com)"
    }

    # Attempt 1: Direct access
    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        if response.status_code != 403:
            response.raise_for_status()
            return response.json()
        print("⚠️  Direct API access returned 403, trying proxies...")
    except requests.RequestException:
        print("⚠️  Direct API access failed, trying proxies...")

    # Attempt 2+: Try each proxy
    full_url = _build_url_with_params(API_URL, params)
    for proxy_template in PROXY_TEMPLATES:
        proxy_url = proxy_template.format(url=full_url)
        try:
            response = requests.get(proxy_url, headers=headers, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            continue

    print("❌ All access methods failed.", file=sys.stderr)
    sys.exit(1)


def fetch_all_reports():
    print("Starting data fetch from Stadtverbesserer API...")
    
    offset = 0
    limit = 100
    all_reports = []
    
    # Run paginated loop
    while True:
        params = {
            "flawReporterId": 24,
            "limit": limit,
            "offset": offset,
            "sortParam": "id",
            "ascending": "true"
        }
        
        print(f"Fetching reports with offset={offset} (limit={limit})...")
        data = fetch_with_fallback(params)
            
        reports = data.get("reports", [])
        total_cnt = data.get("totalCnt", 0)
        
        if not reports:
            print("No more reports returned by API.")
            break
            
        all_reports.extend(reports)
        print(f"  Retrieved {len(reports)} reports (total collected so far: {len(all_reports)} / {total_cnt})")
        
        # Check if we have collected all reports
        if len(all_reports) >= total_cnt or len(reports) < limit:
            print(f"Collected all available reports ({len(all_reports)} total).")
            break
            
        offset += limit
        # Throttle request to be polite to the API
        time.sleep(0.5)
        
    return all_reports

def map_report_fields(raw_report):
    # Extract nested picture URL (if present)
    pictures = raw_report.get("pictures") or []
    first_picture_url = ""
    if pictures and len(pictures) > 0:
        first_picture_url = pictures[0].get("fileCDNUrl") or ""
        
    category = raw_report.get("category") or {}
    coordinate = raw_report.get("coordinate") or {}
    
    # Map to schema of stadtverbesserer_snapshot
    return {
        "id": raw_report.get("id"),
        "createdAt": raw_report.get("createdAt"),
        "state": raw_report.get("state"),
        "categoryId": category.get("id"),
        "categoryName": category.get("categoryName"),
        "latitude": coordinate.get("latitude"),
        "longitude": coordinate.get("longitude"),
        "replacingText": raw_report.get("replacingText") or "",
        "firstPictureUrl": first_picture_url
    }

def main():
    raw_reports = fetch_all_reports()
    if not raw_reports:
        print("❌ Warning: No reports fetched.")
        return
        
    # Process and map fields
    mapped_reports = [map_report_fields(r) for r in raw_reports]
    
    # Save as JSON snapshot
    json_path = "stadtverbesserer_snapshot.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(mapped_reports, f, indent=2, ensure_ascii=False)
    print(f"Saved snapshot to {json_path}")
    
    # Save as CSV snapshot, maintaining strict column ordering
    columns = [
        "id", "createdAt", "state", "categoryId", 
        "categoryName", "latitude", "longitude", 
        "replacingText", "firstPictureUrl"
    ]
    df = pd.DataFrame(mapped_reports)
    # Ensure correct columns order
    df = df.reindex(columns=columns)
    
    csv_path = "stadtverbesserer_snapshot.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved snapshot to {csv_path}")
    print("Data fetching completed successfully.")

if __name__ == "__main__":
    main()
