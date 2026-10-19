# eval.py: compare a model's extraction against my labels
# Run:  python eval.py               (Haiku)
#       python eval.py <model-name>  (any other model)

import sys
import json
import time
import statistics
from pathlib import Path

from rapidfuzz import fuzz

from main import extract_job_description
from cost_log import log_run
from aliases import ALIASES
from config import all_models, Model

THRESHOLDS = {
    "seniority": 0.90,
    "must_haves_recall": 0.80,
    "must_haves_precision": 0.75,
    "stack_recall": 0.80,
}

model = Model[sys.argv[1]] if len(sys.argv) > 1 else Model.ANTHROPIC  # "ANTHROPIC" (text) -> Model.ANTHROPIC
modelId = sys.argv[2] if len(sys.argv) > 2 else "claude-haiku-5-5"  # default model


# ---------- Part 1: how to compare ----------

def norm(name):
    name = name.lower().strip()
    return ALIASES.get(name, name)        # "React.js" -> "react"


def similar(a, b):
    return fuzz.token_set_ratio(a.lower(), b.lower()) >= 70   # 0-100 similarity


def count_found(items, in_list):
    count = 0
    for item in items:
        for x in in_list:
            if similar(item, x):
                count += 1
                break  # Exit the inner loop once a match is found!
    return count

# ---------- Part 2: run every case ----------

scores = {
    "seniority": [],
    "must_haves_recall": [],
    "must_haves_precision": [],
    "stack_recall": [],
}
costs = []
latencies = []
retries = 0

for case in sorted(Path("evals/cases").glob("*.txt")):
    label = json.loads(Path(f"evals/cases_output/{case.stem}.expected.json").read_text())
    output_path = Path(f"model_ouput/{model}/{modelId}_{case.stem}.json") 
    output_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    jd, usage = extract_job_description(case.read_text(), model, modelId, None, None)
    seconds = time.time() - start
    run = log_run(modelId, case.stem, usage["attempts"], usage["input"], usage["output"], seconds)
    output_path.write_text(jd.model_dump_json(indent=2))
    # seniority: same word or not -> 1 or 0
    scores["seniority"].append(1 if jd.seniority == label["seniority"] else 0)

    # must-haves: sentences, so fuzzy match
    scores["must_haves_recall"].append(count_found(label["must_haves"], jd.must_haves) / len(label["must_haves"]))
    scores["must_haves_precision"].append(count_found(jd.must_haves, label["must_haves"]) / len(jd.must_haves))

    # stack: short names, so exact match after aliases
    model_stack = [norm(s) for s in jd.stack]
    found = sum(1 for s in label["stack"] if norm(s) in model_stack)
    scores["stack_recall"].append(found / len(label["stack"]))

    costs.append(run["cost_inr"])
    latencies.append(seconds)
    if usage["attempts"] > 1:
        retries += 1


# ---------- Part 3: report ----------

print(f"\n=== {modelId} ===")

failed = []
for name, values in scores.items():
    average = sum(values) / len(values)
    if average < THRESHOLDS[name]:
        failed.append(name)
    print(f"{name:22} {average:.2f}  (need {THRESHOLDS[name]})")

print(f"avg cost per run       ₹{statistics.mean(costs):.4f}")
print(f"p50 latency            {statistics.median(latencies):.2f}s")
print(f"runs needing a retry   {retries}")

print("\nPASS" if not failed else f"\nFAIL {failed}")
sys.exit(1 if failed else 0)
