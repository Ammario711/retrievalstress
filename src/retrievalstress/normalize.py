"""Answer normalization and matching."""

from __future__ import annotations

import re
import string

_ARTICLES = re.compile(r"\b(a|an|the)\b")


def normalize(text: str) -> str:
    """Lower-case, drop punctuation and articles, collapse whitespace (SQuAD-style)."""
    text = text.lower()
    text = "".join(ch for ch in text if ch not in string.punctuation)
    text = _ARTICLES.sub(" ", text)
    return " ".join(text.split())


def matches(prediction: str, answers: list[str]) -> bool:
    """True if any normalized answer appears as a whole-word span in the normalized prediction."""
    pred = f" {normalize(prediction)} "
    return any(f" {normalize(a)} " in pred for a in answers if normalize(a))
