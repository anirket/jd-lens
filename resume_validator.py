from pydantic import BaseModel, Field
from pathlib import Path


class Jobs(BaseModel):
    company: str = Field(..., description="Name of the company where the candidate worked or is currently working")
    title: str = Field(..., description="Job title of the candidate")
    start: str | None = Field(default=None, description="Start date of the job")
    end: str | None = Field(default=None, description="End date of the job")
    bullets: list[str] = Field(..., description="List of bullet points describing the candidate's responsibilities and achievements in the job")

class Resume(BaseModel):
    name: str = Field(..., description="Name of the candidate")
    years_of_experience: int = Field(..., gt=0, description="Years of experience for all jobs listed in the resume")
    skills: list[str] = Field(..., description="List of skills for the candidate")
    jobs: list[Jobs] = Field(..., description="List of past and current jobs candidate has held, including company name, title, start and end dates, and bullet points describing their responsibilities and achievements in each role.")


def load_resume():
    return Resume.model_validate_json(Path('resume.json').read_text())
