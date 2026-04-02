from flask import Blueprint, jsonify, current_app
from db import get_connection

bp = Blueprint("stats", __name__)

@bp.route("/api/stats")
def stats():
    conn = get_connection(current_app.config["DB_PATH"])
    try:
        total_reports = conn.execute("SELECT COUNT(*) as c FROM reports").fetchone()["c"]
        total_tags = conn.execute(
            "SELECT COUNT(DISTINCT tag_id) as c FROM report_tags").fetchone()["c"]
        total_threads = conn.execute(
            "SELECT COUNT(DISTINCT thread) as c FROM reports WHERE thread IS NOT NULL").fetchone()["c"]
        return jsonify({
            "total_reports": total_reports,
            "total_tags": total_tags,
            "total_threads": total_threads,
        })
    finally:
        conn.close()
