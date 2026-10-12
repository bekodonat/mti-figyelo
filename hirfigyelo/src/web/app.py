import os
import sqlite3
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import DB_PATH
from run_pipeline import main as run_pipeline_cycle, get_pipeline_summary

app = Flask(__name__, template_folder="templates", static_folder="static")


@app.template_filter("format_latency")
def format_latency_filter(mins):
    if mins is None:
        return "-"
    try:
        mins = int(mins)
    except (ValueError, TypeError):
        return "-"
    if mins < 0:
        return "-"
    hours = mins // 60
    rem_mins = mins % 60
    if hours > 0 and rem_mins > 0:
        return f"+{hours} óra {rem_mins} perc"
    elif hours > 0:
        return f"+{hours} óra"
    else:
        return f"+{rem_mins} perc"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    stats = get_pipeline_summary()
    conn = get_db_connection()

    # 1. Fetch Clusters (MTI News with their matched articles)
    clusters_query = """
    SELECT 
        m.id as mti_id, m.title as mti_title, m.lead as mti_lead, m.published_at as mti_pub,
        m.url as mti_url, m.is_hot, m.is_updated, m.word_count as mti_words,
        COUNT(mt.id) as match_count
    FROM mti_news m
    LEFT JOIN matches mt ON m.id = mt.mti_id
    GROUP BY m.id
    ORDER BY match_count DESC, m.published_at DESC
    """
    mti_clusters = conn.execute(clusters_query).fetchall()

    from dateutil import parser as date_parser
    now = datetime.now()

    clusters_data = []
    for m in mti_clusters:
        # Fetch matching articles for this MTI story
        matches = conn.execute(
            """
            SELECT 
                a.id, a.title, a.lead, a.published_at, a.has_mti_citation, a.url, a.word_count,
                o.name as outlet_name, o.slug as outlet_slug,
                mt.similarity_score, mt.latency_minutes
            FROM matches mt
            JOIN articles a ON mt.article_id = a.id
            JOIN outlets o ON a.outlet_id = o.id
            WHERE mt.mti_id = ?
            ORDER BY mt.similarity_score DESC
            """,
            (m["mti_id"],),
        ).fetchall()

        # Calculate age in hours for relevance ranking
        try:
            pub_dt = date_parser.parse(m["mti_pub"])
            age_hours = max(0.1, (now - pub_dt).total_seconds() / 3600.0)
        except Exception:
            age_hours = 24.0

        match_count = len(matches)
        # Relevance: high match count + fresh news (recency decay)
        # Each match gives 100 points, each hour elapsed deducts 1.5 points
        if match_count > 0:
            relevance_score = round((match_count * 100.0) - (age_hours * 1.5), 2)
        else:
            relevance_score = round(-100.0 - age_hours, 2)

        clusters_data.append({
            "mti": dict(m),
            "matches": [dict(match) for match in matches],
            "relevance_score": relevance_score,
            "age_hours": round(age_hours, 1),
        })

    # Default sort by relevance (újabb + legtöbb hivatkozás)
    clusters_data.sort(key=lambda c: c["relevance_score"], reverse=True)

    # 2. Fetch outlets for filter dropdown and stats
    outlets = conn.execute("SELECT id, name, slug FROM outlets ORDER BY name ASC").fetchall()

    outlet_stats = conn.execute(
        """
        SELECT 
            o.name, o.slug,
            COUNT(a.id) as total_articles,
            SUM(CASE WHEN a.has_mti_citation = 1 THEN 1 ELSE 0 END) as mti_cited,
            COUNT(m.id) as matched_count,
            ROUND(AVG(m.latency_minutes), 0) as avg_latency
        FROM outlets o
        LEFT JOIN articles a ON o.id = a.outlet_id
        LEFT JOIN matches m ON a.id = m.article_id
        GROUP BY o.id
        ORDER BY total_articles DESC
        """
    ).fetchall()

    conn.close()
    return render_template(
        "index.html",
        stats=stats,
        clusters=clusters_data,
        outlets=outlets,
        outlet_stats=outlet_stats,
    )


@app.route("/api/articles")
def api_articles():
    outlet_id = request.args.get("outlet_id", "")
    mti_only = request.args.get("mti_only", "")
    search = request.args.get("search", "")
    page = int(request.args.get("page", 1))
    per_page = 30
    offset = (page - 1) * per_page

    conn = get_db_connection()
    query = """
        SELECT a.id, a.title, a.lead, a.published_at, a.has_mti_citation, 
               a.citation_excerpt, a.word_count, a.url, o.name as outlet_name
        FROM articles a
        JOIN outlets o ON a.outlet_id = o.id
        WHERE 1=1
    """
    params = []

    if outlet_id:
        query += " AND a.outlet_id = ?"
        params.append(outlet_id)

    if mti_only == "1":
        query += " AND a.has_mti_citation = 1"

    if search:
        query += " AND (a.title LIKE ? OR a.content_raw LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term])

    count_query = f"SELECT COUNT(*) FROM ({query})"
    total = conn.execute(count_query, params).fetchone()[0]

    query += " ORDER BY a.published_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    articles = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "articles": [dict(a) for a in articles],
    })


@app.route("/api/article/<int:article_id>")
def api_article_detail(article_id):
    conn = get_db_connection()
    row = conn.execute(
        """
        SELECT a.*, o.name as outlet_name 
        FROM articles a 
        JOIN outlets o ON a.outlet_id = o.id 
        WHERE a.id = ?
        """,
        (article_id,),
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Nem található"}), 404
    return jsonify(dict(row))


@app.route("/api/mti-news/<int:mti_id>")
def api_mti_detail(mti_id):
    conn = get_db_connection()
    row = conn.execute(
        """
        SELECT id, guid, url, title, lead, content_raw, published_at, is_hot, word_count
        FROM mti_news
        WHERE id = ?
        """,
        (mti_id,),
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Nem található"}), 404
    return jsonify(dict(row))


@app.route("/api/run-pipeline", methods=["POST"])
def api_run_pipeline():
    try:
        run_pipeline_cycle()
        stats = get_pipeline_summary()
        return jsonify({"status": "success", "stats": stats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=False)
