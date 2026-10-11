"""C0 / C1 / C1-s generator: closed-book probes, counterfactual conflicts and support controls.

For each fact (s, r, o) we create:
  C0    question only (measures what the model knows closed-book)
  C1    a passage asserting a substituted object o' != o  (the conflict)
  C1-s  a passage asserting the true object o              (support control)

Substitutes come from other facts:
  same-type   o' is an object of the same relation (plausible: Paris -> Lyon)
  cross-type  o' is an object of a different relation type (implausible: Paris -> euro)

Everything is deterministic given ``seed`` so the dataset can be regenerated exactly.
"""

from __future__ import annotations

import random
from collections.abc import Iterable

from ..normalize import normalize
from ..relations import RELATIONS, fill
from ..schema import Fact, Item, split_for, stable_hash


def _conflicts(candidate: str, fact: Fact) -> bool:
    """A substitute is invalid if it equals the true object/alias or shares a word with it."""
    true_forms = [fact.obj, *fact.obj_aliases]
    cand = normalize(candidate)
    if any(cand == normalize(t) for t in true_forms):
        return True
    cand_words = set(cand.split())
    return any(cand_words & set(normalize(t).split()) for t in true_forms)


def pick_substitute(fact: Fact, facts: list[Fact], plausibility: str, rng: random.Random) -> str | None:
    """Choose a counterfactual object for ``fact``. Returns None if no valid candidate exists."""
    if plausibility == "same-type":
        pool = {f.obj for f in facts if f.relation == fact.relation}
    elif plausibility == "cross-type":
        my_type = RELATIONS[fact.relation]["type"]
        pool = {f.obj for f in facts if RELATIONS[f.relation]["type"] != my_type}
    else:
        raise ValueError(f"unknown plausibility {plausibility!r}")
    candidates = sorted(c for c in pool if not _conflicts(c, fact))
    return rng.choice(candidates) if candidates else None


def generate(
    facts: Iterable[Fact],
    seed: int = 0,
    plausibilities: tuple[str, ...] = ("same-type", "cross-type"),
    instructions: tuple[str, ...] = ("faithful", "neutral"),
    private_fraction: float = 0.2,
) -> list[Item]:
    facts = list(facts)
    for f in facts:
        if f.relation not in RELATIONS:
            raise ValueError(f"unknown relation {f.relation!r}")
    items: list[Item] = []
    for fact in facts:
        rel = RELATIONS[fact.relation]
        key = fact.subject_id or f"{fact.relation}:{fact.subject}"
        # Per-fact RNG seeded from (seed, fact): adding or removing other facts doesn't change this fact's items.
        rng = random.Random(stable_hash(str(seed), key, fact.relation))
        split = split_for(key, private_fraction)
        q_id = rng.randrange(len(rel["questions"]))
        p_id = rng.randrange(len(rel["passages"]))
        question = fill(rel["questions"][q_id], fact.subject)
        aliases = [fact.obj, *fact.obj_aliases]
        base = {"relation": fact.relation, "subject": fact.subject, "question_template": q_id,
                "passage_template": p_id, "popularity": fact.popularity}

        shared = {"question": question, "true_answer": fact.obj, "true_aliases": aliases, "split": split}

        def make(cat: str, contexts: list[str], ctx_answer: str | None, suffix: str, shared=shared, key=key,
                 base=base, **meta) -> Item:
            return Item(id=f"{cat}:{key}:{base['relation']}:{suffix}", category=cat, contexts=contexts,
                        context_answer=ctx_answer,
                        meta={**base, **meta}, **shared)

        items.append(make("C0", [], None, "closed"))
        for instr in instructions:
            support = fill(rel["passages"][p_id], fact.subject, fact.obj)
            items.append(make("C1-s", [support], fact.obj, instr, instruction=instr))
            for plaus in plausibilities:
                sub = pick_substitute(fact, facts, plaus, rng)
                if sub is None:
                    continue
                passage = fill(rel["passages"][p_id], fact.subject, sub)
                items.append(make("C1", [passage], sub, f"{plaus}:{instr}", instruction=instr, plausibility=plaus))
    return items
