"""Reading facts and writing items as JSON Lines."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from .schema import Fact, Item


def load_facts(path: str | Path | None = None) -> list[Fact]:
    """Load facts from a JSONL file; defaults to the small bundled seed set (for demos/tests)."""
    if path is None:
        text = resources.files("retrievalstress.data").joinpath("seed_facts.jsonl").read_text()
    else:
        text = Path(path).read_text()
    facts = []
    for line in text.splitlines():
        if line.strip():
            d = json.loads(line)
            d["obj_aliases"] = tuple(d.get("obj_aliases", ()))
            facts.append(Fact(**d))
    return facts


def write_items(items: list[Item], path: str | Path) -> None:
    with open(path, "w") as f:
        for it in items:
            f.write(json.dumps(it.to_dict()) + "\n")


def read_items(path: str | Path) -> list[Item]:
    return [Item(**json.loads(line)) for line in Path(path).read_text().splitlines() if line.strip()]
