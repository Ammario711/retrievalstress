"""C4: multi-hop chains  book -> author -> city of birth (-> country).

For each chain we generate:
  * closed-book versions (category C0, relation multihop2/3) to see what the model knows,
  * a 2-hop item (author passage + birthplace passage) and a 3-hop item (+ country passage),
  * an *edited* version of each, where the last hop's passage states a different city/country.
    A faithful reader must propagate the edit to the final answer.
"""

from __future__ import annotations

import random
from collections.abc import Iterable

from ..normalize import normalize
from ..relations import MULTIHOP_QUESTIONS, fill
from ..schema import Fact, Item, split_for, stable_hash

Chain = tuple[str, str, str, str]  # (book, author, city, country)


def _p_author(book: str, author: str) -> str:
    return f"{book} was written by {author}."


def _p_birth(author: str, city: str) -> str:
    return f"{author} was born in {city}."


def _p_country(city: str, country: str) -> str:
    return fill("{s} is a city in {o}.", city, country)


def _pick(rng: random.Random, pool: list[str], avoid: str) -> str | None:
    cands = sorted(c for c in set(pool) if not set(normalize(c).split()) & set(normalize(avoid).split()))
    return rng.choice(cands) if cands else None


def generate(chains: Iterable[Chain], facts: list[Fact] | None = None, seed: int = 0) -> list[Item]:
    chains = list(chains)
    aliases = {(f.relation, f.obj): list(f.obj_aliases) for f in (facts or [])}
    cities = [c[2] for c in chains]
    countries = [c[3] for c in chains]
    items: list[Item] = []
    for book, author, city, country in chains:
        key = f"chain:{book}"
        rng = random.Random(stable_hash(str(seed), "C4", key))
        split = split_for(key)
        for hops, answer, rel in ((2, city, "place_of_birth"), (3, country, "country")):
            q = fill(rng.choice(MULTIHOP_QUESTIONS[hops]), book)
            true_aliases = [answer, *aliases.get((rel, answer), [])]
            meta = {"relation": f"multihop{hops}", "subject": book, "hops": hops,
                    "chain": [book, author, city, country]}
            shared = {"question": q, "true_answer": answer, "true_aliases": true_aliases, "split": split}
            prefix = f"{key}:{meta['relation']}"

            def item(cat, suffix, contexts, ctx_answer, shared=shared, meta=meta, prefix=prefix, **m):
                return Item(id=f"{cat}:{prefix}:{suffix}", category=cat, contexts=contexts,
                            context_answer=ctx_answer, meta={**meta, **m}, **shared)

            items.append(item("C0", "closed", [], None, variant=f"{hops}hop/closed"))
            ctx = [_p_author(book, author), _p_birth(author, city)]
            if hops == 3:
                ctx.append(_p_country(city, country))
            items.append(item("C4", "plain", list(ctx), answer, variant=f"{hops}hop/plain", instruction="faithful"))
            edited = _pick(rng, cities if hops == 2 else countries, answer)
            if edited is None:
                continue
            ectx = list(ctx)
            ectx[-1] = _p_birth(author, edited) if hops == 2 else _p_country(city, edited)
            items.append(item("C4", "edited", ectx, edited, variant=f"{hops}hop/edited", instruction="faithful"))
    return items
