import json
from datetime import datetime

# USD per 1 million tokens
PRICES = {
    "claude-haiku-5-5": {"in": 0.10, "out": 0.50},
}
USD_TO_INR = 88.0  # TODO: today's rate + date


def log_run(model, case_id, attempts, input_tokens, output_tokens, seconds):
    price = PRICES[model]
    cost_usd = (input_tokens * price["in"] + output_tokens * price["out"]) / 1_000_000

    row = {
        "time": datetime.now().isoformat(),
        "model": model,
        "case_id": case_id,
        "attempts": attempts,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_inr": cost_usd * USD_TO_INR,
        "seconds": seconds,
    }

    # "a" = append one line, keep old lines
    with open("runs.jsonl", "a") as f:
        f.write(json.dumps(row) + "\n")

    print(row)
