#!/usr/bin/env python3
"""Census the Civitai LoRA ecosystem per base model.

Why this exists
---------------
Two numbers in this skill go stale fastest: how big each base model's LoRA
ecosystem is, and what share of it is adult. Both are measurable directly, so
they should be re-measured rather than believed -- and both have a gotcha that
costs you a wrong answer if you meet it fresh:

  1. The API's `nsfw` boolean is DEAD. It returns false for every model,
     including ones whose previews are XXX. Anything built on it is wrong.

  2. `nsfwLevel` is a BITMASK over a model's preview images, not a scalar:
         1 = PG   2 = PG-13   4 = R   8 = X   16 = XXX
     A model's value ORs together every level present, so `nsfwLevel > 1`
     counts PG-13 as adult and inflates every share badly. Test bits:
     explicit is `level & (8|16)`, mature is `level & (4|8|16)`.

  3. Levels derive from PREVIEW IMAGES, so this UNDERCOUNTS VIDEO. A video
     LoRA's preview is often a tame first frame. Never read the video rows as
     a capability ranking -- see references/adult-work.md.

Usage
-----
  python scripts/civitai_census.py                     # default bases, table
  python scripts/civitai_census.py --adult             # add adult-share columns
  python scripts/civitai_census.py --base "Krea 2" --base Anima
  python scripts/civitai_census.py --tag character     # character-tagged only
  python scripts/civitai_census.py --json out.json
  python scripts/civitai_census.py --pages 22          # deeper; counts are
                                                       # floors until exhausted

Counts marked `+` hit the page cap and are lower bounds. Unmarked counts are
exact -- the cursor was exhausted.

No API key needed. Be polite: there is a delay between pages.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://civitai.red/api/v1/models"
UA = {"User-Agent": "generative-media-atlas/civitai-census (+github.com/ryannel/skills)"}

PG, PG13, R, X, XXX = 1, 2, 4, 8, 16
EXPLICIT = X | XXX
MATURE = R | X | XXX

DEFAULT_BASES = [
    "Pony", "Illustrious", "NoobAI", "SDXL 1.0",
    "Anima", "Krea 2", "ZImageTurbo", "ZImageBase",
    "Flux.1 D", "Flux.2 Klein 9B", "Flux.2 Klein 4B", "Ideogram 4.0", "Qwen",
    "Wan Video 2.2 I2V-A14B", "Wan Video 2.2 T2V-A14B", "Wan Video 2.2 TI2V-5B",
    "MiniMax H3", "LTXV 2.5", "LTXV 2.3", "Hunyuan Video",
]


def fetch(params, retries=3):
    url = API + "?" + urllib.parse.urlencode(params, doseq=True)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if attempt == retries - 1:
                print(f"  ! {e}", file=sys.stderr)
                return None
            time.sleep(1.5 * (attempt + 1))
    return None


def census_base(base, pages, delay, model_type="LORA", tag=None):
    """Return (total, explicit, mature, exhausted)."""
    total = explicit = mature = 0
    cursor, exhausted = None, False
    for _ in range(pages):
        params = {"limit": 100, "types": model_type, "baseModels": base,
                  "sort": "Most Downloaded"}
        if tag:
            params["tag"] = tag
        if cursor:
            params["cursor"] = cursor
        data = fetch(params)
        if data is None:
            break
        for item in data.get("items", []):
            total += 1
            level = item.get("nsfwLevel") or 0
            if level & EXPLICIT:
                explicit += 1
            if level & MATURE:
                mature += 1
        cursor = (data.get("metadata") or {}).get("nextCursor")
        if not cursor:
            exhausted = True
            break
        time.sleep(delay)
    return total, explicit, mature, exhausted


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", action="append", dest="bases",
                    help="base model name; repeatable. Defaults to the suite's set.")
    ap.add_argument("--adult", action="store_true", help="show explicit/mature shares")
    ap.add_argument("--tag", help="restrict to a Civitai tag, e.g. 'character'")
    ap.add_argument("--type", default="LORA", help="model type (LORA, Checkpoint, ...)")
    ap.add_argument("--pages", type=int, default=6, help="max pages of 100 (default 6)")
    ap.add_argument("--delay", type=float, default=0.4, help="seconds between pages")
    ap.add_argument("--json", dest="json_out", help="also write results to this path")
    args = ap.parse_args()

    bases = args.bases or DEFAULT_BASES
    scope = f"type={args.type}" + (f", tag={args.tag}" if args.tag else "")
    print(f"Civitai census - {scope}, up to {args.pages * 100} per base")
    print("`+` = hit the page cap, so a floor. Video rows undercount: levels come "
          "from preview images.\n")

    header = f"{'base':26} {'count':>8}"
    if args.adult:
        header += f" {'explicit':>9} {'mature':>7}"
    print(header)
    print("-" * len(header))

    results = []
    for base in bases:
        total, explicit, mature, exhausted = census_base(
            base, args.pages, args.delay, args.type, args.tag)
        mark = "" if exhausted else "+"
        row = f"{base:26} {str(total) + mark:>8}"
        if args.adult:
            if total:
                row += f" {100.0 * explicit / total:>8.0f}% {100.0 * mature / total:>6.0f}%"
            else:
                row += f" {'-':>9} {'-':>7}"
        print(row)
        results.append({"base": base, "count": total, "exact": exhausted,
                        "explicit": explicit, "mature": mature})

    if args.adult:
        print("\nranked by explicit share (n >= 50):")
        for r in sorted([x for x in results if x["count"] >= 50],
                        key=lambda x: -x["explicit"] / x["count"]):
            print(f"  {100.0 * r['explicit'] / r['count']:>3.0f}%  {r['base']} (n={r['count']})")

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump({"scope": scope, "pages": args.pages, "results": results}, f, indent=2)
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
