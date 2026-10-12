import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Any, List

import httpx

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import DB_PATH, BASE_DIR

logger = logging.getLogger("sheets_sync")


def get_sheets_payload() -> Dict[str, List[List[Any]]]:
    """Extract and format all database records into structured sheets/tabs."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Tab 1: Hírcsaládok & Mutációk
    matches_rows = [
        [
            "MTI_ID", "MTI_Cím", "MTI_Dátum", "Portál", "Portál_Cím", 
            "Portál_Link", "Hasonlóság_%", "Késleltetés_Perc", "MTI_Idézve"
        ]
    ]
    cursor = conn.execute(
        """
        SELECT 
            m.id as mti_id, m.title as mti_title, m.published_at as mti_pub,
            o.name as outlet_name, a.title as art_title, a.url as art_url,
            mt.similarity_score, mt.latency_minutes, a.has_mti_citation
        FROM matches mt
        JOIN mti_news m ON mt.mti_id = m.id
        JOIN articles a ON mt.article_id = a.id
        JOIN outlets o ON a.outlet_id = o.id
        ORDER BY m.published_at DESC, mt.similarity_score DESC
        """
    )
    for r in cursor.fetchall():
        matches_rows.append([
            r["mti_id"],
            r["mti_title"],
            r["mti_pub"],
            r["outlet_name"],
            r["art_title"],
            r["art_url"],
            f"{round(r['similarity_score'] * 100, 1)}%",
            r["latency_minutes"],
            "IGEN" if r["has_mti_citation"] else "NEM",
        ])

    # Tab 2: Összes Cikk (szöveggel és metaadatokkal)
    articles_rows = [
        [
            "Cikk_ID", "Portál", "Cím", "Lead", "Megjelenés_Ideje", 
            "Szószám", "MTI_Hivatkozás", "MTI_Idézet_Kivonat", "URL", "Teljes_Szöveg"
        ]
    ]
    cursor = conn.execute(
        """
        SELECT 
            a.id, o.name as outlet_name, a.title, a.lead, a.published_at,
            a.word_count, a.has_mti_citation, a.citation_excerpt, a.url, a.content_raw
        FROM articles a
        JOIN outlets o ON a.outlet_id = o.id
        ORDER BY a.published_at DESC
        """
    )
    for r in cursor.fetchall():
        # Clean text for spreadsheets
        full_text = (r["content_raw"] or "").replace("\r", " ")
        # Truncate if exceeds Google Sheets cell limit (50,000 chars)
        if len(full_text) > 40000:
            full_text = full_text[:40000] + "... [levágva cella-korlát miatt]"

        articles_rows.append([
            r["id"],
            r["outlet_name"],
            r["title"],
            r["lead"] or "",
            r["published_at"] or "",
            r["word_count"] or 0,
            "IGEN" if r["has_mti_citation"] else "NEM",
            r["citation_excerpt"] or "",
            r["url"],
            full_text,
        ])

    # Tab 3: Portál Statisztikák
    stats_rows = [
        ["Portál", "Összes_Cikk", "MTI_Idézéses_Cikk", "Párosított_Családok", "MTI_Arány_%", "Átlagos_Késleltetés_Perc"]
    ]
    cursor = conn.execute(
        """
        SELECT 
            o.name,
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
    )
    for r in cursor.fetchall():
        total = r["total_articles"]
        cited = r["mti_cited"] or 0
        ratio = f"{round((cited / total) * 100, 1)}%" if total > 0 else "0%"
        avg_lat = f"+{int(r['avg_latency'])} perc" if r["avg_latency"] else "-"
        stats_rows.append([
            r["name"],
            total,
            cited,
            r["matched_count"] or 0,
            ratio,
            avg_lat,
        ])

    conn.close()

    return {
        "Hircsaladok_Mutaciok": matches_rows,
        "Osszes_Cikk": articles_rows,
        "Portal_Statisztikak": stats_rows,
    }


def sync_to_google_sheet_webhook(webhook_url: str) -> bool:
    """Send formatted data payload to Google Apps Script Webhook."""
    payload = get_sheets_payload()
    try:
        logger.info(f"Adatok küldése a Google Sheet Webhookra: {webhook_url[:50]}...")
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            response = client.post(webhook_url, json=payload)
            if response.status_code == 200:
                logger.info("Google Sheet szinkronizáció sikeres!")
                return True
            else:
                logger.error(f"Google Sheet hiba ({response.status_code}): {response.text}")
                return False
    except Exception as e:
        logger.error(f"Hiba a Google Sheet szinkronizáció során: {e}")
        return False


def export_to_csv_folder(target_dir: Path = BASE_DIR / "data" / "sheets_export") -> List[Path]:
    """Export all 3 tabs into CSV files that can be directly imported into Google Sheets."""
    import csv

    target_dir.mkdir(parents=True, exist_ok=True)
    payload = get_sheets_payload()
    created_files = []

    for tab_name, rows in payload.items():
        file_path = target_dir / f"{tab_name}.csv"
        with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        created_files.append(file_path)
        logger.info(f"Exportálva: {file_path} ({len(rows)} sor)")

    return created_files


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    files = export_to_csv_folder()
    print(f"Sikeresen exportálva {len(files)} CSV fájl a data/sheets_export mappába!")
