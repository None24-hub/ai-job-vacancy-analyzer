from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


RiskLevel = Literal["low", "medium", "high", "unknown"]
Decision = Literal["apply", "consider", "skip"]


class VacancyAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vacancy_title: str
    company: str
    work_format: str
    salary: str
    responsibilities_summary: str
    requirements_summary: str
    why_it_fits: list[str]
    concerns: list[str]
    sales_calls_risk: RiskLevel
    vague_conditions_risk: RiskLevel
    fit_score: int = Field(ge=1, le=10)
    decision: Decision
    questions_for_employer: list[str]
    cover_letter: str
