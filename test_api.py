import requests
import sys

URL = "https://gemeinsam.oldenburg.de/backend/v1/flaw-reporter/findPageableReportsWithFilter?flawReporterId=24&limit=5&offset=0&sortParam=id&ascending=true"

def test_request(name, headers):
    print(f"=== Testing: {name} ===")
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        if response.status_code != 200:
            print(f"Response Body (first 500 chars): {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
    print()

def main():
    # Test 1: Standard browser headers
    test_request("Standard Browser", {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
        "Referer": "https://gemeinsam.oldenburg.de/stadtverbesserer",
        "Origin": "https://gemeinsam.oldenburg.de"
    })

    # Test 2: Custom script headers
    test_request("Custom User Agent (from fetch_reports.py)", {
        "User-Agent": "OldenburgRadDashboardDataPipeline/1.0 (contact: fatih.karahan@example.com)"
    })

    # Test 3: No User-Agent (default requests UA)
    test_request("Default requests UA", {})

if __name__ == "__main__":
    main()
