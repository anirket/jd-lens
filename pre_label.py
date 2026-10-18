# Pre labeleing with bigger model and reviewing them
from pathlib import Path
from main import extract_job_description
from cost_log import log_run
import time


CASES_DIR = Path("evals/cases")
OUT_DIR = Path("evals/cases_output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

model = "claude-sonnet-5-5"


for case in sorted(CASES_DIR.glob("*.txt")):
    OUT = OUT_DIR / f"{case.stem}.expected.json"
    if OUT.exists():
        print(f"skip {case.stem}")
        continue
    txt = case.read_text();
    start = time.time()
    jd, usage = extract_job_description(txt, model=model)
    seconds = time.time() - start
    log_run(model, "sarvam_frontend", usage["attempts"], usage["input"], usage["output"], seconds)



    OUT.write_text(jd.model_dump_json(indent=2))
    print("labelled", case.name)
