import requests
import json
import time
import sys
import pandas as pd

# API Endpoint URL
API_URL = "https://gemeinsam.oldenburg.de/backend/v1/flaw-reporter/findPageableReportsWithFilter"

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
        try:
            # Add reasonable timeout and headers
            headers = {
                "User-Agent": "OldenburgRadDashboardDataPipeline/1.0 (contact: fatih.karahan@example.com)"
            }
            response = requests.get(API_URL, params=params, headers=headers, timeout=30)
            if response.status_code == 403:
                print("⚠️ Direct API access returned 403 (Forbidden). Trying fallback via CodeTabs proxy...")
                import urllib.parse
                target_url = f"{API_URL}?{urllib.parse.urlencode(params)}"
                proxy_url = f"https://api.codetabs.com/v1/proxy?quest={urllib.parse.quote(target_url)}"
                response = requests.get(proxy_url, timeout=30)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"⚠️ Direct request failed: {e}. Trying fallback via CodeTabs proxy...")
            try:
                import urllib.parse
                target_url = f"{API_URL}?{urllib.parse.urlencode(params)}"
                proxy_url = f"https://api.codetabs.com/v1/proxy?quest={urllib.parse.quote(target_url)}"
                response = requests.get(proxy_url, timeout=30)
                response.raise_for_status()
                data = response.json()
            except Exception as proxy_err:
                print(f"❌ Error querying API (including proxy fallback): {proxy_err}", file=sys.stderr)
                sys.exit(1)
            
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
