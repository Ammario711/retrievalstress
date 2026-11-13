# RetrievalStress

A benchmark of how language models handle **retrieved context that conflicts with what they know**, **contains distractors**, or **needs multi-hop reasoning**. Items are generated programmatically from Wikidata (CC0), so the benchmark can be regenerated and keeps a private split.

> Status: **v0.1 evaluated.** All 7,500 v0.1 items (C0–C4) were run on Kaggle with four models: Qwen2.5-1.5B/7B-Instruct, SmolLM2-1.7B-Instruct and Phi-3.5-mini-instruct. Results: [docs/results.md](docs/results.md). Design: [docs/design.md](docs/design.md).

## Task categories
| ID | Category | Status |
|---|---|---|
| C0 | Closed-book probe (what does the model know?) | ✅ generator |
| C1 | Counterfactual conflict (context contradicts the fact) | ✅ generator |
| C1-s | Support control (context states the fact) | ✅ generator |
| C2 | Mixed evidence (supporting + conflicting passages) | ✅ generator (v0.1) |
| C3 | Distractor passages, varied gold position | ✅ generator (v0.1) |
| C4 | Multi-hop chains, with in-context edits | ✅ generator (v0.1) |

## Results (v0.1)
Headline findings, quoted from [docs/results.md](docs/results.md). Read the caveats there first; full tables with 95% bootstrap CIs are in [docs/eval-v01/tables.md](docs/eval-v01/tables.md).

- **Instruction framing (C1):** For Qwen-7B, the "answer from context" instruction moves context-following on plausible swaps from 65.5% to 92.1%.
- **Order effect (C2):** SmolLM2 has a large primacy effect in mixed evidence: P(true answer wins), support-first minus conflict-first, is +21.7 pts [+17.2, +25.9]. Qwen-7B shows none detectable.
- **Edit propagation (C4):** A 2-hop edit (changing the birthplace) propagates 97–99% of the time for every model. The 3-hop edit (changing a city's country) propagates much less often: from 28.0% (Qwen-7B) to 64.7% (SmolLM2).

## Quickstart
```bash
pip install -e ".[dev]"
pytest -q
retrievalstress-generate --out items.jsonl          # uses the bundled seed facts
```

```python
from retrievalstress.generators.counterfactual import generate
from retrievalstress.harness import HFModel, run, summarize
from retrievalstress.io import load_facts

items = generate(load_facts(), seed=0)
records = run(HFModel("Qwen/Qwen2.5-1.5B-Instruct"), items)   # needs pip install -e ".[hf]" and a GPU
print(summarize(records))   # context-faithfulness / parametric-override rates with 95% CIs
```

## Layout
```
src/retrievalstress/
  schema.py        # Fact, Item, deterministic public/private split
  relations.py     # question + passage templates per relation
  generators/counterfactual.py   # C0 / C1 / C1-s
  harness.py       # prompt format, Model protocol, HF backend, answer classification, metrics + bootstrap CIs
  normalize.py     # answer normalization / matching
  data/seed_facts.jsonl          # 13 hand-checked facts for demos and tests
```

## License
Code: MIT. Generated data is derived from Wikidata (CC0).

## v0.1 dataset

`python scripts/build_dataset.py` fetches facts from Wikidata (SPARQL, cached in `cache/`), samples
100 facts per relation (capital, currency, official language, author, place of birth, country) plus
150 book→author→birthplace→country chains, and generates 7,500 items: C0 900, C1 2,400, C1-s 1,200,
C2 1,200, C3 1,200, C4 600. About 18% of items fall in the hashed private split, which is written only
to `private/` (gitignored). A hand audit of 200 random items found 5.0% serious issues and 11.0% with any
issue: see [docs/audit.md](docs/audit.md).

Evaluation runs on Kaggle (`kaggle/eval_kernel.py`) with Qwen2.5-1.5B/7B-Instruct, SmolLM2-1.7B-Instruct
and Phi-3.5-mini-instruct. Results: [docs/results.md](docs/results.md).
