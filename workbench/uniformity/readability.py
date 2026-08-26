#!/usr/bin/env python3
"""Measure how tangled the prose in a skill is.

Usage:
    python3 workbench/uniformity/readability.py skills/generative-media
    python3 workbench/uniformity/readability.py skills/generative-media/krea-2

Prints one row per file, worst first, then the median. See STANDARD.md §6.8a
for what the numbers mean and what counts as a finding.

Only prose is measured. Frontmatter, headings, tables, code blocks and inline
code are stripped out first, because none of those are read as sentences.
"""

import re
import sys
import glob
import statistics


def strip_to_prose(text):
    """Remove everything that is not read as a sentence."""
    text = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.S)   # YAML frontmatter
    text = re.sub(r'```.*?```', '', text, flags=re.S)          # fenced code
    text = re.sub(r'^\s*\|.*$', '', text, flags=re.M)          # table rows
    text = re.sub(r'`[^`]*`', 'thing', text)                   # inline code
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)       # links -> link text
    text = re.sub(r'^\s*#.*$', '', text, flags=re.M)           # headings
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.M)        # bullet markers
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.M)       # numbered markers
    return re.sub(r'[*_>]', '', text)


def measure(path):
    text = strip_to_prose(open(path).read())
    words = text.split()
    if len(words) < 250:
        return None
    sentences = [s for s in re.split(r'(?<=[.!?])[\s"\)]+|\n\n', text)
                 if len(s.split()) > 3]
    per_thousand = 1000 / len(words)
    long_pct = 100 * sum(1 for s in sentences if len(s.split()) > 30) / len(sentences)
    dashes = text.count('—') * per_thousand
    semis = text.count(';') * per_thousand
    return {
        'path': path,
        'words_per_sentence': len(words) / len(sentences),
        'long_pct': long_pct,
        'dashes': dashes,
        'semis': semis,
        # Long sentences dominate. Em-dashes and semicolons are weighted lower
        # because both have legitimate uses; they only signal trouble in bulk.
        'tangle': long_pct + dashes * 0.35 + semis * 0.5,
    }


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else 'skills/generative-media'
    rows = [m for m in (measure(p) for p in sorted(
        glob.glob(target + '/**/*.md', recursive=True))) if m]
    if not rows:
        print('no files over 250 prose words found under', target)
        return 1

    rows.sort(key=lambda r: -r['tangle'])
    print(f"{'tangle':>6} {'w/sent':>7} {'>30w':>6} {'dash/k':>7} {'semi/k':>7}  file")
    for r in rows:
        flag = '  <-- over 15' if r['tangle'] > 15 else ''
        # Show enough path to tell two same-named files apart.
        label = '/'.join(r['path'].split('/')[-3:]).replace('references/', '')
        print(f"{r['tangle']:6.1f} {r['words_per_sentence']:7.1f} "
              f"{r['long_pct']:5.0f}% {r['dashes']:7.1f} {r['semis']:7.1f}  "
              f"{label}{flag}")

    median = statistics.median(r['tangle'] for r in rows)
    over = sum(1 for r in rows if r['tangle'] > 15)
    print(f"\nmedian tangle {median:.1f} across {len(rows)} files; "
          f"{over} over the 15 threshold")
    return 1 if over else 0


if __name__ == '__main__':
    sys.exit(main())
