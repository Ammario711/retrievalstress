"""Helpers shared by the generators."""

from __future__ import annotations

import random

from ..relations import RELATIONS, fill
from ..schema import Fact, Item, split_for, stable_hash


def fact_key(fact: Fact) -> str:
    return fact.subject_id or f"{fact.relation}:{fact.subject}"


def fact_rng(seed: int, category: str, fact: Fact) -> random.Random:
    """RNG seeded by (seed, category, fact), so each fact's items don't depend on the other facts."""
    return random.Random(stable_hash(str(seed), category, fact_key(fact), fact.relation))


def passage(fact: Fact, obj: str, template: int) -> str:
    return fill(RELATIONS[fact.relation]["passages"][template], fact.subject, obj)


def base_item(fact: Fact, category: str, suffix: str, question: str, contexts: list[str], context_answer: str | None,
              private_fraction: float = 0.2, **meta) -> Item:
    key = fact_key(fact)
    return Item(
        id=f"{category}:{key}:{fact.relation}:{suffix}", category=category, question=question, contexts=contexts,
        true_answer=fact.obj, true_aliases=[fact.obj, *fact.obj_aliases], context_answer=context_answer,
        split=split_for(key, private_fraction),
        meta={"relation": fact.relation, "subject": fact.subject, "popularity": fact.popularity, **meta},
    )
