"""Analyse a Kaggle eval run: tables with 95% bootstrap CIs + plots.

    python scripts/analyze.py runs/eval-v01

'both' answers (mention the true and the context object) are resolved with a simple, audited
heuristic: if the answer explicitly rejects the context ("not X", "X is not", "incorrect", "error")
it counts as the model's own knowledge ('true'), otherwise the first-mentioned answer wins.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from retrievalstress.io import read_items  # noqa: E402
from retrievalstress.normalize import normalize  # noqa: E402

RUN = Path(sys.argv[1] if len(sys.argv) > 1 else "runs/eval-v01")
ITEMS = {i.id: i for i in read_items("private/v0.1/items_all.jsonl")}
MODELS = ["Qwen2.5-1.5B-Instruct", "SmolLM2-1.7B-Instruct", "Phi-3.5-mini-instruct", "Qwen2.5-7B-Instruct"]
REJECT = re.compile(r"\b(incorrect|error|mistake|wrong|inaccurate|not accurate|misinformation)\b", re.I)
rng = np.random.default_rng(0)


def resolve(rec):
    """Final label: context / true / distractor / other ('both' resolved, see module doc)."""
    lab = rec["label"]
    if lab != "both":
        return lab
    it, a = ITEMS[rec["id"]], normalize(rec["answer"])
    ctx = normalize(it.context_answer or "")
    if REJECT.search(rec["answer"]) or re.search(rf"\bnot (the )?{re.escape(ctx)}\b|\b{re.escape(ctx)} (is|was|did|does) not\b", a):
        return "true"
    pos_t = min((a.find(normalize(x)) for x in it.true_aliases if normalize(x) and normalize(x) in a), default=1e9)
    return "true" if pos_t < a.find(ctx) else "context"


def ci(x, n=2000):
    x = np.asarray(x, float)
    if len(x) == 0:
        return (float("nan"),) * 3
    b = rng.choice(x, (n, len(x))).mean(1)
    return float(x.mean()), float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))


def fmt(t):
    return "n/a" if np.isnan(t[0]) else f"{100 * t[0]:.1f} [{100 * t[1]:.1f}, {100 * t[2]:.1f}]"


def auroc(scores, labels):
    s, y = np.asarray(scores, float), np.asarray(labels, int)
    pos, neg = s[y == 1], s[y == 0]
    if not len(pos) or not len(neg):
        return float("nan")
    return float(((pos[:, None] > neg[None]).sum() + 0.5 * (pos[:, None] == neg[None]).sum()) / (len(pos) * len(neg)))


data, known, out = {}, {}, {}
for m in MODELS:
    recs = [json.loads(line) for line in open(RUN / "results" / f"{m}.jsonl")]
    for r in recs:
        r["final"] = resolve(r)
    data[m] = recs
    known[m] = {f"{r['meta']['subject']}|{r['meta']['relation']}" for r in recs if r["category"] == "C0" and r["label"] == "true"}
    assert len(recs) == len(ITEMS), (m, len(recs))


def key(r):
    return f"{r['meta']['subject']}|{r['meta']['relation']}"


lines = []
P = lines.append
# --- C0 / C1 / C1-s
P("## C0 closed-book accuracy and C1-s support accuracy\n\n| Model | C0 closed-book | C1-s support (all) |\n|---|---|---|")
for m in MODELS:
    c0 = [r["label"] == "true" for r in data[m] if r["category"] == "C0" and not r["meta"]["relation"].startswith("multihop")]
    cs = [r["final"] == "true" for r in data[m] if r["category"] == "C1-s"]
    out.setdefault(m, {})["C0"] = ci(c0)
    P(f"| {m} | {fmt(ci(c0))} | {fmt(ci(cs))} |")

P("\n## C1 counterfactual conflict\n\nRates in % with 95% bootstrap CI. *Context* = followed the passage; *Own* = answered with "
  "the true (memorised) object; *Other* = neither. 'Known' = facts the model answered correctly closed-book.\n")
P("| Model | Instruction | Swap | Subset | n | Context | Own knowledge | Other | raw 'both' |\n|---|---|---|---|---|---|---|---|---|")
c1 = {}
for m in MODELS:
    for instr in ("faithful", "neutral"):
        for pl in ("same-type", "cross-type"):
            for subset in ("known", "all"):
                rs = [r for r in data[m] if r["category"] == "C1" and r["meta"]["instruction"] == instr
                      and r["meta"]["plausibility"] == pl and (subset == "all" or key(r) in known[m])]
                st = {lab: ci([r["final"] == lab for r in rs]) for lab in ("context", "true", "other")}
                st["n"] = len(rs)
                c1[(m, instr, pl, subset)] = st
                both = sum(r["label"] == "both" for r in rs)
                P(f"| {m} | {instr} | {pl} | {subset} | {len(rs)} | {fmt(st['context'])} | {fmt(st['true'])} | {fmt(st['other'])} | {both} |")

# --- C2 order effects (paired by fact)
P("\n## C2 mixed evidence (one supporting + one conflicting passage)\n\n"
  "P(own/true answer wins) by order; difference is paired by fact (bootstrap over facts).\n")
P("| Model | Support first | Conflict first | Difference (support-first − conflict-first) | Context wins (overall) |\n|---|---|---|---|---|")
c2 = {}
for m in MODELS:
    by = defaultdict(dict)
    for r in data[m]:
        if r["category"] == "C2":
            by[key(r)][r["meta"]["variant"]] = r["final"] == "true"
    pairs = [(v["support_first"], v["conflict_first"]) for v in by.values() if len(v) == 2]
    a, b = np.array(pairs, float).T
    d = ci(a - b)
    ctxw = ci([r["final"] == "context" for r in data[m] if r["category"] == "C2"])
    c2[m] = (ci(a), ci(b))
    P(f"| {m} | {fmt(ci(a))} | {fmt(ci(b))} | {d[0] * 100:+.1f} [{d[1] * 100:+.1f}, {d[2] * 100:+.1f}] | {fmt(ctxw)} |")

# --- C3 distractors
P("\n## C3 distractors: accuracy (gold answer) by k and gold position\n")
P("| Model | k=2 | k=5 | k=10 | first | middle | last | picked a distractor (overall) |\n|---|---|---|---|---|---|---|---|")
c3 = {}
for m in MODELS:
    rs = [r for r in data[m] if r["category"] == "C3"]
    ks = [ci([r["final"] == "true" for r in rs if r["meta"]["k"] == k]) for k in (2, 5, 10)]
    ps = [ci([r["final"] == "true" for r in rs if r["meta"]["gold_position"] == p]) for p in ("first", "middle", "last")]
    c3[m] = ks
    P(f"| {m} | " + " | ".join(fmt(x) for x in ks + ps) + f" | {fmt(ci([r['final'] == 'distractor' for r in rs]))} |")

# --- C4 multi-hop
P("\n## C4 multi-hop (faithful instruction)\n\nPlain = chain as in Wikidata; edited = last hop's passage changed. "
  "*Propagation* = answered with the edited object.\n")
P("| Model | Hops | Closed-book | Plain accuracy | Edited: propagated | Edited: own knowledge | Edited: other |\n|---|---|---|---|---|---|---|")
c4 = {}
for m in MODELS:
    for h in (2, 3):
        cb = ci([r["label"] == "true" for r in data[m] if r["category"] == "C0" and r["meta"]["relation"] == f"multihop{h}"])
        pl = ci([r["final"] in ("true", "context") for r in data[m] if r["category"] == "C4" and r["meta"]["variant"] == f"{h}hop/plain"])
        ed = [r for r in data[m] if r["category"] == "C4" and r["meta"]["variant"] == f"{h}hop/edited"]
        e = {lab: ci([r["final"] == lab for r in ed]) for lab in ("context", "true", "other")}
        c4[(m, h)] = (pl, e["context"])
        P(f"| {m} | {h} | {fmt(cb)} | {fmt(pl)} | {fmt(e['context'])} | {fmt(e['true'])} | {fmt(e['other'])} |")

# --- RQ5: does popularity predict override?
P("\n## Does prior strength predict override? (C1, known facts, context vs own-knowledge answers only)\n\n"
  "Token probabilities / verbalised confidence were **not logged** in this run, so model confidence can't be tested yet. "
  "As a proxy for prior strength we use the subject's popularity (Wikipedia sitelinks) and report the AUROC of "
  "popularity for predicting *own-knowledge override* (0.5 = no signal). CI: bootstrap over items.\n")
P("| Model | n | override rate | AUROC (popularity → override) |\n|---|---|---|---|")
for m in MODELS:
    rs = [r for r in data[m] if r["category"] == "C1" and key(r) in known[m] and r["final"] in ("true", "context")
          and r["meta"].get("popularity") is not None]
    s = np.array([r["meta"]["popularity"] for r in rs], float)
    y = np.array([r["final"] == "true" for r in rs], int)
    boots = []
    for _ in range(500):
        idx = rng.integers(0, len(rs), len(rs))
        boots.append(auroc(s[idx], y[idx]))
    a = auroc(s, y)
    P(f"| {m} | {len(rs)} | {100 * y.mean():.1f} | {a:.3f} [{np.nanquantile(boots, .025):.3f}, {np.nanquantile(boots, .975):.3f}] |")

(RUN / "tables.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))

# --- plots
figdir = RUN / "plots"
figdir.mkdir(exist_ok=True)
short = [m.replace("-Instruct", "").replace("-instruct", "") for m in MODELS]
fig, axes = plt.subplots(1, 4, figsize=(17, 4.2), sharey=True)
conds = [("faithful", "same-type"), ("faithful", "cross-type"), ("neutral", "same-type"), ("neutral", "cross-type")]
for ax, (instr, pl) in zip(axes, conds, strict=True):
    x = np.arange(len(MODELS))
    bottom = np.zeros(len(MODELS))
    for lab, col in (("context", "tab:red"), ("true", "tab:blue"), ("other", "tab:gray")):
        v = np.array([c1[(m, instr, pl, "known")][lab][0] for m in MODELS])
        lo = np.array([c1[(m, instr, pl, "known")][lab][1] for m in MODELS])
        hi = np.array([c1[(m, instr, pl, "known")][lab][2] for m in MODELS])
        ax.bar(x, v, bottom=bottom, color=col, label={"context": "follows context", "true": "own knowledge", "other": "other"}[lab])
        ax.errorbar(x, bottom + v, yerr=[v - lo, hi - v], fmt="none", ecolor="k", capsize=2, lw=0.8)
        bottom += v
    ax.set_xticks(x, short, rotation=30, ha="right", fontsize=8)
    ax.set_title(f"C1 {instr} / {pl} swap", fontsize=10)
axes[0].set_ylabel("fraction of known-fact items")
axes[0].legend(fontsize=8, loc="lower left")
fig.suptitle("RetrievalStress v0.1: context vs own knowledge under counterfactual passages (known facts, 95% CI)")
fig.tight_layout()
fig.savefig(figdir / "c1_conflict.png", dpi=150)

fig, axs = plt.subplots(1, 3, figsize=(15, 4))
for m, s in zip(MODELS, short, strict=True):
    v = [c3[m][i][0] for i in range(3)]
    e = [[v[i] - c3[m][i][1] for i in range(3)], [c3[m][i][2] - v[i] for i in range(3)]]
    axs[0].errorbar([2, 5, 10], v, yerr=e, marker="o", capsize=3, label=s)
axs[0].set(xlabel="distractor passages k", ylabel="accuracy", title="C3: accuracy vs distractors")
axs[0].legend(fontsize=8)
x = np.arange(len(MODELS))
for j, (lab, off) in enumerate((("support first", -0.2), ("conflict first", 0.2))):
    v = np.array([c2[m][j][0] for m in MODELS])
    lo = np.array([c2[m][j][1] for m in MODELS])
    hi = np.array([c2[m][j][2] for m in MODELS])
    axs[1].bar(x + off, v, 0.4, yerr=[v - lo, hi - v], capsize=3, label=lab)
axs[1].set_xticks(x, short, rotation=20, fontsize=8)
axs[1].set(ylabel="P(true answer wins)", title="C2: mixed evidence, order effect")
axs[1].legend(fontsize=8)
for h, off in ((2, -0.2), (3, 0.2)):
    v = np.array([c4[(m, h)][1][0] for m in MODELS])
    lo = np.array([c4[(m, h)][1][1] for m in MODELS])
    hi = np.array([c4[(m, h)][1][2] for m in MODELS])
    axs[2].bar(x + off, v, 0.4, yerr=[v - lo, hi - v], capsize=3, label=f"{h}-hop")
axs[2].set_xticks(x, short, rotation=20, fontsize=8)
axs[2].set(ylabel="edit propagation rate", title="C4: edited last hop propagated to answer")
axs[2].legend(fontsize=8)
fig.tight_layout()
fig.savefig(figdir / "c2_c3_c4.png", dpi=150)
print("plots:", figdir)
