from pydantic import BaseModel, Field
from typing import Literal

Seniority = Literal["junior", "mid", "senior", "staff"]
WorkMode = Literal["remote", "hybrid", "onsite"]


class JobDescription(BaseModel):
        company: str | None = Field(
            None, description="Hiring company. None if the JD doesn't name it."
        )
        role: str = Field(..., description="Job title as written, e.g. 'Agent Engineer'.")
        seniority: Seniority = Field(...,
            description=(
                "Decide in this order: "
                "1) If the JD explicitly says junior/senior/staff, use that. "
                "2) Else use years: junior <2y, mid 2-5y, senior 5-8y, staff 8y+. "
                "3) Else infer from the scope of responsibilities."                    
            )
        )
        years_min: int | None = Field(None, description="Minimum years of experience asked for.")
        years_max: int | None = Field(None, description="Maximum years, if range is specified.")
        location: str | None = Field(None, description="Location of the job, if specified.")
        work_mode: WorkMode | None = Field(None, description="Work mode of the job, if specified.")
        responsibilities: list[str] = Field(
            description="What the person will do day to day, one short item each."
        )
        must_haves: list[str] = Field(
            description=(
                "Hard requirements, shortened to a few words each. "
                "One requirement per item, don't merge. "
                "Include non-technical requirements (e.g. 'shipped and owned production systems'). "
                "Bonus/plus/'stands out if' items go in nice_to_haves, not here."
            )
        )
        nice_to_haves: list[str] = Field(
            description=(
                "Bonus, preferred, or 'stands out if' items, shortened. "
                "One requirement per item, don't merge."
            )
        )
        stack: list[str] = Field(
            description=(
                "Named technologies only: languages, frameworks, libraries, databases, "
                "cloud services, tools, models (e.g. 'Python', 'Postgres', 'AWS', 'React'). "
                "One name per item. No sentences, no skills like 'evals' or 'system design'. "
                "A technology can appear here and also inside a must_haves sentence."
            )
        )
