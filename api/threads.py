import json
from flask import Blueprint, jsonify, current_app
from db import get_connection

bp = Blueprint("threads", __name__)

@bp.route("/api/threads")
def list_threads():
    conn = get_connection(current_app.config["DB_PATH"])
    try:
        rows = conn.execute(
            """SELECT thread, COUNT(*) as report_count, MAX(date) as last_updated
               FROM reports WHERE thread IS NOT NULL
               GROUP BY thread ORDER BY last_updated DESC"""
        ).fetchall()
        return jsonify([dict(name=r["thread"], report_count=r["report_count"],
                             last_updated=r["last_updated"]) for r in rows])
    finally:
        conn.close()

@bp.route("/api/threads/<name>")
def get_thread(name):
    conn = get_connection(current_app.config["DB_PATH"])
    try:
        rows = conn.execute(
            "SELECT * FROM reports WHERE thread = ? ORDER BY date ASC", (name,)
        ).fetchall()
        if not rows:
            return jsonify({"error": "Thread not found"}), 404
        reports = []
        for row in rows:
            r = dict(row)
            r["sources"] = json.loads(r["sources"])
            tag_rows = conn.execute(
                """SELECT t.name FROM tags t
                   JOIN report_tags rt ON t.id = rt.tag_id
                   WHERE rt.report_id = ?""", (r["id"],)).fetchall()
            r["tags"] = [t["name"] for t in tag_rows]
            reports.append(r)
        return jsonify({"name": name, "report_count": len(reports), "reports": reports})
    finally:
        conn.close()
