import json
from flask import Blueprint, request, jsonify, current_app
from db import get_connection

bp = Blueprint("reports", __name__)

def _get_db():
    return get_connection(current_app.config["DB_PATH"])

def _ensure_tags(conn, tag_names: list[str]) -> list[int]:
    tag_ids = []
    for name in tag_names:
        name = name.strip().lower()
        conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
        row = conn.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()
        tag_ids.append(row["id"])
    return tag_ids

@bp.route("/api/reports", methods=["POST"])
def register_report():
    data = request.get_json(force=True)
    required = ["path", "title", "topic", "date"]
    if not all(data.get(f) for f in required):
        return jsonify({"error": f"Missing required fields: {required}"}), 400
    conn = _get_db()
    try:
        cursor = conn.execute(
            """INSERT INTO reports (path, title, topic, thread, parent_id, date, sources, word_count, image_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data["path"], data["title"], data["topic"], data.get("thread"),
             data.get("parent_id"), data["date"], json.dumps(data.get("sources", [])),
             data.get("word_count", 0), data.get("image_count", 0)),
        )
        report_id = cursor.lastrowid
        tag_names = data.get("tags", [])
        if tag_names:
            tag_ids = _ensure_tags(conn, tag_names)
            for tid in tag_ids:
                conn.execute("INSERT INTO report_tags (report_id, tag_id) VALUES (?, ?)", (report_id, tid))
        conn.commit()
        return jsonify({"id": report_id, "title": data["title"]}), 201
    finally:
        conn.close()

@bp.route("/api/reports", methods=["GET"])
def list_reports():
    tag = request.args.get("tag")
    thread = request.args.get("thread")
    conn = _get_db()
    try:
        if tag:
            rows = conn.execute(
                """SELECT r.* FROM reports r
                   JOIN report_tags rt ON r.id = rt.report_id
                   JOIN tags t ON rt.tag_id = t.id
                   WHERE t.name = ? ORDER BY r.date DESC""",
                (tag.lower(),)).fetchall()
        elif thread:
            rows = conn.execute(
                "SELECT * FROM reports WHERE thread = ? ORDER BY date DESC",
                (thread,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM reports ORDER BY date DESC").fetchall()

        results = []
        for row in rows:
            report = dict(row)
            report["sources"] = json.loads(report["sources"])
            tag_rows = conn.execute(
                """SELECT t.name FROM tags t
                   JOIN report_tags rt ON t.id = rt.tag_id
                   WHERE rt.report_id = ?""", (report["id"],)).fetchall()
            report["tags"] = [t["name"] for t in tag_rows]
            results.append(report)
        return jsonify(results)
    finally:
        conn.close()

@bp.route("/api/reports/<int:report_id>", methods=["GET"])
def get_report(report_id):
    conn = _get_db()
    try:
        row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        report = dict(row)
        report["sources"] = json.loads(report["sources"])
        tag_rows = conn.execute(
            """SELECT t.name FROM tags t
               JOIN report_tags rt ON t.id = rt.tag_id
               WHERE rt.report_id = ?""", (report_id,)).fetchall()
        report["tags"] = [t["name"] for t in tag_rows]
        return jsonify(report)
    finally:
        conn.close()
