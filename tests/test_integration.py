import json


def _register(client, path, title, topic, tags, thread=None, date="2026-04-02",
              sources=None, word_count=1000, image_count=0, parent_id=None):
    payload = {
        "path": path, "title": title, "topic": topic, "tags": tags,
        "date": date, "sources": sources or [], "word_count": word_count,
        "image_count": image_count,
    }
    if thread:
        payload["thread"] = thread
    if parent_id:
        payload["parent_id"] = parent_id
    resp = client.post("/api/reports", json=payload)
    assert resp.status_code == 201, f"Failed to register {title}: {resp.data}"
    return json.loads(resp.data)["id"]


def test_full_lifecycle(client):
    id1 = _register(client, path="Research Reports/AI Agent Architectures.md",
        title="AI Agent Architectures", topic="AI Agents",
        tags=["ai", "agents", "architecture"], thread="ai-agents",
        date="2026-04-01", sources=["youtube", "web"], word_count=15000)
    id2 = _register(client, path="Research Reports/IBM Agentic AI Strategy.md",
        title="IBM Agentic AI Strategy", topic="IBM AI",
        tags=["ai", "agents", "ibm", "enterprise"], thread="ai-agents",
        date="2026-04-02", parent_id=id1, sources=["web"], word_count=18000)
    id3 = _register(client, path="Research Reports/CyberSecurity Report.md",
        title="CyberSecurity Report", topic="CyberSecurity",
        tags=["security", "cyber"], thread="cybersec",
        date="2026-04-02", sources=["web", "reddit"], word_count=9000)
    id4 = _register(client, path="Personal Vault/Research Reports/Voice AI.md",
        title="Voice AI Companions", topic="Voice AI",
        tags=["ai", "voice"], date="2026-04-02", word_count=12000)

    # Verify reports list
    resp = client.get("/api/reports")
    data = json.loads(resp.data)
    assert len(data) == 4
    assert data[0]["date"] >= data[-1]["date"]

    # Verify tag filtering
    resp = client.get("/api/reports?tag=ai")
    data = json.loads(resp.data)
    assert len(data) == 3
    titles = {r["title"] for r in data}
    assert "CyberSecurity Report" not in titles

    resp = client.get("/api/reports?tag=ibm")
    data = json.loads(resp.data)
    assert len(data) == 1
    assert data[0]["title"] == "IBM Agentic AI Strategy"

    # Verify thread filtering
    resp = client.get("/api/reports?thread=ai-agents")
    data = json.loads(resp.data)
    assert len(data) == 2

    # Verify threads list
    resp = client.get("/api/threads")
    data = json.loads(resp.data)
    assert len(data) == 2
    thread_names = {t["name"] for t in data}
    assert thread_names == {"ai-agents", "cybersec"}
    ai_thread = next(t for t in data if t["name"] == "ai-agents")
    assert ai_thread["report_count"] == 2

    # Verify thread detail (ordered by date ASC)
    resp = client.get("/api/threads/ai-agents")
    data = json.loads(resp.data)
    assert len(data["reports"]) == 2
    assert data["reports"][0]["title"] == "AI Agent Architectures"
    assert data["reports"][1]["title"] == "IBM Agentic AI Strategy"

    # Verify tags list
    resp = client.get("/api/tags")
    data = json.loads(resp.data)
    tag_map = {t["name"]: t["count"] for t in data}
    assert tag_map["ai"] == 3
    assert tag_map["agents"] == 2
    assert tag_map["security"] == 1
    assert tag_map["voice"] == 1

    # Verify tag graph
    resp = client.get("/api/tags/graph")
    data = json.loads(resp.data)
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0
    ai_agents_edge = next(
        (e for e in data["edges"] if {e["source"], e["target"]} == {"agents", "ai"}), None)
    assert ai_agents_edge is not None
    assert ai_agents_edge["weight"] == 2

    # Verify MOC render
    resp = client.get("/api/moc/render")
    assert resp.status_code == 200
    moc = resp.data.decode()
    assert "# Research Index" in moc
    assert "ai-agents (2 reports)" in moc
    assert "cybersec (1 reports)" in moc
    assert "[[AI Agent Architectures]]" in moc
    assert "[[IBM Agentic AI Strategy]]" in moc
    assert "[[Voice AI Companions]]" in moc

    # Verify stats
    resp = client.get("/api/stats")
    data = json.loads(resp.data)
    assert data["total_reports"] == 4
    assert data["total_threads"] == 2
    assert data["total_tags"] >= 7

    # Verify individual report with tags
    resp = client.get(f"/api/reports/{id2}")
    data = json.loads(resp.data)
    assert data["title"] == "IBM Agentic AI Strategy"
    assert data["parent_id"] == id1
    assert set(data["tags"]) == {"ai", "agents", "ibm", "enterprise"}
    assert data["sources"] == ["web"]


def test_duplicate_tags_normalized(client):
    _register(client, "r1.md", "R1", "T1", tags=["AI", "Agents"], date="2026-04-02")
    _register(client, "r2.md", "R2", "T2", tags=["ai", "agents"], date="2026-04-02")
    resp = client.get("/api/tags")
    data = json.loads(resp.data)
    tag_map = {t["name"]: t["count"] for t in data}
    assert tag_map["ai"] == 2
    assert tag_map["agents"] == 2
    assert "AI" not in tag_map


def test_unthreaded_reports_in_moc(client):
    _register(client, "r1.md", "Standalone Report", "Topic", tags=["misc"], date="2026-04-02")
    resp = client.get("/api/moc/render")
    moc = resp.data.decode()
    assert "Unthreaded" in moc
    assert "[[Standalone Report]]" in moc


def test_empty_state(client):
    resp = client.get("/api/reports")
    assert json.loads(resp.data) == []
    resp = client.get("/api/threads")
    assert json.loads(resp.data) == []
    resp = client.get("/api/tags")
    assert json.loads(resp.data) == []
    resp = client.get("/api/tags/graph")
    data = json.loads(resp.data)
    assert data == {"nodes": [], "edges": []}
    resp = client.get("/api/stats")
    data = json.loads(resp.data)
    assert data["total_reports"] == 0
    resp = client.get("/api/moc/render")
    moc = resp.data.decode()
    assert "# Research Index" in moc
