from pydantic import BaseModel, Field
from main import extract_job_description
import time
from cost_log import log_run
import sys
from pathlib import Path
from config import Model
from resume_validator import load_resume

class RequirementMatch(BaseModel):
    requirment: str = Field(..., description="This line is from evaluation run on JD and copied from JD.must_have")
    matched: bool = Field(..., description="Does the requirment match True or False with resume. true only if the resume honestly shows this")
    evidence: str | None = Field(None, description="Exact evidence copied word for word from resume that matches requirment. None if not matched")

class TailoredBullet(BaseModel):
    jd_requirment: str = Field(..., description="This line is copied from evaluation run on JD")
    source_bullet: str = Field(..., description="Exact line and letter by letter from my resume bullet, Never paraphrase")
    rewritten: str = Field(..., description="Same facts as source_bullet. Use the job description's wording. Don't add numbers, tools or results that aren't in source_bullet. Tailored Rewritten source bullet in my resume to make it more valuable and in line with JD parsed to increase chances of getting shortlisted")

class FitReport(BaseModel):
    matches: list[RequirementMatch]
    bullets: list[TailoredBullet]
    gaps: list[str] = Field(..., description="must haves with no honest match")

 
def find_fakes(fit_report, resume):
    """Return the quotes the model gave that are NOT really in the resume."""
    resume_text = resume.model_dump_json()
    bullets = [b for job in resume.jobs for b in job.bullets]

    fakes = []
    for m in fit_report.matches:
        if m.matched and (m.evidence is None or m.evidence not in resume_text):
            fakes.append(str(m.evidence))
    for b in fit_report.bullets:
        if b.source_bullet not in bullets:
            fakes.append(b.source_bullet)
    return fakes


def run_fit_report(jd, resume, model, modelId, fileName):
    OUTPUT_PATH = Path(f"evals/score_fit/{fileName}.json")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    prompt = (
        "Compare this job description with this resume.\n"
        "For every must-have, say whether the resume shows it.\n"
        "Copy evidence WORD FOR WORD from a resume bullet or a skill. Copy source_bullet WORD FOR WORD from a resume bullet. Never invent experience.\n"
        "If there is no honest match, put the must-have in gaps.\n"
        f"<job_description>\n{jd.model_dump_json()}\n</job_description>\n"
        f"<resume>\n{resume.model_dump_json()}\n</resume>"
    )
    start = time.time()
    fit_report, usage = extract_job_description(None, model, modelId, FitReport, prompt, maxTokens=8192)
    OUTPUT_PATH.write_text(fit_report.model_dump_json())
    seconds = time.time() - start
    run = log_run(modelId, f"fit_{fileName}", usage["attempts"], usage["input"], usage["output"], seconds)
    print(f"\n=== {modelId} : {fileName} ===\n\n")
    matched = sum(1 for m in fit_report.matches if m.matched)
    score = matched / len(fit_report.matches) * 100

    print(f"\n=== Your Score for {fileName} job is {score}% ===\n\n")

    fakes = find_fakes(fit_report, resume)
    print("FAKE QUOTES:" if fakes else "quotes OK", fakes if fakes else "")


if __name__ == "__main__":
    model = Model[sys.argv[1]] if len(sys.argv) > 1 else Model.ANTHROPIC  # "ANTHROPIC" (text) -> Model.ANTHROPIC
    modelId = sys.argv[2] if len(sys.argv) > 2 else "claude-haiku-5-5"  # default model
    resume = load_resume()
    for case in sorted(Path("evals/cases").glob("*.txt")):
        start = time.time()
        jd, usage = extract_job_description(case.read_text(), model, modelId, None, None)
        seconds = time.time() - start
        run = log_run(modelId, case.stem, usage["attempts"], usage["input"], usage["output"], seconds)
        run_fit_report(jd, resume, model, modelId, case.stem)
