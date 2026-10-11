"""C3: distractor passages. The gold passage (true fact) plus k passages stating true facts about
*other* subjects for the same relation, with the gold passage at a controlled position."""

from __future__ import annotations

from collections.abc import Iterable

from ..normalize import matches
from ..relations import RELATIONS, fill
from ..schema import Fact, Item
from .common import base_item, fact_rng, passage

KS = (2, 5, 10)
POSITIONS = ("first", "middle", "last")


def generate(
    facts: Iterable[Fact], seed: int = 0, configs_per_fact: int = 2, instruction: str = "neutral"
) -> list[Item]:
    facts = list(facts)
    by_rel: dict[str, list[Fact]] = {}
    for f in facts:
        by_rel.setdefault(f.relation, []).append(f)
    items = []
    for fact in facts:
        rng = fact_rng(seed, "C3", fact)
        rel = RELATIONS[fact.relation]
        # Distractors must not mention the true answer (otherwise they'd leak or confuse scoring).
        pool = sorted((f for f in by_rel[fact.relation]
                       if f.subject != fact.subject and not matches(f.obj, [fact.obj, *fact.obj_aliases])
                       and not matches(fact.obj, [f.obj])), key=lambda f: f.subject)
        q = fill(rel["questions"][rng.randrange(len(rel["questions"]))], fact.subject)
        configs = rng.sample([(k, p) for k in KS for p in POSITIONS], configs_per_fact)
        for k, pos in configs:
            if len(pool) < k:
                continue
            others = rng.sample(pool, k)
            docs = [passage(o, o.obj, rng.randrange(len(rel["passages"]))) for o in others]
            gold = passage(fact, fact.obj, rng.randrange(len(rel["passages"])))
            idx = {"first": 0, "middle": k // 2, "last": k}[pos]
            docs.insert(idx, gold)
            items.append(base_item(fact, "C3", f"k{k}:{pos}", q, docs, fact.obj, instruction=instruction,
                                   variant=f"k{k}/{pos}", k=k, gold_position=pos,
                                   distractor_objects=[o.obj for o in others]))
    return items
