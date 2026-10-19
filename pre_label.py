# Pre labeleing with bigger model and reviewing them
from pathlib import Path
from main import extract_job_description
from cost_log import log_run
import time
import sys
from config import Model


CASES_DIR = Path("evals/cases")
OUT_DIR = Path("evals/cases_output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

model = Model[sys.argv[1]] if len(sys.argv) > 1 else Model.ANTHROPIC  # "ANTHROPIC" (text) -> Model.ANTHROPIC
modelId = sys.argv[2] if len(sys.argv) > 2 else "claude-opus-5-5"  # labels come from the BIG model


for case in sorted(CASES_DIR.glob("*.txt")):
    OUT = OUT_DIR / f"{case.stem}.expected.json"
    if OUT.exists():
        print(f"skip {case.stem}")
        continue
    txt = case.read_text();
    start = time.time()
    jd, usage = extract_job_description(txt, model, modelId, None, None)
    seconds = time.time() - start
    log_run(modelId, case.stem, usage["attempts"], usage["input"], usage["output"], seconds)



    OUT.write_text(jd.model_dump_json(indent=2))
    print("labelled", case.name)
