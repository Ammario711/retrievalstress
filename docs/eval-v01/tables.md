## C0 closed-book accuracy and C1-s support accuracy

| Model | C0 closed-book | C1-s support (all) |
|---|---|---|
| Qwen2.5-1.5B-Instruct | 72.3 [68.8, 75.8] | 99.6 [99.2, 99.9] |
| SmolLM2-1.7B-Instruct | 77.3 [73.8, 80.5] | 99.8 [99.4, 100.0] |
| Phi-3.5-mini-instruct | 83.0 [79.8, 85.8] | 99.6 [99.2, 99.9] |
| Qwen2.5-7B-Instruct | 77.5 [74.0, 80.8] | 99.4 [99.0, 99.8] |

## C1 counterfactual conflict

Rates in % with 95% bootstrap CI. *Context* = followed the passage; *Own* = answered with the true (memorised) object; *Other* = neither. 'Known' = facts the model answered correctly closed-book.

| Model | Instruction | Swap | Subset | n | Context | Own knowledge | Other | raw 'both' |
|---|---|---|---|---|---|---|---|---|
| Qwen2.5-1.5B-Instruct | faithful | same-type | known | 435 | 96.6 [94.7, 98.2] | 3.0 [1.4, 4.8] | 0.5 [0.0, 1.1] | 2 |
| Qwen2.5-1.5B-Instruct | faithful | same-type | all | 600 | 96.8 [95.3, 98.0] | 2.2 [1.0, 3.3] | 1.0 [0.3, 1.8] | 2 |
| Qwen2.5-1.5B-Instruct | faithful | cross-type | known | 435 | 66.4 [62.1, 70.8] | 17.7 [14.3, 21.4] | 15.9 [12.4, 19.3] | 3 |
| Qwen2.5-1.5B-Instruct | faithful | cross-type | all | 600 | 67.8 [64.2, 71.7] | 13.5 [10.8, 16.2] | 18.7 [15.5, 21.8] | 4 |
| Qwen2.5-1.5B-Instruct | neutral | same-type | known | 435 | 93.3 [90.8, 95.6] | 5.3 [3.4, 7.4] | 1.4 [0.5, 2.5] | 1 |
| Qwen2.5-1.5B-Instruct | neutral | same-type | all | 600 | 94.8 [93.0, 96.5] | 3.8 [2.3, 5.3] | 1.3 [0.5, 2.3] | 1 |
| Qwen2.5-1.5B-Instruct | neutral | cross-type | known | 435 | 42.1 [37.7, 46.7] | 37.0 [32.4, 41.6] | 20.9 [17.2, 24.6] | 5 |
| Qwen2.5-1.5B-Instruct | neutral | cross-type | all | 600 | 45.7 [41.7, 49.8] | 27.7 [24.2, 31.2] | 26.7 [23.2, 30.3] | 5 |
| SmolLM2-1.7B-Instruct | faithful | same-type | known | 466 | 96.1 [94.2, 97.9] | 1.1 [0.2, 2.1] | 2.8 [1.3, 4.5] | 1 |
| SmolLM2-1.7B-Instruct | faithful | same-type | all | 600 | 96.8 [95.3, 98.2] | 0.8 [0.2, 1.7] | 2.3 [1.2, 3.5] | 1 |
| SmolLM2-1.7B-Instruct | faithful | cross-type | known | 466 | 78.3 [74.5, 82.2] | 6.7 [4.5, 8.8] | 15.0 [11.6, 18.5] | 1 |
| SmolLM2-1.7B-Instruct | faithful | cross-type | all | 600 | 78.2 [75.0, 81.3] | 5.3 [3.7, 7.3] | 16.5 [13.5, 19.3] | 1 |
| SmolLM2-1.7B-Instruct | neutral | same-type | known | 466 | 95.5 [93.6, 97.4] | 1.5 [0.4, 2.6] | 3.0 [1.5, 4.5] | 1 |
| SmolLM2-1.7B-Instruct | neutral | same-type | all | 600 | 96.0 [94.3, 97.5] | 1.2 [0.3, 2.2] | 2.8 [1.5, 4.2] | 1 |
| SmolLM2-1.7B-Instruct | neutral | cross-type | known | 466 | 68.5 [64.2, 72.7] | 16.3 [13.1, 19.5] | 15.2 [12.0, 18.7] | 2 |
| SmolLM2-1.7B-Instruct | neutral | cross-type | all | 600 | 70.5 [67.0, 74.2] | 12.7 [10.0, 15.3] | 16.8 [14.0, 19.8] | 2 |
| Phi-3.5-mini-instruct | faithful | same-type | known | 499 | 82.8 [79.4, 86.2] | 16.2 [13.2, 19.6] | 1.0 [0.2, 2.0] | 89 |
| Phi-3.5-mini-instruct | faithful | same-type | all | 600 | 85.3 [82.5, 88.2] | 13.7 [10.8, 16.5] | 1.0 [0.3, 1.8] | 89 |
| Phi-3.5-mini-instruct | faithful | cross-type | known | 499 | 60.1 [55.9, 64.3] | 23.4 [19.6, 26.9] | 16.4 [13.2, 19.8] | 85 |
| Phi-3.5-mini-instruct | faithful | cross-type | all | 600 | 61.2 [56.8, 65.0] | 19.8 [16.7, 23.2] | 19.0 [15.8, 22.2] | 85 |
| Phi-3.5-mini-instruct | neutral | same-type | known | 499 | 72.3 [68.3, 76.2] | 27.7 [23.6, 31.7] | 0.0 [0.0, 0.0] | 143 |
| Phi-3.5-mini-instruct | neutral | same-type | all | 600 | 76.5 [72.8, 79.8] | 23.2 [19.7, 26.5] | 0.3 [0.0, 0.8] | 144 |
| Phi-3.5-mini-instruct | neutral | cross-type | known | 499 | 40.7 [36.5, 45.1] | 47.9 [43.5, 52.1] | 11.4 [8.8, 14.2] | 132 |
| Phi-3.5-mini-instruct | neutral | cross-type | all | 600 | 45.5 [41.5, 49.5] | 40.5 [36.7, 44.5] | 14.0 [11.3, 16.8] | 134 |
| Qwen2.5-7B-Instruct | faithful | same-type | known | 466 | 92.1 [89.5, 94.4] | 5.2 [3.2, 7.3] | 2.8 [1.3, 4.3] | 15 |
| Qwen2.5-7B-Instruct | faithful | same-type | all | 600 | 93.2 [91.2, 95.2] | 4.0 [2.5, 5.7] | 2.8 [1.7, 4.3] | 15 |
| Qwen2.5-7B-Instruct | faithful | cross-type | known | 466 | 65.2 [60.7, 69.5] | 14.8 [11.6, 18.2] | 20.0 [16.3, 23.6] | 24 |
| Qwen2.5-7B-Instruct | faithful | cross-type | all | 600 | 65.5 [61.7, 69.2] | 11.7 [9.3, 14.3] | 22.8 [19.7, 26.0] | 24 |
| Qwen2.5-7B-Instruct | neutral | same-type | known | 466 | 65.5 [60.7, 69.5] | 33.7 [29.2, 38.0] | 0.9 [0.2, 1.7] | 85 |
| Qwen2.5-7B-Instruct | neutral | same-type | all | 600 | 70.8 [67.2, 74.5] | 26.5 [22.8, 30.0] | 2.7 [1.5, 4.0] | 87 |
| Qwen2.5-7B-Instruct | neutral | cross-type | known | 466 | 34.3 [30.0, 38.6] | 52.1 [47.6, 56.7] | 13.5 [10.5, 16.7] | 85 |
| Qwen2.5-7B-Instruct | neutral | cross-type | all | 600 | 40.0 [36.2, 44.2] | 42.0 [38.0, 46.0] | 18.0 [15.0, 21.2] | 88 |

