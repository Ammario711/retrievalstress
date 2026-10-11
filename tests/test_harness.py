from retrievalstress.generators.counterfactual import generate
from retrievalstress.harness import EchoModel, bootstrap_ci, classify, format_prompt, run, summarize
from retrievalstress.io import load_facts

ITEMS = generate(load_facts(), seed=0)


def test_format_prompt():
    c1 = next(it for it in ITEMS if it.category == "C1" and it.meta["instruction"] == "faithful")
    msgs = format_prompt(c1)
    assert msgs[0]["role"] == "system" and "only the information in the context" in msgs[0]["content"]
    assert "[Document 1]" in msgs[1]["content"] and c1.question in msgs[1]["content"]
    c0 = next(it for it in ITEMS if it.category == "C0")
    assert "Context" not in format_prompt(c0)[1]["content"]


def test_classify():
    it = next(i for i in ITEMS if i.category == "C1")
    assert classify(it, f"It's {it.context_answer}.") == "context"
    assert classify(it, it.true_answer) == "true"
    assert classify(it, f"{it.true_answer} or {it.context_answer}") == "both"
    assert classify(it, "no idea") == "other"
    support = next(i for i in ITEMS if i.category == "C1-s")
    assert classify(support, support.true_answer) == "true"  # context == truth is never counted as "context"


def _run(policy):
    model = EchoModel(policy)
    model.bind(ITEMS)
    return run(model, ITEMS)


def test_metrics_for_context_following_model():
    s = summarize(_run({"C0": "true", "C1": "context", "C1-s": "context"}))
    assert s["n_known"] == s["n_closed_book"]
    for name, v in s.items():
        if name.startswith("C1/"):
            assert v["context"] == 1.0 and v["true"] == 0.0
        if name.startswith("C1-s/"):
            assert v["true"] == 1.0


def test_metrics_for_stubborn_model():
    s = summarize(_run({"C0": "true", "C1": "true", "C1-s": "true"}))
    assert all(v["true"] == 1.0 for k, v in s.items() if k.startswith("C1/"))


def test_known_only_filter():
    s = summarize(_run({"C0": "other", "C1": "context"}), known_only=True)
    assert s["n_known"] == 0 and not any(k.startswith("C1") for k in s)
    s_all = summarize(_run({"C0": "other", "C1": "context"}), known_only=False)
    assert any(k.startswith("C1/") for k in s_all)


def test_bootstrap_ci():
    lo, hi = bootstrap_ci([0.0] * 50 + [1.0] * 50)
    assert 0.35 < lo < 0.5 < hi < 0.65
    assert bootstrap_ci([1.0] * 10) == (1.0, 1.0)
