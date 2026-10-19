# jd-lens

Paste a job description. Get back:

1. **Strict JSON**: role, seniority, must-haves, nice-to-haves, stack (a Pydantic schema is the contract).
2. **A fit score against the resume in `resume.json`**, where every "match" has a quote from the resume as evidence.
3. **Tailored resume bullets**: the resume's real bullets rewritten in the job description's wording.

The model is never trusted on its own. The schema forces the shape of the output, and plain Python checks that every quote it gives is really in the resume.

> **The resume in this repo is a fictional dummy** ("Alex Morgan", made-up companies), used so the demo can be public. The pipeline was built and first tested on my real resume; the fit scores below were re-run on the dummy one. To use it for yourself, replace `resume.json` with your own, matching the fields in `resume_validator.py`.

**Status:** the pipeline and eval work locally. It is not deployed yet, so there is no public URL.

## How it works

```
JD text ──► extract_job_description ──► JobDescription (validated, retried by instructor)
                                              │
resume.json (hand-written) ───────────────────┤
                                              ▼
                                   run_fit_report ──► FitReport (matches, bullets, gaps)
                                              │
                                              ▼
                              find_fakes: is every quote really in the resume?
                                              │
                                              ▼
                       score = verified matches / must-haves   (computed in Python)
```

| File | What it does |
|---|---|
| `job_description.py` | Schema for the extracted job description, with rules in each field description |
| `resume.json`, `resume_validator.py` | The resume (a dummy one in this repo), written by hand, loaded through a Pydantic model |
| `main.py` | The model call: instructor + Pydantic validation + retries, for Anthropic and Groq |
| `fit_report.py` | Fit schema, scoring, tailored bullets, and the fake-quote check |
| `eval.py`, `pre_label.py`, `aliases.py` | The extraction eval: labels, fuzzy matching, thresholds |
| `cost_log.py`, `config.py` | Prices per model and the per-run cost log (`runs.jsonl`) |

Design choices that matter:

- **Only one nondeterministic step.** The resume is hand-written JSON, not extracted by a model, so when a score looks wrong there is only one place to look.
- **The score is arithmetic, not the model's opinion.** The model only says matched or not, with evidence. Python counts.
- **A match counts only if its evidence is really in the resume.** Tailored bullets must point at a real source bullet, word for word. A tool that invents experience is worse than no tool.
- **JSON mode, not forced tool calls.** Newer Claude models reject the forced tool call instructor uses by default, so both models run in JSON mode with the same schema.

## Run it

```
pip install -r requirements.txt        # keys in .env: ANTHROPIC_API_KEY, GROQ_API_KEY
python fit_report.py                   # extract + fit score for every job description in evals/cases/
python eval.py ANTHROPIC claude-haiku-5-5
python eval.py GROQ openai/gpt-oss-20b
```

## Finding 1: extraction, two models

Same schema, prompt and JSON mode on 10 real job descriptions. Only the model changes.

| | Claude Haiku 5.5 | gpt-oss-20b (on Groq) |
|---|---|---|
| must_haves recall | 0.90 | 0.84 |
| must_haves precision | 0.93 | 0.90 |
| stack recall | 0.98 | 0.89 |
| seniority accuracy | 1.00 | 1.00 |
| avg cost per run (₹) | 0.0796 | 0.0350 |
| p50 latency | 5.57 s | 11.69 s |
| runs needing a retry | 0 / 10 | 0 / 10 |

Haiku scored 0.90 must-have recall at ₹0.08 a run. gpt-oss-20b scored 0.84 at ₹0.035. That is about 2.3x cheaper for 6 points of recall (9 on stack recall), but it was also about 2x slower here, so the pipeline uses Haiku. Both pass every threshold, and neither needed a retry in 10 runs.

**How the eval works.** Thresholds were written before the first run: seniority 0.90, must_haves recall 0.80, must_haves precision 0.75, stack recall 0.80. `eval.py` exits 1 if any is missed. Scoring is deterministic, with no LLM judge: seniority is an exact match, stack is an exact match after lowercasing and an alias table, and must-haves use `rapidfuzz` (`token_set_ratio >= 70`) because they are sentences that get reworded.

