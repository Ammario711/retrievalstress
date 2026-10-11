"""C2: mixed evidence. One passage supports the true object, one asserts a same-type substitute.

Both orders are generated (support first / conflict first), so order effects can be measured.
The "context_answer" field holds the conflicting object; the label tells which side the model took.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..relations import RELATIONS, fill
from ..schema import Fact, Item
from .common import base_item, fact_rng, passage
from .counterfactual import pick_substitute


def generate(facts: Iterable[Fact], seed: int = 0, instruction: str = "neutral") -> list[Item]:
    facts = list(facts)
    items = []
    for fact in facts:
        rng = fact_rng(seed, "C2", fact)
        rel = RELATIONS[fact.relation]
        sub = pick_substitute(fact, facts, "same-type", rng)
        if sub is None:
            continue
        q = fill(rel["questions"][rng.randrange(len(rel["questions"]))], fact.subject)
        # Use two *different* passage templates so the two documents aren't word-for-word identical.
        t1, t2 = rng.sample(range(len(rel["passages"])), 2) if len(rel["passages"]) > 1 else (0, 0)
        support, conflict = passage(fact, fact.obj, t1), passage(fact, sub, t2)
        for order, ctx in (("support_first", [support, conflict]), ("conflict_first", [conflict, support])):
            items.append(base_item(fact, "C2", order, q, ctx, sub, instruction=instruction, variant=order))
    return items
