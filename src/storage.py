import csv
import json
from pathlib import Path
from typing import Any

from config import OUTPUT_CSV_PATH, OUTPUT_DIR
from schemas import VacancyAnalysis


CSV_FIELDS = list(VacancyAnalysis.model_fields.keys())


def _prepare_csv_row(analysis: VacancyAnalysis) -> dict[str, Any]:
    row = analysis.model_dump()

    for key, value in row.items():
        if isinstance(value, (list, dict)):
            row[key] = json.dumps(value, ensure_ascii=False)

    return row


def save_analysis_to_csv(
    analysis: VacancyAnalysis,
    path: Path = OUTPUT_CSV_PATH,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)

    row = _prepare_csv_row(analysis)
    file_exists = path.exists() and path.stat().st_size > 0

    with path.open("a", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)

    return path


def load_recent_analyses(
    path: Path = OUTPUT_CSV_PATH,
    limit: int = 5,
) -> list[dict[str, str]]:
    rows = load_saved_analyses(path)

    return rows[-limit:]


def load_saved_analyses(path: Path = OUTPUT_CSV_PATH) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def filter_analyses(
    analyses: list[dict[str, str]],
    decision: str | None = None,
    min_score: int | None = None,
    limit: int | None = None,
) -> list[dict[str, str]]:
    filtered = analyses

    if decision is not None:
        filtered = [row for row in filtered if row.get("decision") == decision]

    if min_score is not None:
        filtered = [
            row
            for row in filtered
            if _safe_int(row.get("fit_score")) is not None
            and _safe_int(row.get("fit_score")) >= min_score
        ]

    if limit is not None:
        filtered = filtered[-limit:]

    return filtered


def _safe_int(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None
