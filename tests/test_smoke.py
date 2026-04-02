# tests/test_smoke.py
"""
Smoke test for deployed research-index service.
Run: python tests/test_smoke.py <api-url>
Example: python tests/test_smoke.py https://100.118.62.104:9400
"""
import json
import sys
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API = sys.argv[1] if len(sys.argv) > 1 else "https://localhost:9400"
PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  + {name}")
    else:
        FAIL += 1
        print(f"  X {name} -- {detail}")


def get(path):
    return requests.get(f"{API}{path}", verify=False, timeout=10)


def post(path, data):
    return requests.post(f"{API}{path}", json=data, verify=False, timeout=10)


def main():
    print(f"\n=== Smoke Testing {API} ===\n")

    print("[Health]")
    r = get("/api/health")
    check("Health returns 200", r.status_code == 200)
    if r.status_code == 200:
        data = r.json()
        check("Status is ok", data.get("status") == "ok")
        check("Uptime present", "uptime_seconds" in data)

    print("\n[Stats]")
    r = get("/api/stats")
    check("Stats returns 200", r.status_code == 200)
    if r.status_code == 200:
        data = r.json()
        check("Has total_reports", "total_reports" in data)
        check("Reports > 0 (backfill ran)", data.get("total_reports", 0) > 0,
              f"got {data.get('total_reports', 0)}")

    print("\n[Reports]")
    r = get("/api/reports")
    check("Reports list returns 200", r.status_code == 200)
    if r.status_code == 200:
        data = r.json()
        check("Reports is a list", isinstance(data, list))
        if data:
            check("First report has title", "title" in data[0])
            check("First report has tags", "tags" in data[0])
            check("First report has date", "date" in data[0])

    print("\n[Tags]")
    r = get("/api/tags")
    check("Tags returns 200", r.status_code == 200)
    if r.status_code == 200:
        data = r.json()
        check("Tags is a list", isinstance(data, list))
        check("Has at least 1 tag", len(data) > 0, f"got {len(data)}")

    print("\n[Tag Graph]")
    r = get("/api/tags/graph")
    check("Graph returns 200", r.status_code == 200)
    if r.status_code == 200:
        data = r.json()
        check("Has nodes", len(data.get("nodes", [])) > 0)
        check("Has edges", len(data.get("edges", [])) > 0)

    print("\n[Threads]")
    r = get("/api/threads")
    check("Threads returns 200", r.status_code == 200)
    if r.status_code == 200:
        data = r.json()
        check("Threads is a list", isinstance(data, list))

    print("\n[MOC]")
    r = get("/api/moc/render")
    check("MOC returns 200", r.status_code == 200)
    if r.status_code == 200:
        text = r.text
        check("MOC contains header", "# Research Index" in text)
        check("MOC contains Obsidian links", "[[" in text)

    print("\n[Dashboard]")
    r = get("/")
    check("Dashboard returns 200", r.status_code == 200)
    check("Dashboard is HTML", "text/html" in r.headers.get("Content-Type", ""))

    print("\n[Register Round-Trip]")
    test_payload = {
        "path": "_smoke_test/smoke-test.md",
        "title": "Smoke Test Report",
        "topic": "Smoke Test",
        "tags": ["smoke-test"],
        "date": "2026-01-01",
        "word_count": 100,
    }
    r = post("/api/reports", test_payload)
    check("Register returns 201", r.status_code == 201)
    if r.status_code == 201:
        rid = r.json()["id"]
        r2 = get(f"/api/reports/{rid}")
        check("Can retrieve by ID", r2.status_code == 200)
        if r2.status_code == 200:
            check("Title matches", r2.json()["title"] == "Smoke Test Report")
            check("Tags match", r2.json()["tags"] == ["smoke-test"])

    print(f"\n=== Results: {PASS} passed, {FAIL} failed ===")
    sys.exit(1 if FAIL > 0 else 0)


if __name__ == "__main__":
    main()
