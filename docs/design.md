# RetrievalStress: design

**Status:** design + scaffold. No models have been evaluated yet; this document contains no results.

## 1. Motivation and research questions

Retrieval-augmented generation (RAG) assumes the model will *use* what it retrieves. In practice,
retrieved context can contradict what the model learned in pre-training, can be padded with
plausible but irrelevant passages, or can require combining facts across several passages.
RetrievalStress is a controlled, programmatically generated benchmark for these failure modes,
built to be cheap to regenerate (so it can't simply be memorized) and to run entirely on open models.

- **RQ1 (conflict):** When retrieved context contradicts a fact the model demonstrably knows
  closed-book, how often does the model follow the context vs. its parametric answer? How does this
  depend on the *plausibility* of the substitution, the model's closed-book confidence, and
  the instruction ("answer from the context" vs. "answer correctly")?
- **RQ2 (mixed evidence):** With one supporting and one conflicting passage, does the model show
  order effects or confirmation bias toward its prior (as reported by Xie et al., 2024)?
- **RQ3 (distractors):** How much does accuracy drop as same-type distractor passages are added,
  and does the gold passage's position matter (cf. Liu et al., 2024)?
- **RQ4 (multi-hop):** Given all the needed passages, can models compose 2–3 hops, and does
  a counterfactual edit on one hop propagate to the final answer (cf. MQuAKE)?
- **RQ5 (calibration):** Does verbalized or token-probability confidence predict when the model
  is about to follow wrong context?

## 2. Related work (verified)

| Paper | What it does | How we differ |
|---|---|---|
| Longpre et al., *Entity-Based Knowledge Conflicts in Question Answering*, EMNLP 2021 (arXiv:2109.05052) | Named-entity substitution in NQ/NewsQA passages; finds over-reliance on parametric memory in (older) QA models | We test instruction-tuned LLMs, condition on closed-book knowledge, and vary plausibility |
| Xie et al., *Adaptive Chameleon or Stubborn Sloth*, ICLR 2024 (arXiv:2305.13300) | LLM-generated counter-memory; LLMs are receptive to coherent conflicting evidence but show confirmation bias with mixed evidence | Template-generated (not LLM-generated) contexts, so the conflict is exact and auditable; adds distractors and multi-hop |
| Wu, Wu & Zou, *ClashEval*, NeurIPS 2024 Datasets & Benchmarks (arXiv:2404.10198) | 1,200+ questions in 6 domains with graded perturbations; models adopt wrong context >60% of the time; less confident priors are overridden more | Regenerable from Wikidata with a held-out private split; open models only; explicit multi-hop and distractor axes |
| Chen et al., *Benchmarking LLMs in Retrieval-Augmented Generation* (RGB), AAAI 2024 (arXiv:2309.01431) | Noise robustness, negative rejection, information integration, counterfactual robustness | Controlled entity-level generation lets us condition on what each model knows |
| Shi et al., *LLMs Can Be Easily Distracted by Irrelevant Context*, ICML 2023 (arXiv:2302.00093) | Irrelevant context hurts arithmetic reasoning (GSM-IC) | We study retrieval-style distractors for factual QA |
| Liu et al., *Lost in the Middle*, TACL 2024 (arXiv:2307.03172) | Performance depends on where relevant information sits in long contexts | Gold position is a controlled variable in our distractor category |
| Zhong et al., *MQuAKE*, EMNLP 2023 (arXiv:2305.14795) | Multi-hop questions to test whether knowledge edits propagate | We test propagation of *in-context* (not weight) edits |
| Mallen et al., *When Not to Trust Language Models* (PopQA), ACL 2023 (arXiv:2212.10511) | Parametric knowledge depends strongly on entity popularity; retrieval helps for long-tail entities | We use popularity (Wikipedia page views / sitelinks) as a covariate |
| Xu et al., *Knowledge Conflicts for LLMs: A Survey*, EMNLP 2024 (arXiv:2403.08319) | Taxonomy: context-memory, inter-context, intra-memory conflicts | Our categories map onto context-memory (C1) and inter-context (C2) conflicts |

## 3. Task categories

| ID | Category | Context given | Gold "context-faithful" answer |
|---|---|---|---|
| C0 | Closed-book probe | none | true object (measures parametric knowledge) |
| C1 | Counterfactual conflict | one passage stating a substituted object | substituted object |
| C1-s | Support control | one passage stating the true object | true object |
| C2 | Mixed evidence | one supporting + one conflicting passage (both orders) | none: we measure which one wins, and order effects |
| C3 | Distractors | gold passage + k ∈ {0, 2, 5, 10} same-relation passages about other subjects, gold at varied positions | true (or substituted) object |
| C4 | Multi-hop | 2–3 passages forming a chain (e.g. author → birthplace → country), optionally with one hop edited | answer implied by the passages |

Each C1 item has a **plausibility level**:
- *same-type*: substitute another entity of the same type and relation (Paris → Lyon as the capital of France).
- *cross-type*: substitute an entity of a different type (Paris → "Mount Kenya"). This is implausible on purpose.

Instruction variants: **faithful** ("Answer using only the context") and **neutral** ("Answer the question").

## 4. Dataset construction

- **Source of facts:** Wikidata (all structured data is CC0) via the public SPARQL endpoint. We start with
  single-valued relations that have unambiguous, short answers, such as P36 capital, P38 currency, P19 place of birth,
  P50 author, P112 founded by, P17 country and P37 official language. Each relation has 2–3 question templates
  and 2–3 passage templates, so we can check that results aren't tied to one phrasing.
- **Popularity covariate:** Wikidata sitelink count, which is cheap and needs no extra licence.
- **Substitutes:** sampled from other objects of the same relation (same-type), or from other relations'
  objects (cross-type). Excluded: the true object, its aliases, and anything sharing a token with it.
- **Answer matching:** normalized exact match against Wikidata labels + aliases (lower-case, strip
  articles/punctuation). Fallback is an LLM judge on a small audited sample, used only to estimate matcher error.
- **Existing QA sets (optional):** PopQA (repo MIT-licensed) for popularity-stratified single-hop questions.
  MuSiQue/HotpotQA for natural multi-hop chains, *after* verifying licences. Default is generating everything from Wikidata.
- **Contamination control:** items are generated from a seed. The split is decided by a hash of the subject QID, with
  ~20% kept as a **private split** that is never published. Regenerating with new templates and substitutes is cheap.
- **Validation:** 200 items hand-checked for template fluency and correct gold answers before any results are reported.
- **Size target:** ~2,000 base facts × categories/variants ≈ 15–25k prompts. Closed-book C0 decides which items
  count as "known" for each model.

## 5. Metrics

Per model, computed over items where the model answered C0 correctly ("known facts"), and separately over all items:

- **Context-faithfulness (C1):** fraction answering with the substituted (context) object.
- **Parametric override (C1):** fraction answering with the true (memorized) object despite the context.
- **Other:** neither (abstentions, hallucinations). Reported separately; never folded into either rate.
- **Support accuracy (C1-s):** sanity check; should be ≈100%.
- **Mixed-evidence preference (C2):** P(true object wins) and the order effect (first vs. second position).
- **Distractor robustness (C3):** accuracy vs. k and gold position.
- **Multi-hop accuracy (C4):** with and without an edited hop; *edit propagation rate*.
- **Confidence → behaviour:** AUROC of closed-book answer probability (or verbalized confidence)
  for predicting parametric override.

All rates come with 95% bootstrap confidence intervals over items. Comparisons between models use paired bootstrap.

## 6. Models (free / open only)

No paid APIs without asking first. The plan is to run open-weight instruct models on a Kaggle T4 (16 GB, 30 GPU-h/week),
4-bit quantized where needed:

- Qwen2.5-Instruct 0.5B / 1.5B / 3B / 7B (scaling within a family)
- Llama-3.2-1B/3B-Instruct and Llama-3.1-8B-Instruct (need to accept the Llama licence on Hugging Face)
- Gemma-2-2B/9B-it (Gemma licence)
- Mistral-7B-Instruct-v0.3, Phi-3.5-mini-instruct

Greedy decoding, max 16 new tokens, a fixed system prompt per instruction variant. Optionally, free-tier
hosted APIs as a cross-check, if their terms allow benchmarking.

## 7. Milestones

1. **Scaffold** (this commit): package, C1 generator, harness interface, tests, CI.
2. Wikidata fetcher + popularity; C0/C1/C1-s full generation; 200-item audit.
3. Kaggle eval runner for 3–4 models; first C1 results with CIs.
4. C2 and C3 generators; position and order analyses.
5. C4 multi-hop chains; edit propagation.
6. Write-up, dataset card (public split on HF), leaderboard table.

## 8. Risks

- *Template artifacts:* models might key on phrasing. Mitigation: several templates, with per-template breakdowns.
- *Alias gaps:* exact match under-counts correct answers. Mitigation: an alias expansion plus an audited judge sample to estimate the error.
- *Wikidata errors / ambiguity:* stick to single-valued relations and drop subjects with multiple current values.
- *"Knowing" is model-specific:* always report both the "known-facts" and "all-items" denominators.