## Finding 2: fit score on the dummy resume (Haiku, 10 job descriptions)

| Job description | Fit | Verified of must-haves |
|---|---|---|
| 03 Sarvam, Frontend Engineer | 83% | 10 / 12 |
| 08 Emergent Labs, Frontend | 53% | 8 / 15 |
| 09 Degreed, Sr Frontend + GenAI | 38% | 5 / 13 |
| 05 Faff, Applied AI (agents) | 30% | 3 / 10 |
| 01 Razorpay, AI Engineer | 25% | 2 / 8 |
| 04 dscout, Applied AI | 14% | 1 / 7 |
| 10 Zimperium, Sr AI (Python) | 11% | 1 / 9 |
| 02 Sarvam, Agent Engineer | 8% | 1 / 13 |
| 06 Level AI, Sr ML | 0% | 0 / 8 |
| 07 Credo AI, Sr AI | 0% | 0 / 10 |

- **The scores follow the resume.** A frontend engineer's resume scores 83% on the frontend role and 0% on the senior ML roles. A low score with an honest gaps list is the tool working, not a bug.
- **Whether the model invented quotes: 0 unverifiable quotes in these 10 final runs** (model-claimed matches equalled verified matches every time). During development, on the original resume, the check did catch one: the model dropped the word "and" from a bullet. A check that rejects a one-word difference is strict on purpose.
- **Cost of one full analysis (extract + fit): about ₹0.23** (₹0.08 + ₹0.16), about 17 seconds end to end, 0 retries in 10 runs.
- **The score is verified-only.** A match counts only if its evidence quote is really in the resume. The report prints both numbers, "model claimed" and "verified", so a gap between them would show up immediately.

## Things that went wrong, and what they taught me

- **My first fuzzy matcher scored recall at 0.60 when the model was fine.** Substring matching missed `2–6` vs `2-6` and reworded sentences. I checked a case by hand, switched to word-overlap and then `rapidfuzz`, and left the thresholds alone.
- **Sending only the resume bullets gave 3 of 12 matches. Sending the whole resume gave 9 of 12** (measured on my original resume, Sarvam frontend role). The model could not see the skills list or the years of experience, so it could not match "React" or "3-6 years". The score looked like a model problem, and it was a prompt problem.
- **`max_tokens=2048` cut the fit report off mid-JSON.** A fit report is about 3,000 to 4,500 output tokens, so `max_tokens` is now a parameter (8192 for the fit report).
- **Opus 5.5 rejected forced tool calls**, which is instructor's default way to get JSON. Switching both models to JSON mode fixed it and kept the comparison fair.
- **Groq had no Llama chat model on my account** (only `prompt-guard` classifiers, which cannot write JSON), so the second model is `gpt-oss-20b`.

## Known limits

- **Only extraction is compared across two models.** The fit score and bullets were run on Haiku only.
- **The evidence check is a substring check.** A very short quote such as `React` passes, because it appears in the resume. It proves the text is real, not that it supports the requirement.
- **Tailored bullets are checked for their source, not their facts.** Python confirms the source bullet is a real one, word for word. It cannot tell if the rewrite adds a number or a tool. Read the rewrites by hand.
- **The score divides by the number of must-haves the model returned,** so a skipped must-have does not count against the candidate. Dividing by the job description's must-have count would be stricter.
- **The must-haves matcher is crude.** It cannot detect two requirements merged into one, and it can miss real paraphrases. The cutoff of 70 was checked by hand on one case.
- **Labels were pre-labelled with Claude Opus 5.5.** If a label is wrong, both models are scored against the same mistake.
- **10 cases, one run per model.** Output varies between runs, so differences of a few points are within noise.
- **Cost uses a fixed rate of ₹88 per USD** and the prices in `config.py`. Check them against the provider pricing pages before trusting the ₹ figures.
- **A public URL would spend my API credit on every call.** Before deploying, the endpoint needs a length limit, a secret key header and a spend cap.

## Cost log

Every model call is appended to `runs.jsonl`: model, case, attempts, input and output tokens summed across all attempts (retries cost money too), ₹ cost and latency.
