import concurrent.futures
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import feedparser
import httpx
import trafilatura
from dateutil import parser as date_parser

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import DEFAULT_HEADERS, REQUEST_TIMEOUT
from src.db.database import get_db, get_active_outlets, get_existing_article_urls

logger = logging.getLogger("portal_collector")

# Comprehensive Hungarian MTI citation patterns
MTI_PATTERNS = [
    re.compile(r"\((?:via\s+)?mti\)", re.IGNORECASE),
    re.compile(r"(?:–|-)\s*mti\b", re.IGNORECASE),
    re.compile(r"forrás:\s*[^,\n\.]*mti\b", re.IGNORECASE),
    re.compile(r"(?:szerző|fotó|forrás|nyitókép|borítókép|kép)\s*:\s*[^,\n\.]*mti\b", re.IGNORECASE),
    re.compile(
        r"(?:közölte|írta|írja|jelentette|tudósított|tájékoztatott|tudatta|számolt be|értesült|fogalmazott|emlékeztet|megjegyzi)\s+(?:az|a)\s+(?:magyar távirati iroda|mti)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:az\s+)?mti\s+(?:híradása|tudósítása|értesülései|jelentése|közleménye|információi|megkeresésére|adatai|szerint)\b",
        re.IGNORECASE,
    ),
    re.compile(r"(?:az\s+)?mti-(?:nek|hez|vel|re|nél)\b", re.IGNORECASE),
    re.compile(r"\bmti\b", re.IGNORECASE),  # Fallback: standalone word MTI
]


def detect_mti_citation(text: str) -> Tuple[bool, Optional[str]]:
    """Detect if article references MTI and extract snippet."""
    if not text:
        return False, None

    for pattern in MTI_PATTERNS:
        match = pattern.search(text)
        if match:
            start = max(0, match.start() - 35)
            end = min(len(text), match.end() + 35)
            excerpt = text[start:end].replace("\n", " ").strip()
            return True, f"...{excerpt}..."

    return False, None


def fetch_rss_feed(rss_url: str) -> List[Dict[str, Any]]:
    """Download and parse an outlet's RSS feed."""
    try:
        response = httpx.get(
            rss_url,
            headers=DEFAULT_HEADERS,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )
        if response.status_code != 200:
            logger.warning(f"Sikertelen RSS lekérés ({response.status_code}): {rss_url}")
            return []

        parsed = feedparser.parse(response.text)
        entries = []
        for entry in parsed.entries:
            link = getattr(entry, "link", None)
            if not link:
                continue

            # Parse published date
            pub_date = None
            if hasattr(entry, "published"):
                try:
                    pub_date = date_parser.parse(entry.published).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
            elif hasattr(entry, "updated"):
                try:
                    pub_date = date_parser.parse(entry.updated).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass

            entries.append({
                "url": link,
                "title_hint": getattr(entry, "title", ""),
                "published_at": pub_date,
            })
        return entries
    except Exception as e:
        logger.error(f"Hiba az RSS feldolgozásakor ({rss_url}): {e}")
        return []


def fetch_and_extract_article(
    outlet_id: int,
    url: str,
    title_hint: str = "",
    published_hint: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Download single article HTML and extract clean text with trafilatura."""
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
        title = (data.get("title") or title_hint or "").strip()
        raw_text = (data.get("raw_text") or "").strip()

        if not title or not raw_text:
            return None

        # Resolve date
        pub_date = published_hint
        if not pub_date and data.get("date"):
            try:
                pub_date = date_parser.parse(data["date"]).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
        if not pub_date:
            pub_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Extract lead
        paragraphs = [p.strip() for p in raw_text.split("\n") if p.strip()]
        lead = paragraphs[0] if paragraphs else title

        # Check for MTI citation
        has_mti, citation_excerpt = detect_mti_citation(raw_text)

        word_count = len(raw_text.split())

        return {
            "outlet_id": outlet_id,
            "url": url,
            "title": title,
            "lead": lead[:500],
            "content_raw": raw_text,
            "published_at": pub_date,
            "has_mti_citation": 1 if has_mti else 0,
            "citation_excerpt": citation_excerpt,
            "word_count": word_count,
        }
    except Exception as e:
        logger.error(f"Hiba a cikk letöltésekor ({url}): {e}")
        return None


def run_portal_collector(max_workers: int = 5) -> Dict[str, Any]:
    """Execute portal news ingestion cycle across all active outlets."""
    logger.info("Portál Cikkgyűjtő futtatása indul...")
    outlets = get_active_outlets()
    logger.info(f"Aktív portálok száma: {len(outlets)}")

    total_discovered = 0
    total_saved = 0
    total_mti_cited = 0

    for outlet in outlets:
        outlet_id = outlet["id"]
        outlet_name = outlet["name"]
        rss_url = outlet["rss_url"]

        feed_items = fetch_rss_feed(rss_url)
        total_discovered += len(feed_items)

        if not feed_items:
            continue

        candidate_urls = [item["url"] for item in feed_items]
        existing_urls = get_existing_article_urls(candidate_urls)
        new_items = [item for item in feed_items if item["url"] not in existing_urls]

        if not new_items:
            continue

        logger.info(f"[{outlet_name}] {len(new_items)} új letöltendő cikk...")

        # Concurrently fetch articles for this outlet
        saved_for_outlet = 0
        mti_for_outlet = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    fetch_and_extract_article,
                    outlet_id,
                    item["url"],
                    item["title_hint"],
                    item["published_at"]
                )
                for item in new_items
            ]

            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Batch insert into database
        valid_results = [r for r in results if r is not None]
        if valid_results:
            with get_db() as conn:
                for article in valid_results:
                    conn.execute(
                        """
                        INSERT INTO articles (
                            outlet_id, url, title, lead, content_raw, published_at, 
                            has_mti_citation, citation_excerpt, word_count
                        )
                        VALUES (
                            :outlet_id, :url, :title, :lead, :content_raw, :published_at, 
                            :has_mti_citation, :citation_excerpt, :word_count
                        )
                        ON CONFLICT(url) DO NOTHING;
                        """,
                        article,
                    )
                    saved_for_outlet += 1
                    if article["has_mti_citation"]:
                        mti_for_outlet += 1

        total_saved += saved_for_outlet
        total_mti_cited += mti_for_outlet
        logger.info(
            f"[{outlet_name}] Sikeresen mentve: {saved_for_outlet} cikk "
            f"(ebből MTI hivatkozás: {mti_for_outlet})"
        )

    logger.info(
        f"Portál Cikkgyűjtő befejezve. Összesen felderítve: {total_discovered}, "
        f"Új cikk mentve: {total_saved}, MTI-t hivatkozó: {total_mti_cited}"
    )

    return {
        "discovered": total_discovered,
        "saved": total_saved,
        "mti_cited": total_mti_cited,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run_portal_collector()
