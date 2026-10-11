from collections import Counter

from retrievalstress.generators import distractors, mixed, multihop
from retrievalstress.harness import classify
from retrievalstress.io import load_facts
from retrievalstress.normalize import matches
from retrievalstress.schema import Fact

FACTS = load_facts()
# A larger synthetic capital set so C3 can draw up to 10 distractors.
CAPS = [Fact(f"Country{i}", "capital", f"City{i}", subject_id=f"Q{i}") for i in range(30)]


def test_c2_both_orders_with_support_and_conflict():
    items = mixed.generate(FACTS)
    assert Counter(it.meta["variant"] for it in items)["support_first"] == Counter(
        it.meta["variant"] for it in items)["conflict_first"]
    for it in items:
        assert len(it.contexts) == 2
        support, conflict = it.contexts if it.meta["variant"] == "support_first" else it.contexts[::-1]
        assert matches(support, it.true_aliases) and it.context_answer in conflict
        assert not matches(conflict, it.true_aliases)
    assert len({it.id for it in items}) == len(items)


def test_c3_gold_position_and_distractors():
    items = distractors.generate(CAPS, configs_per_fact=9)
    assert len(items) == 30 * 9
    for it in items:
        k, pos = it.meta["k"], it.meta["gold_position"]
        assert len(it.contexts) == k + 1
        gold_idx = [i for i, c in enumerate(it.contexts) if matches(c, it.true_aliases)]
        assert gold_idx == [{"first": 0, "middle": k // 2, "last": k}[pos]]
        assert len(it.meta["distractor_objects"]) == k and it.true_answer not in it.meta["distractor_objects"]


def test_c3_skips_configs_without_enough_distractors():
    assert all(len(it.contexts) <= len(CAPS[:4]) for it in distractors.generate(CAPS[:4], configs_per_fact=9))


def test_c3_distractor_label():
    it = distractors.generate(CAPS)[0]
    assert classify(it, it.meta["distractor_objects"][0]) == "distractor"
    assert classify(it, it.true_answer) == "true"


CHAINS = [("Book A", "Ann Author", "Citytown", "Landia"), ("Book B", "Bo Writer", "Villeburg", "Otherland"),
          ("Book C", "Cy Poet", "Hamletton", "Thirdia")]


def test_c4_items_and_edits():
    items = multihop.generate(CHAINS)
    by = Counter((it.category, it.meta["variant"]) for it in items)
    for v in ("2hop/closed", "3hop/closed"):
        assert by[("C0", v)] == 3
    for v in ("2hop/plain", "2hop/edited", "3hop/plain", "3hop/edited"):
        assert by[("C4", v)] == 3
    for it in items:
        if it.category != "C4":
            continue
        assert len(it.contexts) == it.meta["hops"]
        if it.meta["variant"].endswith("plain"):
            assert it.context_answer == it.true_answer and it.true_answer in it.contexts[-1]
        else:
            assert it.context_answer != it.true_answer and it.context_answer in it.contexts[-1]
            assert not any(matches(c, [it.true_answer]) for c in it.contexts[it.meta["hops"] - 1:])
    assert len({it.id for it in items}) == len(items)


def test_generators_deterministic():
    for gen in (lambda s: mixed.generate(FACTS, seed=s), lambda s: distractors.generate(CAPS, seed=s),
                lambda s: multihop.generate(CHAINS, seed=s)):
        assert [i.to_dict() for i in gen(3)] == [i.to_dict() for i in gen(3)]