## C2 mixed evidence (one supporting + one conflicting passage)

P(own/true answer wins) by order; difference is paired by fact (bootstrap over facts).

| Model | Support first | Conflict first | Difference (support-first − conflict-first) | Context wins (overall) |
|---|---|---|---|---|
| Qwen2.5-1.5B-Instruct | 83.9 [80.9, 86.8] | 79.9 [76.6, 83.1] | +4.0 [+0.8, +7.4] | 17.7 [15.6, 19.9] |
| SmolLM2-1.7B-Instruct | 78.1 [74.6, 81.3] | 56.4 [52.3, 60.2] | +21.7 [+17.2, +25.9] | 32.0 [29.4, 34.5] |
| Phi-3.5-mini-instruct | 91.6 [89.3, 93.8] | 84.9 [81.9, 87.8] | +6.7 [+3.7, +9.9] | 10.8 [9.1, 12.4] |
| Qwen2.5-7B-Instruct | 93.3 [91.3, 95.3] | 92.1 [89.8, 94.1] | +1.2 [-1.3, +3.7] | 7.2 [5.8, 8.7] |

## C3 distractors: accuracy (gold answer) by k and gold position

| Model | k=2 | k=5 | k=10 | first | middle | last | picked a distractor (overall) |
|---|---|---|---|---|---|---|---|
| Qwen2.5-1.5B-Instruct | 99.8 [99.3, 100.0] | 98.7 [97.4, 99.7] | 98.7 [97.5, 99.7] | 99.3 [98.3, 100.0] | 98.2 [96.9, 99.5] | 99.8 [99.3, 100.0] | 0.5 [0.2, 0.9] |
| SmolLM2-1.7B-Instruct | 94.3 [91.9, 96.4] | 88.7 [85.3, 91.9] | 88.7 [85.4, 91.7] | 95.7 [93.5, 97.6] | 85.8 [82.2, 89.2] | 90.1 [87.1, 93.1] | 5.8 [4.4, 7.1] |
| Phi-3.5-mini-instruct | 99.5 [98.8, 100.0] | 100.0 [100.0, 100.0] | 99.7 [99.2, 100.0] | 99.5 [98.8, 100.0] | 100.0 [100.0, 100.0] | 99.8 [99.3, 100.0] | 0.2 [0.0, 0.4] |
| Qwen2.5-7B-Instruct | 99.8 [99.3, 100.0] | 99.7 [99.2, 100.0] | 99.5 [98.7, 100.0] | 100.0 [100.0, 100.0] | 99.2 [98.2, 100.0] | 99.8 [99.0, 100.0] | 0.2 [0.0, 0.6] |

