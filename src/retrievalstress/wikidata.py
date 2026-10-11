"""Fetch facts from the public Wikidata SPARQL endpoint (all Wikidata data is CC0).

- Every query result is cached on disk (keyed by a hash of the query text), so runs are
  reproducible and the endpoint is hit only once per query.
- Popularity = the subject's number of Wikipedia sitelinks (a cheap proxy for how well known it is).
- Only *single-valued* facts are kept: if a subject has several values for a relation
  (e.g. a country with two official languages), it's dropped, so there's exactly one right answer.
- Splits are assigned later from the subject QID (``schema.split_for``), so they're stable across runs.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

from .schema import Fact

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "RetrievalStress/0.1 (research benchmark; https://github.com/Ammario711)"

# Subject class restrictions per relation. Literary works are limited by sitelinks to keep queries small.
QUERIES = {
    "capital": """
SELECT ?s ?sLabel ?o ?oLabel ?sl ?alias WHERE {
  ?s wdt:P31 wd:Q3624078; wdt:P36 ?o; wikibase:sitelinks ?sl.
  FILTER NOT EXISTS { ?s wdt:P576 [] }
  OPTIONAL { ?o skos:altLabel ?alias. FILTER(LANG(?alias) = "en") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}""",
    "currency": """
SELECT ?s ?sLabel ?o ?oLabel ?sl ?alias WHERE {
  ?s wdt:P31 wd:Q3624078; wdt:P38 ?o; wikibase:sitelinks ?sl.
  FILTER NOT EXISTS { ?s wdt:P576 [] }
  OPTIONAL { ?o skos:altLabel ?alias. FILTER(LANG(?alias) = "en") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}""",
    "official_language": """
SELECT ?s ?sLabel ?o ?oLabel ?sl ?alias WHERE {
  ?s wdt:P31 wd:Q3624078; wdt:P37 ?o; wikibase:sitelinks ?sl.
  FILTER NOT EXISTS { ?s wdt:P576 [] }
  OPTIONAL { ?o skos:altLabel ?alias. FILTER(LANG(?alias) = "en") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}""",
}

# Chains: book -> author -> place of birth -> country. Yields author, place_of_birth and country facts.
CHAIN_QUERY = """
SELECT ?book ?bookLabel ?bsl ?author ?authorLabel ?asl ?city ?cityLabel ?csl ?country ?countryLabel WHERE {
  ?book wdt:P31 wd:Q7725634; wdt:P50 ?author; wikibase:sitelinks ?bsl.
  FILTER(?bsl >= %(min_sitelinks)d)
  ?author wdt:P19 ?city; wikibase:sitelinks ?asl.
  ?city wdt:P17 ?country; wikibase:sitelinks ?csl.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}"""


def run_query(query: str, cache_dir: str | Path, retries: int = 3) -> list[dict]:
    """Run a SPARQL query (or load it from cache) and return the result bindings."""
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"{hashlib.sha256(query.encode()).hexdigest()[:16]}.json"
    if path.exists():
        return json.loads(path.read_text())
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                rows = json.load(resp)["results"]["bindings"]
            path.write_text(json.dumps(rows))
            return rows
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))
    return []


# Common names used instead of formal Wikidata labels (the formal label is kept as an alias).
LABEL_OVERRIDES = {"People's Republic of China": "China"}
# Birthplaces with fewer sitelinks than this are usually villages, parishes or houses ("Ashfield",
# "Östra Ämtervik church parish") rather than the city people would name, so chains through them are dropped.
MIN_CITY_SITELINKS = 25


def _person_aliases(name: str) -> set[str]:
    """Surname alias for a person ("George Orwell" -> "Orwell"), so short answers are matched."""
    parts = name.split()
    return {parts[-1]} if len(parts) >= 2 and len(parts[-1]) >= 4 and parts[-1][0].isupper() else set()


def finalize(fact: Fact) -> Fact:
    """Apply label overrides, add person surname aliases, drop aliases that equal the subject."""
    obj, aliases = fact.obj, set(fact.obj_aliases)
    if obj in LABEL_OVERRIDES:
        aliases.add(obj)
        obj = LABEL_OVERRIDES[obj]
    if fact.relation == "author":
        aliases |= _person_aliases(obj)
    subj = LABEL_OVERRIDES.get(fact.subject, fact.subject)
    aliases = {a for a in aliases if a.lower() not in (subj.lower(), obj.lower(), "the " + subj.lower())}
    return Fact(subj, fact.relation, obj, fact.subject_id, tuple(sorted(aliases)), fact.popularity)


def _qid(binding: dict, key: str) -> str:
    return binding[key]["value"].rsplit("/", 1)[-1]


def _val(binding: dict, key: str) -> str | None:
    return binding[key]["value"] if key in binding else None


def _good_label(label: str | None, qid: str) -> bool:
    """Drop unlabelled entities (label == QID), very long labels and labels with brackets."""
    return bool(label) and label != qid and len(label) <= 40 and not re.search(r"[()\[\]]", label)


def facts_from_rows(rows: list[dict], relation: str) -> list[Fact]:
    """Aggregate (s, o, sitelinks, alias) rows into single-valued Facts."""
    objs: dict[str, set[str]] = defaultdict(set)
    labels: dict[str, str] = {}
    aliases: dict[str, set[str]] = defaultdict(set)
    sitelinks: dict[str, int] = {}
    for b in rows:
        s, o = _qid(b, "s"), _qid(b, "o")
        objs[s].add(o)
        labels[s], labels[o] = _val(b, "sLabel") or s, _val(b, "oLabel") or o
        sitelinks[s] = int(_val(b, "sl") or 0)
        alias = _val(b, "alias")
        if alias and len(alias) <= 40:
            aliases[o].add(alias)
    facts = []
    for s, os_ in sorted(objs.items()):
        if len(os_) != 1:
            continue  # multi-valued: ambiguous gold answer
        (o,) = os_
        if not (_good_label(labels[s], s) and _good_label(labels[o], o)):
            continue
        facts.append(Fact(subject=labels[s], relation=relation, obj=labels[o], subject_id=s,
                          obj_aliases=tuple(sorted(aliases[o] - {labels[o]})), popularity=sitelinks[s]))
    return facts


def chain_facts(rows: list[dict]) -> tuple[list[Fact], list[tuple[str, str, str, str]]]:
    """From chain rows, build author/place_of_birth/country facts and unambiguous chains.

    Returns (facts, chains) where each chain is (book, author, city, country) labels, kept only
    if every hop is single-valued.
    """
    hop = {"author": defaultdict(set), "place_of_birth": defaultdict(set), "country": defaultdict(set)}
    label, pop = {}, {}
    for b in rows:
        bk, au, ci, co = (_qid(b, k) for k in ("book", "author", "city", "country"))
        hop["author"][bk].add(au)
        hop["place_of_birth"][au].add(ci)
        hop["country"][ci].add(co)
        for q, k in ((bk, "bookLabel"), (au, "authorLabel"), (ci, "cityLabel"), (co, "countryLabel")):
            label[q] = _val(b, k) or q
        pop[bk], pop[au], pop[ci] = int(_val(b, "bsl")), int(_val(b, "asl")), int(_val(b, "csl"))
    single = {r: {s: next(iter(o)) for s, o in m.items() if len(o) == 1} for r, m in hop.items()}
    ok = {q for q in label if _good_label(label[q], q)}
    # Drop co-authored "people" like "Ilf and Petrov" and obscure birthplaces (see MIN_CITY_SITELINKS).
    ok -= {q for q in single["place_of_birth"] if re.search(r" and | & ", label[q])}
    ok -= {q for q in single["place_of_birth"].values() if pop.get(q, 0) < MIN_CITY_SITELINKS}
    facts, chains = [], []
    for r, m in single.items():
        for s, o in sorted(m.items()):
            if s in ok and o in ok:
                facts.append(Fact(subject=label[s], relation=r, obj=label[o], subject_id=s, popularity=pop.get(s)))
    for bk, au in sorted(single["author"].items()):
        ci = single["place_of_birth"].get(au)
        co = single["country"].get(ci) if ci else None
        if ci and co and {bk, au, ci, co} <= ok:
            chains.append((label[bk], label[au], label[ci], label[co]))
    return facts, chains


ALIAS_QUERY = """
SELECT ?item ?alias WHERE {
  VALUES ?item { %(values)s }
  ?item skos:altLabel ?alias. FILTER(LANG(?alias) = "en")
}"""


def fetch_aliases(qids: list[str], cache_dir: str | Path, batch: int = 200) -> dict[str, set[str]]:
    """English alternative labels for many entities, in batches (VALUES queries)."""
    out: dict[str, set[str]] = defaultdict(set)
    qids = sorted(set(qids))
    for i in range(0, len(qids), batch):
        values = " ".join(f"wd:{q}" for q in qids[i : i + batch])
        for b in run_query(ALIAS_QUERY % {"values": values}, cache_dir):
            alias = _val(b, "alias")
            if alias and len(alias) <= 40:
                out[_qid(b, "item")].add(alias)
    return out


def fetch_all(
    cache_dir: str | Path, min_book_sitelinks: int = 30
) -> tuple[list[Fact], list[tuple[str, str, str, str]]]:
    """Fetch every relation. Returns (facts, multi-hop chains)."""
    facts: list[Fact] = []
    for rel, q in QUERIES.items():
        facts += facts_from_rows(run_query(q, cache_dir), rel)
    rows = run_query(CHAIN_QUERY % {"min_sitelinks": min_book_sitelinks}, cache_dir)
    cf, chains = chain_facts(rows)
    # Chain objects (authors, cities, countries) need aliases too, e.g. "Conan Doyle", "USA".
    obj_qid = {}
    for b in rows:
        for k in ("author", "city", "country"):
            obj_qid[_val(b, k + "Label")] = _qid(b, k)
    aliases = fetch_aliases(list(obj_qid.values()), cache_dir)
    cf = [Fact(f.subject, f.relation, f.obj, f.subject_id,
               tuple(sorted(aliases.get(obj_qid.get(f.obj, ""), set()) - {f.obj})), f.popularity) for f in cf]
    seen = {(f.subject_id, f.relation) for f in facts}
    facts += [f for f in cf if (f.subject_id, f.relation) not in seen]
    facts = [finalize(f) for f in facts]
    chains = [tuple(LABEL_OVERRIDES.get(x, x) for x in c) for c in chains]
    return facts, chains
