from datetime import datetime
import json
from pathlib import Path
from typing import Any

from config import OUTPUT_CSV_PATH, OUTPUT_DIR
from storage import filter_analyses, load_saved_analyses


DEFAULT_REPORT_DIR = OUTPUT_DIR / "reports"


class ReportError(Exception):
    pass


def select_analyses_for_report(
    csv_path: Path = OUTPUT_CSV_PATH,
    decision: str | None = None,
    min_score: int | None = None,
    limit: int = 10,
) -> list[dict[str, str]]:
    rows = load_saved_analyses(csv_path)

    if not rows:
        return []

    return filter_analyses(
        rows,
        decision=decision,
        min_score=min_score,
        limit=limit,
    )


def export_report(
    csv_path: Path = OUTPUT_CSV_PATH,
    output_dir: Path = DEFAULT_REPORT_DIR,
    decision: str | None = None,
    min_score: int | None = None,
    limit: int = 10,
) -> Path:
    analyses = select_analyses_for_report(
        csv_path=csv_path,
        decision=decision,
        min_score=min_score,
        limit=limit,
    )

    if not analyses:
        raise ReportError("Подходящие сохранённые анализы не найдены.")

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = _build_report_path(output_dir)
    report_path.write_text(
        _build_report_markdown(
            analyses,
            decision=decision,
            min_score=min_score,
            limit=limit,
        ),
        encoding="utf-8",
    )

    return report_path


def _build_report_path(output_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = output_dir / f"report_{timestamp}.md"

    if not base_path.exists():
        return base_path

    counter = 1
    while True:
        candidate = output_dir / f"report_{timestamp}_{counter:03d}.md"
        if not candidate.exists():
            return candidate
        counter += 1


def _build_report_markdown(
    analyses: list[dict[str, str]],
    decision: str | None,
    min_score: int | None,
    limit: int,
) -> str:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = _build_summary(analyses)
    filters = _format_filters(decision, min_score, limit)
    vacancy_sections = "\n\n".join(
        _build_vacancy_section(index, analysis)
        for index, analysis in enumerate(analyses, start=1)
    )

    return f"""# Отчёт по анализу вакансий

Дата создания: {created_at}
Фильтры: {filters}
Количество вакансий: {len(analyses)}

## Краткая сводка

- apply: {summary["apply"]}
- consider: {summary["consider"]}
- skip: {summary["skip"]}
- средний fit_score: {summary["average_score"]}
- количество high risk по sales_calls_risk: {summary["high_sales_risk"]}
- количество high risk по vague_conditions_risk: {summary["high_vague_risk"]}

## Вакансии

{vacancy_sections}
"""


def _build_summary(analyses: list[dict[str, str]]) -> dict[str, Any]:
    scores = [_safe_int(row.get("fit_score")) for row in analyses]
    scores = [score for score in scores if score is not None]
    average_score = round(sum(scores) / len(scores), 2) if scores else "не указано"

    return {
        "apply": sum(1 for row in analyses if row.get("decision") == "apply"),
        "consider": sum(1 for row in analyses if row.get("decision") == "consider"),
        "skip": sum(1 for row in analyses if row.get("decision") == "skip"),
        "average_score": average_score,
        "high_sales_risk": sum(1 for row in analyses if row.get("sales_calls_risk") == "high"),
        "high_vague_risk": sum(1 for row in analyses if row.get("vague_conditions_risk") == "high"),
    }


def _build_vacancy_section(index: int, analysis: dict[str, str]) -> str:
    return f"""### {index}. {_text(analysis, "vacancy_title")}

Компания: {_text(analysis, "company")}
Зарплата: {_text(analysis, "salary")}
Решение: {_text(analysis, "decision")}
Оценка: {_text(analysis, "fit_score")}
Риск продаж/звонков: {_text(analysis, "sales_calls_risk")}
Риск мутных условий: {_text(analysis, "vague_conditions_risk")}

Кратко:
{_text(analysis, "responsibilities_summary")}

Почему подходит:
{_bullets(analysis, "why_it_fits")}

Риски:
{_bullets(analysis, "concerns")}

Вопросы работодателю:
{_bullets(analysis, "questions_for_employer")}
"""


def _format_filters(decision: str | None, min_score: int | None, limit: int) -> str:
    parts = [f"limit={limit}"]

    if decision:
        parts.append(f"decision={decision}")
    if min_score is not None:
        parts.append(f"min_score={min_score}")

    return ", ".join(parts)


def _text(data: dict[str, str], key: str) -> str:
    value = data.get(key)
    return value if value else "не указано"


def _bullets(data: dict[str, str], key: str) -> str:
    values = _list_value(data.get(key))

    if not values:
        return "- не указано"

    return "\n".join(f"- {value}" for value in values)


def _list_value(value: str | None) -> list[str]:
    if not value:
        return []

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return [value]

    if isinstance(parsed, list):
        return [str(item) for item in parsed]

    return [str(parsed)]


def _safe_int(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None
