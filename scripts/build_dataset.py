"""Build a RetrievalStress dataset version from Wikidata.

    python scripts/build_dataset.py --version v0.1 --per-relation 100 --chains 150

Public items go to data/<version>/, private items (hashed ~20% of subjects) to private/<version>/
(gitignored, never published). private/<version>/items_all.jsonl holds everything, for evaluation.
"""

import argparse
import json
import random
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from retrievalstress.generators import counterfactual, distractors, mixed, multihop
from retrievalstress.io import write_items
from retrievalstress.wikidata import fetch_all


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v0.1")
    ap.add_argument("--cache", default="cache")
    ap.add_argument("--per-relation", type=int, default=100)
    ap.add_argument("--chains", type=int, default=150)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    facts, chains = fetch_all(a.cache)
    rng = random.Random(a.seed)
    by_rel: dict[str, list] = {}
    for f in sorted(facts, key=lambda f: (f.relation, f.subject_id)):
        by_rel.setdefault(f.relation, []).append(f)
    sampled = [f for rel in sorted(by_rel) for f in rng.sample(by_rel[rel], min(a.per_relation, len(by_rel[rel])))]
    chains = rng.sample(sorted(chains), min(a.chains, len(chains)))

    items = (counterfactual.generate(sampled, seed=a.seed) + mixed.generate(sampled, seed=a.seed)
             + distractors.generate(sampled, seed=a.seed) + multihop.generate(chains, facts, seed=a.seed))
    pub, priv = Path("data") / a.version, Path("private") / a.version
    pub.mkdir(parents=True, exist_ok=True)
    priv.mkdir(parents=True, exist_ok=True)
    write_items([i for i in items if i.split == "public"], pub / "items_public.jsonl")
    write_items([i for i in items if i.split == "private"], priv / "items_private.jsonl")
    write_items(items, priv / "items_all.jsonl")
    (pub / "facts.jsonl").write_text("".join(json.dumps(asdict(f)) + "\n" for f in sampled))
    (pub / "chains.jsonl").write_text("".join(json.dumps(c) + "\n" for c in chains))
    stats = {"version": a.version, "seed": a.seed, "n_items": len(items), "n_facts": len(sampled), "n_chains": len(chains),
             "by_category": dict(Counter(i.category for i in items)), "by_split": dict(Counter(i.split for i in items)),
             "facts_by_relation": dict(Counter(f.relation for f in sampled))}
    (pub / "stats.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
