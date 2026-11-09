#!/usr/bin/env python3
"""
Static Dashboard Exporter for GitHub Pages
Generates docs/index.html with all current news clusters, portal statistics,
and client-side searchable articles.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import DB_PATH
from dateutil import parser as date_parser
from jinja2 import Environment, FileSystemLoader


def format_latency(mins):
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


def generate_static_site(output_dir: Path = None):
    if output_dir is None:
        # Repository root / docs
        output_dir = BASE_DIR.parent / "docs"

    output_dir.mkdir(parents=True, exist_ok=True)
    # .nojekyll disables Jekyll processing on GitHub Pages
    (output_dir / ".nojekyll").touch(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # 1. Fetch Stats
    outlets_count = conn.execute("SELECT COUNT(*) FROM outlets WHERE active = 1").fetchone()[0]
    mti_total = conn.execute("SELECT COUNT(*) FROM mti_news").fetchone()[0]
    mti_hot = conn.execute("SELECT COUNT(*) FROM mti_news WHERE is_hot = 1").fetchone()[0]
    articles_total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    articles_mti_cited = conn.execute("SELECT COUNT(*) FROM articles WHERE has_mti_citation = 1").fetchone()[0]
    matches_total = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]

    last_updated_row = conn.execute("""
        SELECT datetime(MAX(ts), 'localtime') FROM (
            SELECT MAX(scraped_at) as ts FROM articles
            UNION ALL
            SELECT MAX(scraped_at) as ts FROM mti_news
        )
    """).fetchone()
    last_updated = last_updated_row[0] if last_updated_row and last_updated_row[0] else "N/A"

    stats = {
        "outlets": outlets_count,
        "mti_total": mti_total,
        "mti_hot": mti_hot,
        "articles_total": articles_total,
        "articles_mti_cited": articles_mti_cited,
        "matches_total": matches_total,
        "last_updated": last_updated,
    }

    # 2. Fetch Clusters
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
    now = datetime.now()

    clusters_data = []
    for m in mti_clusters:
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

        try:
            pub_dt = date_parser.parse(m["mti_pub"])
            age_hours = max(0.1, (now - pub_dt).total_seconds() / 3600.0)
        except Exception:
            age_hours = 24.0

        match_count = len(matches)
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

    clusters_data.sort(key=lambda c: c["relevance_score"], reverse=True)

    # 3. Fetch Outlets and Stats
    outlets = [dict(r) for r in conn.execute("SELECT id, name, slug FROM outlets ORDER BY name ASC").fetchall()]
    outlet_stats = [dict(r) for r in conn.execute("""
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
    """).fetchall()]

    # 4. Fetch Articles for Client-side Search / Browsing (all recent articles)
    articles_rows = conn.execute("""
        SELECT a.id, a.title, a.lead, a.published_at, a.has_mti_citation,
               a.citation_excerpt, a.word_count, a.url, a.outlet_id, o.name as outlet_name
        FROM articles a
        JOIN outlets o ON a.outlet_id = o.id
        ORDER BY a.published_at DESC
        LIMIT 2000
    """).fetchall()
    articles_list = [dict(r) for r in articles_rows]

    # 5. MTI news map for client-side modal viewing
    mti_map = {c["mti"]["mti_id"]: c["mti"] for c in clusters_data}

    conn.close()

    # Setup Jinja2 Environment
    template_dir = BASE_DIR / "src" / "web" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    env.filters["format_latency"] = format_latency

    # Render static template
    template = env.get_template("static_index.html")
    rendered_html = template.render(
        stats=stats,
        clusters=clusters_data,
        outlets=outlets,
        outlet_stats=outlet_stats,
        articles_json=json.dumps(articles_list, ensure_ascii=False),
        mti_json=json.dumps(mti_map, ensure_ascii=False),
        is_static=True,
    )

    output_file = output_dir / "index.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    print(f"Static dashboard successfully generated at: {output_file} ({len(articles_list)} articles embedded)")
    return output_file


if __name__ == "__main__":
    generate_static_site()
