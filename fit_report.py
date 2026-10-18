from pydantic import BaseModel, Field
from main import extract_job_description
import time


class RequirementMatch(BaseModel):
    requirment: str = Field(..., description="This line is from evaluation run on JD and copied from JD.must_have")
    matched: bool = Field(..., description="Does the requirment match True or False with resume. true only if the resume honestly shows this")
    evidence: str = Field(..., description="Exact evidence copied from resume that matches requirment")

class TailoredBullet(BaseModel):
    jd_requirment: str = Field(..., description="This line is copied from evaluation run on JD")
    source_bullet: bool = Field(..., description="Exact line and letter by letter from my resume bullet, Never paraphrase")
    rewritten: str = Field(..., description="Same facts as source_bullet. Use the job description's wording. Don't add numbers, tools or results that aren't in source_bullet. Tailored Rewritten source bullet in my resume to make it more valuable and in line with JD parsed to increase chances of getting shortlisted")

class FitReport(BaseModel):
    matches: list[RequirementMatch]
    bullets: list[TailoredBullet]
    gaps: list[str] = Field(..., description="must haves with no honest match")


def ask_model(prompt, response_model, model, modelId):
    # same body as now: pick the client, count tokens, create(...)
    # but with response_model=response_model
    start = time.time()
    jd, usage = extract_job_description(case.read_text(), model, modelId)
    seconds = time.time() - start
    run = log_run(modelId, case.stem, usage["attempts"], usage["input"], usage["output"], seconds)
    return result, usage