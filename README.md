# jd-lens

Paste a job description, get strict JSON (role, seniority, must-haves, stack), a fit score against my resume with quoted evidence, and tailored resume bullets.

## Two-model comparison

Same schema, same prompt, same JSON mode, same 10 job descriptions. Only the model changes.

| | Claude Haiku 5.5 | OpenAI gpt-oss-20b (on Groq) |
|---|---|---|
| must_haves recall | 0.90 | 0.84 |
| must_haves precision | 0.93 | 0.90 |
| stack recall | 0.98 | 0.89 |
| seniority accuracy | 1.00 | 1.00 |
| avg cost per run (₹) | 0.0796 | 0.0350 |
| p50 latency | 5.57 s | 11.69 s |
| runs needing a retry | 0 / 10 | 0 / 10 |

**Result:** Haiku scored 0.90 must-have recall at ₹0.08/run; gpt-oss-20b scored 0.84 at ₹0.035/run. That is about 2.3x cheaper for 6 points of recall (and 9 points on stack recall), but it was about 2x slower here, so the pipeline uses Haiku.

Both models passed all thresholds, with 0 retries in 10 runs each.

## How the eval works

- 10 real job descriptions in `evals/cases/`, labelled in `evals/cases_output/*.expected.json`.
- Run it: `python eval.py ANTHROPIC claude-haiku-5-5` or `python eval.py GROQ openai/gpt-oss-20b`. It exits 1 if any threshold is missed.
- Thresholds were written before the first run: seniority 0.90, must_haves recall 0.80, must_haves precision 0.75, stack recall 0.80.
- Scoring is deterministic, with no LLM judge:
  - **seniority**: exact match.
  - **stack**: exact match after lowercasing and an alias table (`aliases.py`).
  - **must_haves**: fuzzy match with `rapidfuzz` (`token_set_ratio >= 70`). Recall is the share of labelled items the model found. Precision is the share of model items that match a label.

## Known limits

- The must-haves matcher is crude. It counts rewordings, but it cannot tell when the model merged two requirements into one, and real paraphrases can still miss.
- The cutoff of 70 was checked by hand on one case only (case 01).
- Labels were pre-labelled by Claude Opus 5.5, then reviewed. If a label is wrong, both models are scored against the same mistake.
- 10 cases, one run per model. Model output varies between runs, so differences of a few points are within noise.
- Latency for Groq includes network time and can vary by time of day.

## Cost

Every run is appended to `runs.jsonl` (model, tokens across all attempts, ₹ cost, latency). Prices are in `config.py`, USD per million tokens, converted at a fixed `USD_TO_INR` in `cost_log.py`.
