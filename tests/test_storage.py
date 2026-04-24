import csv
import json

from analyzer import parse_analysis_json
from storage import (
    CSV_FIELDS,
    filter_analyses,
    load_saved_analyses,
    save_analysis_to_csv,
)
from test_analyzer import valid_analysis_data


def test_save_analysis_to_csv_creates_file_with_headers_and_utf8_values(tmp_path) -> None:
    analysis = parse_analysis_json(json.dumps(valid_analysis_data(), ensure_ascii=False))
    output_path = tmp_path / "analyses.csv"

    save_analysis_to_csv(analysis, output_path)

    assert output_path.exists()

    with output_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    assert reader.fieldnames == CSV_FIELDS
    assert len(rows) == 1
    assert rows[0]["vacancy_title"] == "Тестовая вакансия"
    assert rows[0]["salary"] == "от 50 000 ₽"
    assert json.loads(rows[0]["why_it_fits"]) == ["работа за компьютером", "нет продаж"]
    assert json.loads(rows[0]["concerns"]) == ["нужно уточнить график"]
    assert json.loads(rows[0]["questions_for_employer"]) == ["Как проходит обучение?"]


def test_save_analysis_to_csv_appends_without_overwriting(tmp_path) -> None:
    analysis = parse_analysis_json(json.dumps(valid_analysis_data(), ensure_ascii=False))
    output_path = tmp_path / "analyses.csv"

    save_analysis_to_csv(analysis, output_path)
    save_analysis_to_csv(analysis, output_path)

    with output_path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 2


def test_load_saved_analyses_reads_rows_from_csv(tmp_path) -> None:
    analysis = parse_analysis_json(json.dumps(valid_analysis_data(), ensure_ascii=False))
    output_path = tmp_path / "analyses.csv"
    save_analysis_to_csv(analysis, output_path)

    rows = load_saved_analyses(output_path)

    assert len(rows) == 1
    assert rows[0]["vacancy_title"] == "Тестовая вакансия"
    assert rows[0]["decision"] == "apply"


def test_filter_analyses_by_decision() -> None:
    rows = [
        {"vacancy_title": "A", "decision": "apply", "fit_score": "8"},
        {"vacancy_title": "B", "decision": "consider", "fit_score": "7"},
        {"vacancy_title": "C", "decision": "skip", "fit_score": "3"},
    ]

    filtered = filter_analyses(rows, decision="apply")

    assert filtered == [{"vacancy_title": "A", "decision": "apply", "fit_score": "8"}]


def test_filter_analyses_by_min_score() -> None:
    rows = [
        {"vacancy_title": "A", "decision": "apply", "fit_score": "8"},
        {"vacancy_title": "B", "decision": "consider", "fit_score": "7"},
        {"vacancy_title": "C", "decision": "skip", "fit_score": "6"},
        {"vacancy_title": "D", "decision": "skip", "fit_score": "not a number"},
    ]

    filtered = filter_analyses(rows, min_score=7)

    assert [row["vacancy_title"] for row in filtered] == ["A", "B"]
