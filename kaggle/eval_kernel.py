"""Kaggle GPU kernel: evaluate open models on RetrievalStress v0.1, saving results incrementally.

Inputs (private Kaggle dataset ammararshad711/retrievalstress-v01):
  retrievalstress-src.tar.gz  the package source
  items_all.jsonl             all v0.1 items (public + private split)
Outputs in /kaggle/working/results/: <model>.jsonl (one record per item, appended in chunks so a
crash or timeout keeps finished work), <model>.summary.json, and progress.log.
"""

import gc
import glob
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time

INPUT = (glob.glob("/kaggle/input/*retrievalstress*") + glob.glob("/kaggle/input/datasets/*/*retrievalstress*"))[0]
WORK = "/kaggle/working"
OUT = f"{WORK}/results"
os.makedirs(OUT, exist_ok=True)

# Kaggle auto-extracts uploaded archives into a folder; handle both the folder and the raw tarball.
if os.path.isdir(f"{INPUT}/retrievalstress-src"):
    shutil.copytree(f"{INPUT}/retrievalstress-src", f"{WORK}/src", dirs_exist_ok=True)
else:
    with tarfile.open(f"{INPUT}/retrievalstress-src.tar.gz") as t:
        t.extractall(f"{WORK}/src")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-e", f"{WORK}/src", "bitsandbytes", "accelerate"],
               check=True)
sys.path.insert(0, f"{WORK}/src/src")

import torch  # noqa: E402

from retrievalstress.harness import HFModel, classify, format_prompt, summarize  # noqa: E402
from retrievalstress.io import read_items  # noqa: E402

MODELS = [  # (hf id, 4-bit?, batch size)
    ("Qwen/Qwen2.5-1.5B-Instruct", False, 48),
    ("HuggingFaceTB/SmolLM2-1.7B-Instruct", False, 48),
    ("microsoft/Phi-3.5-mini-instruct", False, 24),
    ("Qwen/Qwen2.5-7B-Instruct", True, 24),
]
CHUNK = 480


def log(msg: str) -> None:
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(f"{OUT}/progress.log", "a") as f:
        f.write(line + "\n")


items = read_items(glob.glob(f"{INPUT}/**/items_all.jsonl", recursive=True)[0])
# Sort by prompt length so batches have similar lengths (less padding, faster).
items.sort(key=lambda it: sum(len(c) for c in it.contexts) + len(it.question))
log(f"{len(items)} items, GPU={torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none'}")

for name, four_bit, bs in MODELS:
    tag = name.split("/")[-1]
    path = f"{OUT}/{tag}.jsonl"
    done = set()
    if os.path.exists(path):
        done = {json.loads(line)["id"] for line in open(path)}
    todo = [it for it in items if it.id not in done]
    if not todo:
        continue
    t0 = time.time()
    try:
        model = HFModel(name, max_new_tokens=24, batch_size=bs, load_in_4bit=four_bit)
    except Exception as e:  # e.g. download failure: skip, keep going with the others
        log(f"{tag}: load failed: {e!r}")
        continue
    log(f"{tag}: loaded in {time.time() - t0:.0f}s, {len(todo)} items to do")
    for i in range(0, len(todo), CHUNK):
        chunk = todo[i : i + CHUNK]
        answers = model.generate([format_prompt(it) for it in chunk])
        with open(path, "a") as f:
            for it, a in zip(chunk, answers, strict=True):
                f.write(json.dumps({"id": it.id, "category": it.category, "split": it.split, "meta": it.meta,
                                    "answer": a, "label": classify(it, a)}) + "\n")
        log(f"{tag}: {min(i + CHUNK, len(todo))}/{len(todo)} ({time.time() - t0:.0f}s)")
    recs = [json.loads(line) for line in open(path)]
    summary = {"model": name, "4bit": four_bit, "n": len(recs),
               "known_only": summarize(recs, known_only=True), "all_items": summarize(recs, known_only=False)}
    json.dump(summary, open(f"{OUT}/{tag}.summary.json", "w"), indent=1)
    log(f"{tag}: done in {time.time() - t0:.0f}s")
    del model
    gc.collect()
    torch.cuda.empty_cache()

log("all done")
