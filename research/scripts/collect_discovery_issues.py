"""Collect the frozen bounded public-issue screen in GitHub Actions."""
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

REPOS = ("temporalio/sdk-python", "dbos-inc/dbos-transact-py", "restatedev/restate")
TERMS = ("cancel", "replay", "version")


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Run the discovery collection in GitHub Actions.")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "durable-research-discovery"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    queries, records = [], {}
    for repo in REPOS:
        for term in TERMS:
            query = f"repo:{repo} is:issue created:2025-01-01..2026-10-09 {term} in:title,body"
            url = "https://api.github.com/search/issues?" + urllib.parse.urlencode(
                {"q": query, "sort": "created", "order": "asc", "per_page": 5})
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
                        data = json.load(response)
                    break
                except urllib.error.HTTPError as exc:
                    if exc.code not in (403, 429) or attempt == 2:
                        raise
                    time.sleep(60)
            selected = []
            for item in data["items"]:
                key = f"{repo}#{item['number']}"
                selected.append(key)
                body = item.get("body") or ""
                records.setdefault(key, {
                    "key": key, "url": item["html_url"], "title": item["title"],
                    "created_at": item["created_at"], "updated_at": item["updated_at"],
                    "state": item["state"], "comments": item["comments"],
                    "body_sha256": hashlib.sha256(body.encode()).hexdigest(),
                    "body_excerpt": " ".join(body.split()[:90]),
                })
            queries.append({"query": query, "total_count": data["total_count"],
                            "incomplete_results": data["incomplete_results"], "selected": selected})
    output = {
        "schema": 1, "kind": "exploratory_issue_screen",
        "run_url": f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
        "checkout_commit": os.environ["GITHUB_SHA"], "queries": queries,
        "records": list(records.values()),
        "limits": "First five per query; not a representative sample or prevalence estimate.",
    }
    path = Path("research/results/discovery/screen.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n")
    print("DISCOVERY_SCREEN_JSON=" + json.dumps(output, separators=(",", ":")))


if __name__ == "__main__":
    main()
