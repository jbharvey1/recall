# backfill.py
"""One-time script to import existing research reports into the index."""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_BASE = os.getenv("RECALL_API", sys.argv[1] if len(sys.argv) > 1 else "https://localhost:9400")

REPORT_DIRS = [
    Path(p.strip())
    for p in os.getenv("RECALL_REPORT_DIRS", "reports").split(",")
    if p.strip()
]

TAG_KEYWORDS = {
    "ai": ["artificial intelligence", "machine learning", "llm", "gpt", "claude", "gemini"],
    "agents": ["agentic", "ai agent", "multi-agent", "orchestrat"],
    "security": ["cybersecurity", "security", "threat", "vulnerability", "soc"],
    "ibm": ["ibm", "watsonx", "granite"],
    "voice": ["voice ai", "speech-to-text", "tts", "stt", "voice assistant"],
    "infrastructure": ["ec2", "aws", "docker", "server setup", "tailscale"],
    "poe": ["path of exile", "poe ", "farming", "currency"],
    "finance": ["bank", "transaction", "recurring charge", "financial"],
    "enterprise": ["enterprise", "consulting", "accenture", "deloitte"],
    "gaming": ["gaming", "game", "arpg"],
}


def extract_title(content: str, filename: str) -> str:
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        title = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        return title
    return filename.replace(".md", "").replace("-", " ").title()


def extract_date(content: str, filepath: Path) -> str:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", filepath.name)
    if match:
        return match.group(1)
    for pattern in [
        r"\*?(?:Date|Research Date|Created|Generated)[:\s]*(\d{4}-\d{2}-\d{2})",
        r"(\d{4}-\d{2}-\d{2})",
    ]:
        match = re.search(pattern, content[:500])
        if match:
            return match.group(1)
    mtime = filepath.stat().st_mtime
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")


def infer_tags(content: str) -> list[str]:
    content_lower = content.lower()
    tags = []
    for tag, keywords in TAG_KEYWORDS.items():
        if any(kw in content_lower for kw in keywords):
            tags.append(tag)
    return tags if tags else ["untagged"]


def infer_thread(tags: list[str], title: str) -> str | None:
    title_lower = title.lower()
    if "agents" in tags or "agentic" in title_lower:
        return "ai-agents"
    if "security" in tags or "cyber" in tags:
        return "cybersec"
    if "poe" in tags:
        return "poe"
    if "voice" in tags:
        return "voice-ai"
    if "finance" in tags:
        return "finance"
    return None


def count_words(content: str) -> int:
    text = re.sub(r"[#*_`\[\]|<>{}]", " ", content)
    return len(text.split())


def register(report: dict) -> bool:
    try:
        resp = requests.post(f"{API_BASE}/api/reports", json=report, verify=False, timeout=10)
        if resp.status_code == 201:
            print(f"  + Registered: {report['title']}")
            return True
        else:
            print(f"  X Failed ({resp.status_code}): {report['title']}: {resp.text}")
            return False
    except Exception as e:
        print(f"  X Error: {report['title']}: {e}")
        return False


def main():
    total = 0
    success = 0

    for report_dir in REPORT_DIRS:
        if not report_dir.exists():
            print(f"Skipping {report_dir} (not found)")
            continue

        print(f"\nScanning {report_dir}...")
        for md_file in sorted(report_dir.glob("*.md")):
            if md_file.name == "Research Index.md":
                continue

            total += 1
            content = md_file.read_text(encoding="utf-8", errors="replace")
            title = extract_title(content, md_file.name)
            date = extract_date(content, md_file)
            tags = infer_tags(content)
            thread = infer_thread(tags, title)
            word_count = count_words(content)

            vault_root = os.getenv("RECALL_VAULT_ROOT")
            if vault_root:
                try:
                    rel_path = md_file.relative_to(Path(vault_root))
                except ValueError:
                    rel_path = md_file.name
            else:
                rel_path = md_file.name

            report = {
                "path": str(rel_path),
                "title": title,
                "topic": title,
                "tags": tags,
                "thread": thread,
                "date": date,
                "sources": [],
                "word_count": word_count,
                "image_count": 0,
            }

            if register(report):
                success += 1

    print(f"\nDone: {success}/{total} reports registered")


if __name__ == "__main__":
    main()
