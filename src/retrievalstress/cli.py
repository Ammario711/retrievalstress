"""Command line: generate the C0/C1 dataset.

    retrievalstress-generate --facts facts.jsonl --out items.jsonl [--seed 0]
"""

import argparse
from collections import Counter

from .generators.counterfactual import generate
from .io import load_facts, write_items


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--facts", default=None, help="JSONL of facts (default: bundled seed facts)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    items = generate(load_facts(a.facts), seed=a.seed)
    write_items(items, a.out)
    print(f"wrote {len(items)} items:", dict(Counter((it.category, it.split) for it in items)))


if __name__ == "__main__":
    main()
