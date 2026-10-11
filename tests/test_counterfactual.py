from collections import Counter

import pytest

from retrievalstress.generators.counterfactual import generate, pick_substitute
from retrievalstress.io import load_facts, read_items, write_items
from retrievalstress.normalize import matches, normalize
from retrievalstress.relations import RELATIONS
from retrievalstress.schema import Fact, split_for

FACTS = load_facts()


def test_seed_facts_load_and_use_known_relations():
    assert len(FACTS) >= 10
    assert all(f.relation in RELATIONS for f in FACTS)


def test_item_counts_per_fact():
    items = generate(FACTS, seed=0)
    by_cat = Counter(it.category for it in items)
    assert by_cat["C0"] == len(FACTS)
    assert by_cat["C1-s"] == 2 * len(FACTS)  # two instruction variants
    assert by_cat["C1"] <= 4 * len(FACTS) and by_cat["C1"] > 0


def test_ids_unique():
    items = generate(FACTS)
    assert len({it.id for it in items}) == len(items)


def test_deterministic_and_seed_dependent():
    a = [it.to_dict() for it in generate(FACTS, seed=1)]
    b = [it.to_dict() for it in generate(FACTS, seed=1)]
    c = [it.to_dict() for it in generate(FACTS, seed=2)]
    assert a == b
    assert a != c


def test_items_stable_when_other_facts_are_added():
    """Per-fact RNG: a fact's closed-book/support items don't change when the fact list grows."""
    small = {it.id: it for it in generate(FACTS[:5]) if it.category in ("C0", "C1-s")}
    large = {it.id: it for it in generate(FACTS) if it.id in small}
    assert all(small[k].to_dict() == large[k].to_dict() for k in small)


def test_conflict_context_states_substitute_not_truth():
    for it in generate(FACTS):
        if it.category != "C1":
            continue
        ctx = it.contexts[0]
        assert it.context_answer in ctx
        assert it.context_answer != it.true_answer
        assert not matches(ctx, it.true_aliases), (ctx, it.true_aliases)  # truth never leaks into the context
        assert not matches(it.context_answer, it.true_aliases)


def test_support_context_states_truth():
    for it in generate(FACTS):
        if it.category == "C1-s":
            assert it.context_answer == it.true_answer and it.true_answer in it.contexts[0]


def test_closed_book_has_no_context():
    assert all(not it.contexts and it.context_answer is None for it in generate(FACTS) if it.category == "C0")


def test_plausibility_types():
    import random

    paris = next(f for f in FACTS if f.obj == "Paris")
    same = pick_substitute(paris, FACTS, "same-type", random.Random(0))
    cross = pick_substitute(paris, FACTS, "cross-type", random.Random(0))
    capitals = {f.obj for f in FACTS if f.relation == "capital"}
    assert same in capitals and same != "Paris"
    assert cross not in capitals
    with pytest.raises(ValueError):
        pick_substitute(paris, FACTS, "weird", random.Random(0))


def test_substitute_rejects_alias_and_word_overlap():
    import random

    f = Fact("Canada", "currency", "Canadian dollar", obj_aliases=("dollar",))
    pool = [f, Fact("Australia", "currency", "Australian dollar"), Fact("Japan", "currency", "Japanese yen")]
    assert pick_substitute(f, pool, "same-type", random.Random(0)) == "Japanese yen"
    lonely = Fact("X", "currency", "X dollar")
    assert pick_substitute(lonely, [lonely], "same-type", random.Random(0)) is None


def test_split_is_deterministic_and_roughly_proportional():
    keys = [f"Q{i}" for i in range(5000)]
    frac = sum(split_for(k) == "private" for k in keys) / len(keys)
    assert 0.17 < frac < 0.23
    assert split_for("Q42") == split_for("Q42")
    items = generate(FACTS)
    for key in {it.meta["subject"] for it in items}:
        assert len({it.split for it in items if it.meta["subject"] == key}) == 1  # one split per subject


def test_unknown_relation_rejected():
    with pytest.raises(ValueError):
        generate([Fact("X", "nonexistent", "Y")])


def test_jsonl_roundtrip(tmp_path):
    items = generate(FACTS)
    write_items(items, tmp_path / "items.jsonl")
    assert [i.to_dict() for i in read_items(tmp_path / "items.jsonl")] == [i.to_dict() for i in items]


def test_normalize_and_match():
    assert normalize("The  Japanese Yen!") == "japanese yen"
    assert matches("It is the yen.", ["Japanese yen", "yen"])
    assert not matches("Yenisei", ["yen"])  # whole words only
    assert not matches("anything", [""])
