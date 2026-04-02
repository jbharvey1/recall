from datetime import date
from flask import Blueprint, current_app, Response
from db import get_connection

bp = Blueprint("moc", __name__)

@bp.route("/api/moc/render")
def render_moc():
    conn = get_connection(current_app.config["DB_PATH"])
    try:
        lines = [
            "# Research Index", "",
            f"> Auto-generated — last updated {date.today().isoformat()}", "",
            "## Threads", "",
        ]
        threads = conn.execute(
            """SELECT thread, COUNT(*) as cnt FROM reports
               WHERE thread IS NOT NULL GROUP BY thread ORDER BY thread""").fetchall()
        for thread in threads:
            lines.append(f"### {thread['thread']} ({thread['cnt']} reports)")
            reports = conn.execute(
                "SELECT * FROM reports WHERE thread = ? ORDER BY date ASC",
                (thread["thread"],)).fetchall()
            for r in reports:
                tag_rows = conn.execute(
                    """SELECT t.name FROM tags t
                       JOIN report_tags rt ON t.id = rt.tag_id
                       WHERE rt.report_id = ?""", (r["id"],)).fetchall()
                tags = ", ".join(t["name"] for t in tag_rows)
                lines.append(f"- [[{r['title']}]] — {r['date']} · {tags}")
            lines.append("")
        unthreaded = conn.execute(
            "SELECT * FROM reports WHERE thread IS NULL ORDER BY date DESC").fetchall()
        if unthreaded:
            lines.append("### Unthreaded")
            for r in unthreaded:
                tag_rows = conn.execute(
                    """SELECT t.name FROM tags t
                       JOIN report_tags rt ON t.id = rt.tag_id
                       WHERE rt.report_id = ?""", (r["id"],)).fetchall()
                tags = ", ".join(t["name"] for t in tag_rows)
                lines.append(f"- [[{r['title']}]] — {r['date']} · {tags}")
            lines.append("")
        all_tags = conn.execute(
            """SELECT t.name, COUNT(rt.report_id) as cnt
               FROM tags t JOIN report_tags rt ON t.id = rt.tag_id
               GROUP BY t.id ORDER BY cnt DESC""").fetchall()
        if all_tags:
            lines.append("## All Tags")
            lines.append(" · ".join(f"{t['name']} ({t['cnt']})" for t in all_tags))
            lines.append("")
        return Response("\n".join(lines), mimetype="text/plain")
    finally:
        conn.close()
