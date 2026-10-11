"""Evaluation harness: prompt formatting, a model interface, answer classification and metrics.

Any backend that implements ``Model.generate(prompts) -> answers`` can be evaluated.
``HFModel`` (transformers, for Kaggle GPUs) is imported lazily so the core stays light.
"""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Sequence
from typing import Protocol

from .normalize import matches
from .schema import Item

INSTRUCTIONS = {
    "faithful": "Answer the question using only the information in the context. Reply with a short answer only.",
    "neutral": "Answer the question. Reply with a short answer only.",
}


def format_prompt(item: Item) -> list[dict]:
    """Chat messages for an item. Contexts are numbered like retrieved documents."""
    instr = INSTRUCTIONS[item.meta.get("instruction", "neutral")]
    if item.contexts:
        docs = "\n".join(f"[Document {i + 1}] {c}" for i, c in enumerate(item.contexts))
        user = f"Context:\n{docs}\n\nQuestion: {item.question}"
    else:
        user = f"Question: {item.question}"
    return [{"role": "system", "content": instr}, {"role": "user", "content": user}]


class Model(Protocol):
    name: str

    def generate(self, prompts: Sequence[list[dict]]) -> list[str]: ...


class EchoModel:
    """Test double: answers with the context answer, the true answer, or nonsense, by fixed policy."""

    def __init__(self, policy: dict[str, str], name: str = "echo") -> None:
        self.policy = policy  # category -> "context" | "true" | "other"
        self.name = name
        self._items: list[Item] = []

    def bind(self, items: list[Item]) -> None:
        self._items = items

    def generate(self, prompts: Sequence[list[dict]]) -> list[str]:
        out = []
        for it in self._items[: len(prompts)]:
            mode = self.policy.get(it.category, "true")
            out.append({"context": it.context_answer or "", "true": it.true_answer}.get(mode, "I don't know"))
        self._items = self._items[len(prompts):]
        return out


class HFModel:
    """Greedy-decoding Hugging Face chat model (for GPU runs, e.g. on Kaggle)."""

    def __init__(self, model_name: str, max_new_tokens: int = 16, batch_size: int = 16, load_in_4bit: bool = False):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.name = model_name
        self.tok = AutoTokenizer.from_pretrained(model_name, padding_side="left")
        kw: dict = {"torch_dtype": torch.float16, "device_map": "auto"}
        if load_in_4bit:
            from transformers import BitsAndBytesConfig

            kw["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, **kw).eval()
        self.max_new_tokens, self.batch_size = max_new_tokens, batch_size

    def generate(self, prompts: Sequence[list[dict]]) -> list[str]:
        import torch

        outs: list[str] = []
        for i in range(0, len(prompts), self.batch_size):
            texts = [self.tok.apply_chat_template(p, tokenize=False, add_generation_prompt=True)
                     for p in prompts[i : i + self.batch_size]]
            enc = self.tok(texts, return_tensors="pt", padding=True).to(self.model.device)
            with torch.no_grad():
                gen = self.model.generate(**enc, max_new_tokens=self.max_new_tokens, do_sample=False,
                                          pad_token_id=self.tok.pad_token_id or self.tok.eos_token_id)
            outs += self.tok.batch_decode(gen[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)
        return outs


def classify(item: Item, answer: str) -> str:
    """Label an answer as 'context', 'true' (parametric/gold), 'both', 'distractor' (C3), or 'other'."""
    is_true = matches(answer, item.true_aliases)
    distractors = item.meta.get("distractor_objects") or []
    if not is_true and distractors and matches(answer, distractors):
        return "distractor"
    is_ctx = item.context_answer is not None and item.context_answer != item.true_answer and matches(
        answer, [item.context_answer])
    if is_true and is_ctx:
        return "both"
    if is_ctx:
        return "context"
    if is_true:
        return "true"
    return "other"


def run(model: Model, items: list[Item]) -> list[dict]:
    """Generate answers for all items and attach the classification."""
    answers = model.generate([format_prompt(it) for it in items])
    return [{"id": it.id, "category": it.category, "meta": it.meta, "answer": a, "label": classify(it, a)}
            for it, a in zip(items, answers, strict=True)]


def bootstrap_ci(values: list[float], n: int = 1000, seed: int = 0) -> tuple[float, float]:
    """95% percentile bootstrap CI of the mean."""
    if not values:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    means = sorted(sum(rng.choices(values, k=len(values))) / len(values) for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def summarize(records: list[dict], known_only: bool = True) -> dict:
    """C1 metrics, optionally only over facts the model answered correctly closed-book (C0)."""
    known = {r["meta"]["subject"] + "|" + r["meta"]["relation"] for r in records
             if r["category"] == "C0" and r["label"] == "true"}
    out: dict = {"n_closed_book": sum(r["category"] == "C0" for r in records), "n_known": len(known)}
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        if r["category"] == "C0":
            continue
        if known_only and r["meta"]["subject"] + "|" + r["meta"]["relation"] not in known:
            continue
        m = r["meta"]
        groups[(r["category"], m.get("relation") if r["category"] == "C4" else None, m.get("instruction"),
                m.get("plausibility"), m.get("variant"))].append(r)
    for parts, rs in sorted(groups.items(), key=lambda kv: str(kv[0])):
        name = "/".join(str(x) for x in parts if x)
        stats = {"n": len(rs)}
        for lab in ("context", "true", "both", "distractor", "other"):
            vals = [float(r["label"] == lab) for r in rs]
            stats[lab] = sum(vals) / len(vals)
            stats[f"{lab}_ci"] = bootstrap_ci(vals)
        out[name] = stats
    return out
