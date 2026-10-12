import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
import trafilatura
from dateutil import parser as date_parser

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import (
    MTI_BASE_URL,
    MTI_HOT_WINDOW_HOURS,
    DEFAULT_HEADERS,
    REQUEST_TIMEOUT,
    LOGS_DIR,
)
from src.db.database import get_db, update_mti_hot_status

logger = logging.getLogger("mti_collector")


def get_existing_mti_urls(urls: List[str]) -> set:
    """Check which MTI URLs already exist in the database."""
    if not urls:
        return set()
    with get_db() as conn:
        placeholders = ",".join("?" for _ in urls)
        cursor = conn.execute(
            f"SELECT url FROM mti_news WHERE url IN ({placeholders})",
            urls,
        )
        return {row["url"] for row in cursor.fetchall()}


def discover_mti_article_urls() -> List[str]:
    """Discover fresh article URLs from mti.hu homepage and national press release archive."""
    endpoints = [
        MTI_BASE_URL,
        urljoin(MTI_BASE_URL, "/nemzeti-kozlemenytar"),
    ]
    discovered = []

    with httpx.Client(headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        for url in endpoints:
            try:
                response = client.get(url)
                if response.status_code != 200:
                    logger.warning(f"MTI végpont nem elérhető ({response.status_code}): {url}")
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"]
                    if href.startswith("/hirek/") or href.startswith("/nemzeti-kozlemenytar/"):
                        # Exclude root category links
                        parts = href.strip("/").split("/")
                        if len(parts) >= 3:  # e.g., hirek/2026/10/11/title
                            full_url = urljoin(MTI_BASE_URL, href)
                            if full_url not in discovered:
                                discovered.append(full_url)
            except Exception as e:
                logger.error(f"Hiba az MTI URL-ek felderítésekor ({url}): {e}")

    return discovered


def fetch_and_parse_mti_article(url: str) -> Optional[Dict[str, Any]]:
    """Fetch MTI article and extract clean metadata and content using trafilatura."""
    try:
        html = trafilatura.fetch_url(url)
        if not html:
            return None

        extracted = trafilatura.extract(
            html,
            output_format="json",
            with_metadata=True,
            include_comments=False,
            include_tables=False,
        )
        if not extracted:
            return None

        data = json.loads(extracted)
        title = (data.get("title") or "").strip()
        raw_text = (data.get("raw_text") or "").strip()

        if not title or not raw_text:
            return None

        # Determine published date
        raw_date = data.get("date")
        if raw_date:
            try:
                pub_date = date_parser.parse(raw_date).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pub_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            pub_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create a stable guid
        guid = hashlib.sha256(url.encode("utf-8")).hexdigest()

        # Generate lead: first 2-3 sentences or first paragraph
        paragraphs = [p.strip() for p in raw_text.split("\n") if p.strip()]
        lead = paragraphs[0] if paragraphs else title

        word_count = len(raw_text.split())

        return {
            "guid": guid,
            "url": url,
            "title": title,
            "lead": lead[:500],
            "content_raw": raw_text,
            "published_at": pub_date,
            "is_hot": 1,
            "word_count": word_count,
        }
    except Exception as e:
        logger.error(f"Hiba a cikk letöltésekor ({url}): {e}")
        return None


def run_mti_collector() -> Dict[str, int]:
    """Execute MTI news ingestion cycle."""
    logger.info("MTI Collector futtatása indul...")
    
    # 1. Update hot status on existing news
    expired_count = update_mti_hot_status(hot_window_hours=MTI_HOT_WINDOW_HOURS)
    if expired_count > 0:
        logger.info(f"{expired_count} korábbi MTI hír lezárva (12 óránál régebbi, már nem 'hot').")

    # 2. Discover URLs
    all_urls = discover_mti_article_urls()
    logger.info(f"Felfedezett MTI cikk URL-ek száma: {len(all_urls)}")

    if not all_urls:
        return {"discovered": 0, "saved": 0, "expired": expired_count}

    # 3. Deduplicate
    existing_urls = get_existing_mti_urls(all_urls)
    new_urls = [u for u in all_urls if u not in existing_urls]
    logger.info(f"Új MTI cikkek száma: {len(new_urls)}")

    # 4. Fetch and insert
    saved_count = 0
    with get_db() as conn:
        for url in new_urls:
            article_data = fetch_and_parse_mti_article(url)
            if not article_data:
                continue

            conn.execute(
                """
                INSERT INTO mti_news (guid, url, title, lead, content_raw, published_at, is_hot, word_count)
                VALUES (:guid, :url, :title, :lead, :content_raw, :published_at, :is_hot, :word_count)
                ON CONFLICT(guid) DO NOTHING;
                """,
                article_data,
            )
            saved_count += 1
            logger.info(f"Új MTI hír rögzítve: {article_data['title'][:60]}...")

    logger.info(f"MTI Collector kész. Mentve: {saved_count}, Lejárt: {expired_count}")
    return {"discovered": len(all_urls), "saved": saved_count, "expired": expired_count}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run_mti_collector()
