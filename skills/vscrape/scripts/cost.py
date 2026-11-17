#!/usr/bin/env python3
"""cost.py - planning calculator: what will extracting N items cost, by route? (Python 3.9+, stdlib only)

  python3 cost.py --items 12000 --in-tokens 650 --out-tokens 150 --prefix-tokens 1500
  python3 cost.py --items 12000 --in-tokens 650 --out-tokens 150 --prefix-tokens 1500 --model sonnet --escalate 0.05

--items          number of pages / records to process
--in-tokens      tokens of NEW text per item (the page itself)
--out-tokens     tokens the model writes per item (the JSON row)
--prefix-tokens  tokens of the stable instruction prefix (codebook, schema, examples) sent with every item
--cached-share   share of items whose prefix is read from the cache (default 0.95)
--model          haiku | sonnet | opus | all (default all)
--escalate       share of items re-run once on the large model (Opus) after the cheap pass (default 0)
A token is roughly three-quarters of an English word. Output is an ESTIMATE for planning, not a quote.
"""
import argparse

# List prices, US dollars per million tokens (input, output). Anthropic first-party API, cached
# September 25, 2026. CHECK THE LIVE PRICING PAGE before you budget: https://platform.claude.com/docs
PRICES = {"haiku": (1.0, 5.0), "sonnet": (2.0, 10.0), "opus": (4.0, 20.0)}
NAMES = {"haiku": "Haiku 4.5", "sonnet": "Sonnet 5.5", "opus": "Opus 5.5"}
CACHE_READ = {"haiku": 0.1, "sonnet": 0.1, "opus": 0.05}  # multiple of the input price
CACHE_WRITE = 1.25  # 5-minute cache, multiple of input price; paid once per cache lifetime (modelled once)
BATCH = 0.5  # Message Batches API: half price on input and output


def route(m, n, i, o, p, share, batch, cache):
    pin, pout = PRICES[m]
    k = BATCH if batch else 1.0
    if cache:
        hit = n * share
        miss = n - hit
        pre = (hit * p * CACHE_READ[m] + miss * p * 1.0 + CACHE_WRITE * p) * pin
    else:
        pre = n * p * pin
    return k * (pre + n * i * pin + n * o * pout) / 1e6


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--items", type=int, required=True)
    ap.add_argument("--in-tokens", type=int, required=True)
    ap.add_argument("--out-tokens", type=int, required=True)
    ap.add_argument("--prefix-tokens", type=int, default=0)
    ap.add_argument("--cached-share", type=float, default=0.95)
    ap.add_argument("--model", default="all", choices=["all", *PRICES])
    ap.add_argument("--escalate", type=float, default=0.0)
    a = ap.parse_args()

    models = list(PRICES) if a.model == "all" else [a.model]
    total_in = a.items * (a.in_tokens + a.prefix_tokens)
    print(f"{a.items:,} items, {a.in_tokens} new + {a.prefix_tokens} prefix tokens in, {a.out_tokens} out each "
          f"(= {total_in / 1e6:.1f} M input tokens, {a.items * a.out_tokens / 1e6:.2f} M output)")
    print(f"prefix cache hit share {a.cached_share:.0%}; prices cached Sept 25, 2026 - check the live page\n")
    print(f"{'model':<12}{'sync, no cache':>16}{'sync + cache':>14}{'batch':>10}{'batch + cache':>15}")
    best = None
    for m in models:
        v = [route(m, a.items, a.in_tokens, a.out_tokens, a.prefix_tokens, a.cached_share, b, c)
             for b, c in ((0, 0), (0, 1), (1, 0), (1, 1))]
        print(f"{NAMES[m]:<12}" + "".join(f"{'$%.2f' % x:>{w}}" for x, w in zip(v, (16, 14, 10, 15))))
        if best is None or v[3] < best[1]:
            best = (m, v[3])
    if a.escalate > 0:
        n2 = round(a.items * a.escalate)
        e = route("opus", n2, a.in_tokens, a.out_tokens, a.prefix_tokens, a.cached_share, 1, 1)
        print(f"\nEscalation: {n2:,} items ({a.escalate:.0%}) re-run on Opus 5.5, batch + cache: +${e:.2f}")
        print(f"Cheap pass ({NAMES[best[0]]}, batch + cache) + escalation: ${best[1] + e:.2f}")
    print("\nPlanning estimate only: ignores retries, cache-write timing, failed calls, and your own time.")
    print("Cache hits inside a batch are best-effort, so treat 'batch + cache' as the optimistic end.")


if __name__ == "__main__":
    main()
