# tests/test_backfill.py
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backfill import extract_title, extract_date, infer_tags, infer_thread, count_words


class TestExtractTitle:
    def test_extracts_from_h1(self):
        content = "# AI Agent Architectures\n\nSome body text."
        assert extract_title(content, "fallback.md") == "AI Agent Architectures"

    def test_strips_html_from_h1(self):
        content = '<h1 style="color: red;">Report Title</h1>\n\n# Actual Title'
        assert extract_title(content, "fallback.md") == "Actual Title"

    def test_falls_back_to_filename(self):
        content = "No headings here, just text."
        assert extract_title(content, "my-cool-report.md") == "My Cool Report"

    def test_skips_h2(self):
        content = "## This is H2\n\nBody text."
        assert extract_title(content, "fallback.md") == "Fallback"


class TestExtractDate:
    def test_from_filename(self, tmp_path):
        f = tmp_path / "2026-04-02-ai-agents.md"
        f.write_text("content")
        assert extract_date("content", f) == "2026-04-02"

    def test_from_content_date_field(self, tmp_path):
        f = tmp_path / "report.md"
        f.write_text("content")
        content = "**Date:** 2026-03-31\n\nBody text."
        assert extract_date(content, f) == "2026-03-31"

    def test_from_research_date_field(self, tmp_path):
        f = tmp_path / "report.md"
        f.write_text("content")
        content = "*Research Date: 2026-04-01*\n\nBody."
        assert extract_date(content, f) == "2026-04-01"

    def test_falls_back_to_mtime(self, tmp_path):
        f = tmp_path / "no-date.md"
        f.write_text("No date anywhere in here whatsoever.")
        result = extract_date("No date anywhere in here whatsoever.", f)
        assert len(result) == 10 and result[4] == "-"


class TestInferTags:
    def test_ai_content(self):
        tags = infer_tags("This report covers artificial intelligence and LLM architectures.")
        assert "ai" in tags

    def test_agents_content(self):
        tags = infer_tags("Agentic AI and multi-agent orchestration patterns.")
        assert "agents" in tags

    def test_security_content(self):
        tags = infer_tags("Cybersecurity threat landscape and vulnerability assessment.")
        assert "security" in tags

    def test_poe_content(self):
        tags = infer_tags("Path of Exile farming strategies for currency.")
        assert "poe" in tags

    def test_no_matches_returns_untagged(self):
        tags = infer_tags("A completely generic document with no keywords.")
        assert tags == ["untagged"]

    def test_multiple_tags(self):
        tags = infer_tags("IBM watsonx agentic LLM platform for cybersecurity.")
        assert "ai" in tags
        assert "ibm" in tags
        assert "agents" in tags
        assert "security" in tags


class TestInferThread:
    def test_agents_thread(self):
        assert infer_thread(["ai", "agents"], "AI Agent Architectures") == "ai-agents"

    def test_security_thread(self):
        assert infer_thread(["security"], "CyberSecurity Report") == "cybersec"

    def test_poe_thread(self):
        assert infer_thread(["poe"], "Farming Guide") == "poe"

    def test_no_thread(self):
        assert infer_thread(["untagged"], "Random Notes") is None


class TestCountWords:
    def test_basic(self):
        assert count_words("one two three four five") == 5

    def test_strips_markdown(self):
        count = count_words("# Heading\n\n**Bold** text with `code` and [links](url)")
        assert count > 0
