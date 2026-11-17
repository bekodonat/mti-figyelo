import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from dateutil import parser as date_parser
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import SIMILARITY_THRESHOLD
from src.db.database import get_db

logger = logging.getLogger("matching_engine")


def calculate_latency_minutes(mti_pub: str, art_pub: str) -> int:
    """Calculate latency in minutes between MTI publication and outlet publication."""
    try:
        t_mti = date_parser.parse(mti_pub)
        t_art = date_parser.parse(art_pub)
        diff_seconds = (t_art - t_mti).total_seconds()
        return int(diff_seconds / 60)
    except Exception:
        return 0


def run_matching_engine() -> Dict[str, Any]:
    """Match active MTI wire news with newly collected outlet articles using vectorized TF-IDF."""
    logger.info("Matching Engine futtatása indul...")

    with get_db() as conn:
        # 1. Fetch active MTI news
        mti_cursor = conn.execute(
            """
            SELECT id, title, lead, content_raw, published_at, scraped_at 
            FROM mti_news 
            WHERE is_hot = 1 
            ORDER BY published_at DESC
            """
        )
        active_mti_news = mti_cursor.fetchall()

        if not active_mti_news:
            logger.info("Nincs jelenleg aktív ('hot') MTI hír a párosításhoz.")
            return {"active_mti": 0, "matched": 0}

        # 2. Fetch candidate articles
        articles_cursor = conn.execute(
            """
            SELECT a.id, a.outlet_id, a.title, a.lead, a.content_raw, a.published_at, 
                   a.has_mti_citation, o.name as outlet_name
            FROM articles a
            JOIN outlets o ON a.outlet_id = o.id
            LEFT JOIN matches m ON a.id = m.article_id
            WHERE m.id IS NULL
              AND (a.has_mti_citation = 1 OR datetime(a.scraped_at) > datetime('now', '-24 hours'))
            """
        )
        candidate_articles = articles_cursor.fetchall()

        if not candidate_articles:
            logger.info("Nincs párosításra váró cikk.")
            return {"active_mti": len(active_mti_news), "matched": 0}

        logger.info(
            f"Vektorizált párosítás: {len(active_mti_news)} aktív MTI hír x "
            f"{len(candidate_articles)} jelölt cikk..."
        )

        # Build corpus for TF-IDF
        mti_texts = [f"{m['title']} {m['lead'] or ''}" for m in active_mti_news]
        art_texts = [f"{a['title']} {a['lead'] or ''}" for a in candidate_articles]

        # Vectorize all documents in one fast pass
        vectorizer = TfidfVectorizer(max_features=15000, sublinear_tf=True, ngram_range=(1, 2))
        all_tfidf = vectorizer.fit_transform(mti_texts + art_texts)

        mti_tfidf = all_tfidf[:len(mti_texts)]
        art_tfidf = all_tfidf[len(mti_texts):]

        # Pairwise cosine similarity matrix: shape (num_articles, num_mti)
        sim_matrix = cosine_similarity(art_tfidf, mti_tfidf)

        matches_found = 0
        match_records = []

        for i, article in enumerate(candidate_articles):
            row_sims = sim_matrix[i]
            best_mti_idx = int(np.argmax(row_sims))
            best_score = float(row_sims[best_mti_idx])

            matched_mti = active_mti_news[best_mti_idx]
            art_id = article["id"]
            mti_id = matched_mti["id"]

            # Required threshold
            required_threshold = SIMILARITY_THRESHOLD if not article["has_mti_citation"] else 0.40

            if best_score >= required_threshold:
                latency = calculate_latency_minutes(matched_mti["published_at"], article["published_at"])
                match_records.append((mti_id, art_id, round(best_score, 4), latency))
                matches_found += 1
                logger.info(
                    f"Match találat! [{article['outlet_name']}] '{article['title'][:40]}...' "
                    f"<-> MTI: '{matched_mti['title'][:40]}...' (Score: {best_score:.2f}, Latency: {latency}m)"
                )

        if match_records:
            conn.executemany(
                """
                INSERT INTO matches (mti_id, article_id, similarity_score, latency_minutes)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(mti_id, article_id) DO UPDATE SET
                    similarity_score = excluded.similarity_score,
                    latency_minutes = excluded.latency_minutes;
                """,
                match_records,
            )

    logger.info(f"Matching Engine befejezve. Új párosítások száma: {matches_found}")
    return {"active_mti": len(active_mti_news), "matched": matches_found}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run_matching_engine()
