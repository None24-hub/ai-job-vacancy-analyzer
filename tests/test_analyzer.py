import json

import pytest

from analyzer import AnalysisError, parse_analysis_json
from schemas import VacancyAnalysis


def valid_analysis_data() -> dict:
    return {
        "vacancy_title": "Тестовая вакансия",
        "company": "Тестовая компания",
        "work_format": "удалёнка",
        "salary": "от 50 000 ₽",
        "responsibilities_summary": "Работа с документами и внутренними системами.",
        "requirements_summary": "Уверенное владение ПК и внимательность.",
        "why_it_fits": ["работа за компьютером", "нет продаж"],
        "concerns": ["нужно уточнить график"],
        "sales_calls_risk": "low",
        "vague_conditions_risk": "low",
        "fit_score": 8,
        "decision": "apply",
        "questions_for_employer": ["Как проходит обучение?"],
        "cover_letter": "Здравствуйте! Готов обсудить вакансию.",
    }


def test_parse_analysis_json_accepts_valid_json() -> None:
    analysis = parse_analysis_json(json.dumps(valid_analysis_data(), ensure_ascii=False))

    assert isinstance(analysis, VacancyAnalysis)
    assert analysis.vacancy_title == "Тестовая вакансия"
    assert analysis.fit_score == 8
    assert analysis.decision == "apply"


def test_parse_analysis_json_rejects_empty_input() -> None:
    with pytest.raises(AnalysisError, match="JSON"):
        parse_analysis_json("")


def test_parse_analysis_json_rejects_invalid_json() -> None:
    with pytest.raises(AnalysisError, match="Невалидный JSON"):
        parse_analysis_json('{"vacancy_title": "broken",')


def test_parse_analysis_json_rejects_fit_score_out_of_range() -> None:
    data = valid_analysis_data()
    data["fit_score"] = 11

    with pytest.raises(AnalysisError, match="fit_score"):
        parse_analysis_json(json.dumps(data, ensure_ascii=False))


def test_parse_analysis_json_rejects_wrong_decision() -> None:
    data = valid_analysis_data()
    data["decision"] = "maybe"

    with pytest.raises(AnalysisError, match="decision"):
        parse_analysis_json(json.dumps(data, ensure_ascii=False))


def test_parse_analysis_json_rejects_wrong_sales_calls_risk() -> None:
    data = valid_analysis_data()
    data["sales_calls_risk"] = "danger"

    with pytest.raises(AnalysisError, match="sales_calls_risk"):
        parse_analysis_json(json.dumps(data, ensure_ascii=False))
