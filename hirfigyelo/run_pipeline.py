#!/usr/bin/env python3
"""
Pipeline Orchestrator: News Mutation & Wire Drift Tracker
Runs MTI collector, Portal collector, and Matching Engine in sequence.
"""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import LOGS_DIR
from src.collectors.mti_collector import run_mti_collector
from src.collectors.portal_collector import run_portal_collector
from src.matching.engine import run_matching_engine
from src.db.database import get_db

# Configure file and stream logging
log_file = LOGS_DIR / f"pipeline_{datetime.now().strftime('%Y%m')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("pipeline")


def get_pipeline_summary() -> dict:
    """Fetch current database statistics."""
    with get_db() as conn:
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
        last_updated = last_updated_row[0] if last_updated_row and last_updated_row[0] else None

    return {
        "outlets": outlets_count,
        "mti_total": mti_total,
        "mti_hot": mti_hot,
        "articles_total": articles_total,
        "articles_mti_cited": articles_mti_cited,
        "matches_total": matches_total,
        "last_updated": last_updated or "Még nem futott",
    }


def main():
    start_time = time.time()

    # Ellenőrzés: A gyűjtési időszak 2026. november 15. 23:59:59-kor zárul
    cutoff_date = datetime(2026, 11, 15, 23, 59, 59)
    if datetime.now() > cutoff_date:
        logger.info("=" * 60)
        logger.info("A megfigyelési időszak (2026. november 9 - 15.) lezárult.")
        logger.info("A pipeline nem végez új scrapinget, az adatbázis zárolva van a leadáshoz.")
        logger.info("=" * 60)
        return

    logger.info("=" * 60)
    logger.info(f"Hírfigyelő Pipeline indítása: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 1. MTI Ingestion
    logger.info("[1/3] MTI Hírek gyűjtése és hot-ablak karbantartása...")
    mti_res = run_mti_collector()

    # 2. Portals Ingestion
    logger.info("[2/3] 15 Hírportál friss cikkeinek begyűjtése...")
    portal_res = run_portal_collector()

    # 3. Matching Engine
    logger.info("[3/4] Hírcsaládok és MTI-átvételek párosítása...")
    match_res = run_matching_engine()

    # 4. Google Sheet Sync / CSV Export
    logger.info("[4/5] Adatok szinkronizálása a Google Sheet / táblázat felé...")
    from src.sync.sheets_sync import sync_to_google_sheet_webhook, export_to_csv_folder
    from config.settings import GOOGLE_SHEET_WEBHOOK_URL

    if GOOGLE_SHEET_WEBHOOK_URL:
        sync_ok = sync_to_google_sheet_webhook(GOOGLE_SHEET_WEBHOOK_URL)
        if sync_ok:
            logger.info("Google Sheet szinkronizáció sikeresen lefutott.")
        else:
            logger.warning("Google Sheet szinkronizáció sikertelen, helyi CSV export készült.")
            export_to_csv_folder()
    else:
        export_to_csv_folder()
        logger.info("Helyi CSV export frissítve a data/sheets_export mappában (Webhook beállításra vár).")

    # 5. Static Dashboard Generation for GitHub Pages
    logger.info("[5/5] Publikus webes dashboard generálása (docs/index.html)...")
    try:
        from src.web.export_static import generate_static_site
        generate_static_site()
        logger.info("Publikus GitHub Pages weboldal sikeresen frissítve.")
    except Exception as e:
        logger.warning(f"Nem sikerült a statikus weboldal generálása: {e}")

    elapsed = time.time() - start_time
    stats = get_pipeline_summary()

    logger.info("=" * 60)
    logger.info(f"Pipeline sikeresen lefutott ({elapsed:.1f} másodperc alatt).")
    logger.info(
        f"Adatbázis aktuális állapota: "
        f"{stats['outlets']} portál | "
        f"{stats['articles_total']} cikk ({stats['articles_mti_cited']} MTI-hivatkozással) | "
        f"{stats['mti_total']} MTI hír ({stats['mti_hot']} aktív hot) | "
        f"{stats['matches_total']} igazolt átvételi párosítás"
    )
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
