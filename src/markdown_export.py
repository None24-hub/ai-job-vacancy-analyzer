from datetime import datetime
import json
from pathlib import Path
from typing import Any, Mapping

from config import OUTPUT_DIR
from schemas import VacancyAnalysis


DEFAULT_EXPORT_DIR = OUTPUT_DIR / "exports"


def export_analysis_to_markdown(
    analysis: VacancyAnalysis | Mapping[str, Any],
    output_dir: Path = DEFAULT_EXPORT_DIR,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    data = _analysis_to_dict(analysis)
    export_path = _build_export_path(output_dir)
    export_path.write_text(_build_markdown(data), encoding="utf-8")

    return export_path


def export_analyses_to_markdown(
    analyses: list[VacancyAnalysis | Mapping[str, Any]],
    output_dir: Path = DEFAULT_EXPORT_DIR,
) -> list[Path]:
    return [export_analysis_to_markdown(analysis, output_dir) for analysis in analyses]


def _analysis_to_dict(analysis: VacancyAnalysis | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(analysis, VacancyAnalysis):
        return analysis.model_dump()

    return dict(analysis)


def _build_export_path(output_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = output_dir / f"analysis_{timestamp}.md"

    if not base_path.exists():
        return base_path

    counter = 1
    while True:
        candidate = output_dir / f"analysis_{timestamp}_{counter:03d}.md"
        if not candidate.exists():
            return candidate
        counter += 1


def _build_markdown(data: dict[str, Any]) -> str:
    return f"""# {_text(data, "vacancy_title")}

Компания: {_text(data, "company")}
Формат: {_text(data, "work_format")}
Зарплата: {_text(data, "salary")}
Решение: {_text(data, "decision")}
Оценка: {_text(data, "fit_score")}
Риск продаж/звонков: {_text(data, "sales_calls_risk")}
Риск мутных условий: {_text(data, "vague_conditions_risk")}

## Обязанности
{_text(data, "responsibilities_summary")}

## Требования
{_text(data, "requirements_summary")}

## Почему подходит
{_bullets(data, "why_it_fits")}

## Риски и сомнения
{_bullets(data, "concerns")}

## Вопросы работодателю
{_bullets(data, "questions_for_employer")}

## Сопроводительное письмо
{_text(data, "cover_letter")}
"""


def _text(data: dict[str, Any], key: str) -> str:
    value = data.get(key)

    if value is None or value == "":
        return "не указано"

    return str(value)


def _bullets(data: dict[str, Any], key: str) -> str:
    values = _list_value(data.get(key))

    if not values:
        return "- не указано"

    return "\n".join(f"- {value}" for value in values)


def _list_value(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [value] if value else []

        if isinstance(parsed, list):
            return [str(item) for item in parsed]

    return []
