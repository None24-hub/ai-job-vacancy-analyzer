import csv
import json

from analyzer import parse_analysis_json
from storage import CSV_FIELDS, save_analysis_to_csv
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
