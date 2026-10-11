# RetrievalStress

A benchmark of how language models handle **retrieved context that conflicts with what they know**, **contains distractors**, or **needs multi-hop reasoning**. Items are generated programmatically from Wikidata (CC0), so the benchmark can be regenerated and keeps a private split.

> Status: **design + scaffold.** The counterfactual-conflict generator (C0/C1/C1-s) and the evaluation harness interface are implemented and tested on a small bundled seed set. No models have been evaluated yet. See [docs/design.md](docs/design.md).

## Task categories
| ID | Category | Status |
|---|---|---|
| C0 | Closed-book probe (what does the model know?) | ✅ generator |
| C1 | Counterfactual conflict (context contradicts the fact) | ✅ generator |
| C1-s | Support control (context states the fact) | ✅ generator |
| C2 | Mixed evidence (supporting + conflicting passages) | planned |
| C3 | Distractor passages, varied gold position | planned |
| C4 | Multi-hop chains, with in-context edits | planned |

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
