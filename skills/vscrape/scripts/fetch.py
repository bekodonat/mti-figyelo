#!/usr/bin/env python3
"""fetch.py - polite, resumable page fetcher (Python 3.9+, standard library only).

Reads a text file of URLs (one per line, '#' comments allowed), downloads each page once, keeps the raw
bytes on disk and writes a manifest CSV: url, saved_path, http_status, sha1, fetched_at (UTC).

  python3 fetch.py urls.txt --out data
  python3 fetch.py urls.txt --out data --rate 0.5 --retries 5
  python3 fetch.py urls.txt --out data --resample-404 0.2     # re-probe a sample of recorded 404s

Rules it follows: never re-fetches a URL already on disk; at most one request per --rate seconds per host;
retries 429 / 5xx / network errors with exponential back-off (honours Retry-After); stops cleanly on Ctrl-C
and resumes where it left off. Servers under load sometimes answer fake 404s, so --resample-404 re-checks
a random sample of the recorded 404s before you accept them as real gaps.
"""
import argparse, csv, hashlib, os, random, sys, time, urllib.error, urllib.request
from datetime import datetime, timezone
from urllib.parse import urlparse

FIELDS = ["url", "saved_path", "http_status", "sha1", "fetched_at"]
UA = "Mozilla/5.0 (compatible; research-fetcher/1.0; polite; contact: set --user-agent)"


def load_manifest(path):
    rows = {}
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows[r["url"]] = r  # later rows win
    return rows


def append_row(path, row):
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


class Throttle:
    def __init__(self, gap):
        self.gap, self.last = gap, {}

    def wait(self, host):
        now = time.monotonic()
        due = self.last.get(host, 0) + self.gap
        if due > now:
            time.sleep(due - now)
        self.last[host] = time.monotonic()


def get(url, throttle, retries, timeout, ua):
    """Return (status, body_or_None). Status 0 = gave up on network errors."""
    host = urlparse(url).netloc
    delay = 2.0
    status = 0
    for attempt in range(retries + 1):
        throttle.wait(host)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            status = e.code
            if e.code == 429 or e.code >= 500:
                ra = e.headers.get("Retry-After", "")
                wait = float(ra) if ra.replace(".", "", 1).isdigit() else delay
            else:
                return e.code, None  # 404, 403, 410 ...: no point retrying
        except (urllib.error.URLError, TimeoutError, OSError):
            status, wait = 0, delay
        if attempt < retries:
            print(f"  retry {attempt + 1}/{retries} in {wait:.0f}s ({url})", file=sys.stderr)
            time.sleep(wait)
            delay *= 2
    return status, None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("urls", help="text file, one URL per line")
    ap.add_argument("--out", default="data", help="output directory (default: data)")
    ap.add_argument("--rate", type=float, default=1.0, help="minimum seconds between requests to one host (default 1.0)")
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--timeout", type=float, default=30)
    ap.add_argument("--user-agent", default=UA)
    ap.add_argument("--resample-404", type=float, nargs="?", const=0.2, default=None, metavar="FRACTION",
                    help="re-probe this fraction (default 0.2) of recorded 404s and report how many now succeed")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    raw = os.path.join(a.out, "raw")
    os.makedirs(raw, exist_ok=True)
    mpath = os.path.join(a.out, "manifest.csv")
    man = load_manifest(mpath)
    thr = Throttle(a.rate)

    def fetch_one(url):
        status, body = get(url, thr, a.retries, a.timeout, a.user_agent)
        row = {"url": url, "saved_path": "", "http_status": status, "sha1": "",
               "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        if status == 200 and body is not None:
            sha = hashlib.sha1(body).hexdigest()
            p = os.path.join(raw, hashlib.sha1(url.encode()).hexdigest()[:16] + ".html")
            with open(p, "wb") as f:
                f.write(body)
            row.update(saved_path=p, sha1=sha)
        append_row(mpath, row)
        man[url] = row
        return row

    if a.resample_404 is not None:
        four = [u for u, r in man.items() if str(r["http_status"]) == "404"]
        random.Random(a.seed).shuffle(four)
        k = max(1, round(len(four) * a.resample_404)) if four else 0
        flipped = 0
        for u in four[:k]:
            r = fetch_one(u)
            flipped += str(r["http_status"]) != "404"
        print(f"resample-404: {len(four)} recorded 404s, re-probed {k}, {flipped} now answer differently.")
        if flipped:
            print("  -> some 404s were load-shedding, not real gaps. Re-run with a lower --rate "
                  "and re-fetch the 404 list before recording any gap.")
        return

    urls = [l.strip() for l in open(a.urls, encoding="utf-8") if l.strip() and not l.startswith("#")]
    seen, todo = set(), []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        r = man.get(u)
        if r and str(r["http_status"]) == "200" and os.path.exists(r["saved_path"]):
            continue  # on disk already
        if r and str(r["http_status"]) == "404":
            continue  # recorded; use --resample-404 to re-check
        todo.append(u)
    print(f"{len(seen)} unique URLs, {len(seen) - len(todo)} already done, {len(todo)} to fetch")
    ok = bad = 0
    try:
        for i, u in enumerate(todo, 1):
            r = fetch_one(u)
            if str(r["http_status"]) == "200":
                ok += 1
            else:
                bad += 1
            if i % 25 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)}  ok={ok} not-ok={bad}")
    except KeyboardInterrupt:
        print("interrupted; re-run the same command to resume")
        sys.exit(130)
    print(f"done. ok={ok} not-ok={bad}  manifest: {mpath}")


if __name__ == "__main__":
    main()