## C4 multi-hop (faithful instruction)

Plain = chain as in Wikidata; edited = last hop's passage changed. *Propagation* = answered with the edited object.

| Model | Hops | Closed-book | Plain accuracy | Edited: propagated | Edited: own knowledge | Edited: other |
|---|---|---|---|---|---|---|
| Qwen2.5-1.5B-Instruct | 2 | 20.0 [13.3, 26.7] | 100.0 [100.0, 100.0] | 99.3 [98.0, 100.0] | 0.0 [0.0, 0.0] | 0.7 [0.0, 2.0] |
| Qwen2.5-1.5B-Instruct | 3 | 34.7 [26.7, 42.7] | 98.7 [96.7, 100.0] | 57.3 [49.3, 64.7] | 28.0 [21.3, 35.3] | 14.7 [9.3, 20.7] |
| SmolLM2-1.7B-Instruct | 2 | 22.7 [16.0, 30.0] | 97.3 [94.7, 99.3] | 96.7 [93.3, 99.3] | 0.0 [0.0, 0.0] | 3.3 [0.7, 6.7] |
| SmolLM2-1.7B-Instruct | 3 | 40.7 [32.7, 48.7] | 85.3 [79.3, 90.7] | 64.7 [56.7, 72.0] | 2.7 [0.7, 6.0] | 32.7 [24.7, 40.7] |
| Phi-3.5-mini-instruct | 2 | 24.0 [17.3, 31.3] | 99.3 [98.0, 100.0] | 99.3 [98.0, 100.0] | 0.7 [0.0, 2.0] | 0.0 [0.0, 0.0] |
| Phi-3.5-mini-instruct | 3 | 61.3 [53.3, 69.3] | 94.7 [90.7, 98.0] | 40.0 [32.7, 48.0] | 28.0 [20.7, 35.3] | 32.0 [24.7, 39.3] |
| Qwen2.5-7B-Instruct | 2 | 17.3 [12.0, 23.3] | 99.3 [98.0, 100.0] | 98.7 [96.7, 100.0] | 0.0 [0.0, 0.0] | 1.3 [0.0, 3.3] |
| Qwen2.5-7B-Instruct | 3 | 53.3 [45.3, 61.3] | 99.3 [98.0, 100.0] | 28.0 [21.3, 35.3] | 54.7 [46.7, 62.7] | 17.3 [11.3, 24.0] |

## Does prior strength predict override? (C1, known facts, context vs own-knowledge answers only)

Token probabilities / verbalised confidence were **not logged** in this run, so model confidence can't be tested yet. As a proxy for prior strength we use the subject's popularity (Wikipedia sitelinks) and report the AUROC of popularity for predicting *own-knowledge override* (0.5 = no signal). CI: bootstrap over items.

| Model | n | override rate | AUROC (popularity → override) |
|---|---|---|---|
| Qwen2.5-1.5B-Instruct | 1572 | 17.4 | 0.597 [0.553, 0.639] |
| SmolLM2-1.7B-Instruct | 1696 | 7.0 | 0.534 [0.480, 0.590] |
| Phi-3.5-mini-instruct | 1852 | 31.0 | 0.648 [0.622, 0.675] |
| Qwen2.5-7B-Instruct | 1691 | 29.2 | 0.662 [0.633, 0.692] |
