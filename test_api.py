import requests
import sys
import urllib.parse
import json

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

def test_allorigins():
    print("=== Testing: AllOrigins Proxy ===")
    try:
        encoded_url = urllib.parse.quote(URL)
        proxy_url = f"https://api.allorigins.win/get?url={encoded_url}"
        response = requests.get(proxy_url, timeout=15)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            contents = response.json().get("contents", "")
            print(f"Contents (first 500 chars): {contents[:500]}")
            # Try to parse as JSON
            data = json.loads(contents)
            print("Successfully parsed response contents as JSON!")
            print(f"Found totalCnt: {data.get('totalCnt')}")
        else:
            print(f"Body: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_corsproxy_io():
    print("=== Testing: Corsproxy.io ===")
    try:
        proxy_url = f"https://corsproxy.io/?{urllib.parse.quote(URL)}"
        response = requests.get(proxy_url, timeout=15)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Body (first 500 chars): {response.text[:500]}")
            data = response.json()
            print("Successfully parsed response body as JSON!")
            print(f"Found totalCnt: {data.get('totalCnt')}")
        else:
            print(f"Body: {response.text[:500]}")
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

    # Test 2: AllOrigins
    test_allorigins()

    # Test 3: Corsproxy.io
    test_corsproxy_io()

if __name__ == "__main__":
    main()
