import json

def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["status"] == "ok"
    assert "uptime_seconds" in data


def test_register_report(client):
    payload = {
        "path": "Research Reports/AI Agents.md",
        "title": "AI Agent Architectures",
        "topic": "AI Agents",
        "tags": ["ai", "agents", "architecture"],
        "thread": "ai-agents",
        "date": "2026-04-02",
        "sources": ["youtube", "web"],
        "word_count": 15000,
        "image_count": 2,
    }
    resp = client.post("/api/reports", json=payload)
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["id"] == 1
    assert data["title"] == "AI Agent Architectures"


def test_register_report_missing_required_fields(client):
    resp = client.post("/api/reports", json={"title": "Incomplete"})
    assert resp.status_code == 400


def test_list_reports(client):
    for i in range(3):
        client.post("/api/reports", json={
            "path": f"reports/report-{i}.md",
            "title": f"Report {i}",
            "topic": f"Topic {i}",
            "tags": ["ai"],
            "date": "2026-04-02",
        })
    resp = client.get("/api/reports")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) == 3


def test_list_reports_filter_by_tag(client):
    client.post("/api/reports", json={
        "path": "r1.md", "title": "R1", "topic": "T1",
        "tags": ["ai", "security"], "date": "2026-04-02",
    })
    client.post("/api/reports", json={
        "path": "r2.md", "title": "R2", "topic": "T2",
        "tags": ["gaming"], "date": "2026-04-02",
    })
    resp = client.get("/api/reports?tag=security")
    data = json.loads(resp.data)
    assert len(data) == 1
    assert data[0]["title"] == "R1"


def test_list_reports_filter_by_thread(client):
    client.post("/api/reports", json={
        "path": "r1.md", "title": "R1", "topic": "T1",
        "tags": ["ai"], "thread": "ai-agents", "date": "2026-04-02",
    })
    client.post("/api/reports", json={
        "path": "r2.md", "title": "R2", "topic": "T2",
        "tags": ["gaming"], "thread": "poe", "date": "2026-04-02",
    })
    resp = client.get("/api/reports?thread=ai-agents")
    data = json.loads(resp.data)
    assert len(data) == 1
    assert data[0]["title"] == "R1"


def test_get_report_by_id(client):
    client.post("/api/reports", json={
        "path": "r1.md", "title": "R1", "topic": "T1",
        "tags": ["ai", "agents"], "date": "2026-04-02",
    })
    resp = client.get("/api/reports/1")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["title"] == "R1"
    assert set(data["tags"]) == {"ai", "agents"}


def test_get_report_not_found(client):
    resp = client.get("/api/reports/999")
    assert resp.status_code == 404


# --- Thread tests ---

def test_list_threads(client):
    client.post("/api/reports", json={
        "path": "r1.md", "title": "R1", "topic": "T1",
        "tags": ["ai"], "thread": "ai-agents", "date": "2026-04-02",
    })
    client.post("/api/reports", json={
        "path": "r2.md", "title": "R2", "topic": "T2",
        "tags": ["ai"], "thread": "ai-agents", "date": "2026-04-03",
    })
    client.post("/api/reports", json={
        "path": "r3.md", "title": "R3", "topic": "T3",
        "tags": ["gaming"], "thread": "poe", "date": "2026-04-01",
    })
    resp = client.get("/api/threads")
    data = json.loads(resp.data)
    assert len(data) == 2
    ai_thread = next(t for t in data if t["name"] == "ai-agents")
    assert ai_thread["report_count"] == 2


def test_get_thread_detail(client):
    client.post("/api/reports", json={
        "path": "r1.md", "title": "Architectures", "topic": "AI",
        "tags": ["ai"], "thread": "ai-agents", "date": "2026-04-01",
    })
    client.post("/api/reports", json={
        "path": "r2.md", "title": "IBM Strategy", "topic": "AI",
        "tags": ["ai", "ibm"], "thread": "ai-agents", "date": "2026-04-02",
    })
    resp = client.get("/api/threads/ai-agents")
    data = json.loads(resp.data)
    assert data["name"] == "ai-agents"
    assert len(data["reports"]) == 2
    assert data["reports"][0]["title"] == "Architectures"


def test_get_thread_not_found(client):
    resp = client.get("/api/threads/nonexistent")
    assert resp.status_code == 404


# --- Tag tests ---

def test_list_tags(client):
    client.post("/api/reports", json={
        "path": "r1.md", "title": "R1", "topic": "T1",
        "tags": ["ai", "agents"], "date": "2026-04-02",
    })
    client.post("/api/reports", json={
        "path": "r2.md", "title": "R2", "topic": "T2",
        "tags": ["ai", "security"], "date": "2026-04-02",
    })
    resp = client.get("/api/tags")
    data = json.loads(resp.data)
    ai_tag = next(t for t in data if t["name"] == "ai")
    assert ai_tag["count"] == 2


def test_tag_graph(client):
    client.post("/api/reports", json={
        "path": "r1.md", "title": "R1", "topic": "T1",
        "tags": ["ai", "agents", "security"], "date": "2026-04-02",
    })
    resp = client.get("/api/tags/graph")
    data = json.loads(resp.data)
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 3
    assert len(data["edges"]) == 3


# --- MOC tests ---

def test_moc_render(client):
    client.post("/api/reports", json={
        "path": "Research Reports/AI Agents.md", "title": "AI Agents",
        "topic": "AI", "tags": ["ai"], "thread": "ai-agents", "date": "2026-04-02",
    })
    resp = client.get("/api/moc/render")
    assert resp.status_code == 200
    text = resp.data.decode()
    assert "# Research Index" in text
    assert "ai-agents" in text
    assert "[[AI Agents]]" in text


# --- Stats tests ---

def test_stats(client):
    client.post("/api/reports", json={
        "path": "r1.md", "title": "R1", "topic": "T1",
        "tags": ["ai", "agents"], "thread": "ai-agents", "date": "2026-04-02",
    })
    resp = client.get("/api/stats")
    data = json.loads(resp.data)
    assert data["total_reports"] == 1
    assert data["total_tags"] == 2
    assert data["total_threads"] == 1
