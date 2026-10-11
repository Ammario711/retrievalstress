"""Core data types shared by generators and the evaluation harness."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class Fact:
    """One (subject, relation, object) triple, e.g. (France, capital, Paris)."""

    subject: str
    relation: str  # a key in relations.RELATIONS, e.g. "capital"
    obj: str
    subject_id: str = ""  # Wikidata QID if known (used for deterministic splits)
    obj_aliases: tuple[str, ...] = ()
    popularity: int | None = None  # e.g. Wikidata sitelink count


@dataclass
class Item:
    """One benchmark prompt plus everything needed to score the answer."""

    id: str
    category: str  # "C0", "C1", "C1-s", ...
    question: str
    contexts: list[str]
    true_answer: str  # what the world (Wikidata) says
    true_aliases: list[str]
    context_answer: str | None  # what the context says (None if there's no context)
    split: str  # "public" or "private"
    meta: dict = field(default_factory=dict)  # relation, template ids, plausibility, ...

    def to_dict(self) -> dict:
        return asdict(self)


def stable_hash(*parts: str) -> int:
    """Deterministic hash, the same across runs and machines (unlike Python's hash())."""
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:12], 16)


def split_for(subject_key: str, private_fraction: float = 0.2) -> str:
    """Assign a subject to the public or private split by hashing it, so the split is stable."""
    return "private" if (stable_hash("split", subject_key) % 10_000) / 10_000 < private_fraction else "public"
