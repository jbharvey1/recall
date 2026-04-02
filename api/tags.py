from itertools import combinations
from flask import Blueprint, jsonify, current_app
from db import get_connection

bp = Blueprint("tags", __name__)

@bp.route("/api/tags")
def list_tags():
    conn = get_connection(current_app.config["DB_PATH"])
    try:
        rows = conn.execute(
            """SELECT t.name, COUNT(rt.report_id) as count
               FROM tags t JOIN report_tags rt ON t.id = rt.tag_id
               GROUP BY t.id ORDER BY count DESC""").fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()

@bp.route("/api/tags/graph")
def tag_graph():
    conn = get_connection(current_app.config["DB_PATH"])
    try:
        tag_rows = conn.execute(
            """SELECT t.name, COUNT(rt.report_id) as count
               FROM tags t JOIN report_tags rt ON t.id = rt.tag_id
               GROUP BY t.id""").fetchall()
        nodes = [{"name": r["name"], "count": r["count"]} for r in tag_rows]
        report_ids = conn.execute("SELECT DISTINCT report_id FROM report_tags").fetchall()
        edge_counts: dict[tuple[str, str], int] = {}
        for rid_row in report_ids:
            rid = rid_row["report_id"]
            tags = conn.execute(
                """SELECT t.name FROM tags t
                   JOIN report_tags rt ON t.id = rt.tag_id
                   WHERE rt.report_id = ?""", (rid,)).fetchall()
            tag_names = sorted(t["name"] for t in tags)
            for a, b in combinations(tag_names, 2):
                key = (a, b)
                edge_counts[key] = edge_counts.get(key, 0) + 1
        edges = [{"source": a, "target": b, "weight": w} for (a, b), w in edge_counts.items()]
        return jsonify({"nodes": nodes, "edges": edges})
    finally:
        conn.close()
