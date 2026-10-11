import json

from retrievalstress import wikidata
from retrievalstress.wikidata import chain_facts, facts_from_rows, run_query


def b(**kv):
    """Build a fake SPARQL binding: entity QIDs become URIs, other values literals."""
    entity_keys = ("s", "o", "book", "author", "city", "country", "item")
    out = {}
    for k, v in kv.items():
        val = f"http://www.wikidata.org/entity/{v}" if k in entity_keys else v
        out[k] = {"value": str(val)}
    return out


def test_single_valued_filter_aliases_and_popularity():
    rows = [
        b(s="Q1", sLabel="Freedonia", o="Q10", oLabel="Fredville", sl=50, alias="Fred City"),
        b(s="Q1", sLabel="Freedonia", o="Q10", oLabel="Fredville", sl=50, alias="FV"),
        b(s="Q2", sLabel="Twolang", o="Q20", oLabel="A", sl=10),
        b(s="Q2", sLabel="Twolang", o="Q21", oLabel="B", sl=10),  # multi-valued -> dropped
        b(s="Q3", sLabel="Q3", o="Q30", oLabel="X", sl=5),  # unlabelled subject -> dropped
        b(s="Q4", sLabel="Paren", o="Q40", oLabel="Town (old)", sl=5),  # bracketed label -> dropped
    ]
    facts = facts_from_rows(rows, "capital")
    assert len(facts) == 1
    f = facts[0]
    assert (f.subject, f.obj, f.subject_id, f.popularity) == ("Freedonia", "Fredville", "Q1", 50)
    assert f.obj_aliases == ("FV", "Fred City")


def test_chain_facts_require_unambiguous_hops():
    rows = [
        b(book="Q1", bookLabel="Book One", bsl=40, author="Q2", authorLabel="Ann Author", asl=30,
          city="Q3", cityLabel="Citytown", csl=40, country="Q4", countryLabel="Landia"),
        # Book Two has two authors -> no chain for it.
        b(book="Q5", bookLabel="Book Two", bsl=40, author="Q2", authorLabel="Ann Author", asl=30,
          city="Q3", cityLabel="Citytown", csl=40, country="Q4", countryLabel="Landia"),
        b(book="Q5", bookLabel="Book Two", bsl=40, author="Q6", authorLabel="Bob Writer", asl=30,
          city="Q3", cityLabel="Citytown", csl=40, country="Q4", countryLabel="Landia"),
    ]
    facts, chains = chain_facts(rows)
    assert chains == [("Book One", "Ann Author", "Citytown", "Landia")]
    rels = {(f.relation, f.subject) for f in facts}
    assert ("author", "Book One") in rels and ("author", "Book Two") not in rels
    assert ("place_of_birth", "Ann Author") in rels and ("country", "Citytown") in rels


def test_run_query_uses_cache(tmp_path, monkeypatch):
    calls = []

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"results": {"bindings": [{"x": {"value": "1"}}]}}).encode()

    def fake_urlopen(req, timeout):
        calls.append(req.full_url)
        return FakeResp()

    monkeypatch.setattr(wikidata.urllib.request, "urlopen", fake_urlopen)
    assert run_query("SELECT 1", tmp_path) == [{"x": {"value": "1"}}]
    assert run_query("SELECT 1", tmp_path) == [{"x": {"value": "1"}}]
    assert len(calls) == 1  # second call served from disk


def test_finalize_overrides_and_aliases():
    from retrievalstress.schema import Fact
    from retrievalstress.wikidata import finalize

    f = finalize(Fact("Beijing", "country", "People's Republic of China", "Q956", ("PRC",)))
    assert f.obj == "China" and "People's Republic of China" in f.obj_aliases
    g = finalize(Fact("Animal Farm", "author", "George Orwell", "Q1"))
    assert "Orwell" in g.obj_aliases
    h = finalize(Fact("Kuwait", "capital", "Kuwait City", "Q2", ("Kuwait", "Al Kuwait")))
    assert h.obj_aliases == ("Al Kuwait",)


def test_articles_in_templates():
    from retrievalstress.relations import fill

    assert fill("What is the capital of {s}?", "United Kingdom") == "What is the capital of the United Kingdom?"
    assert fill("{s} is the capital.", "Czech Republic") == "The Czech Republic is the capital."
    assert fill("What is the capital of {s}?", "France") == "What is the capital of France?"
