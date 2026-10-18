import json
from datetime import datetime
from config import all_models

PRICES = {
    model_info["modelId"]: model_info["tokens"]
    for vendor_dict in all_models.values()
    for model_info in vendor_dict.values()
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
    return row
