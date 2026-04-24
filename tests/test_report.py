import json

import pytest

from analyzer import parse_analysis_json
from report import ReportError, export_report, select_analyses_for_report
from storage import save_analysis_to_csv
from test_analyzer import valid_analysis_data


def make_analysis(title: str, decision: str, fit_score: int, sales_risk: str = "low"):
    data = valid_analysis_data()
    data["vacancy_title"] = title
    data["decision"] = decision
    data["fit_score"] = fit_score
    data["sales_calls_risk"] = sales_risk
    return parse_analysis_json(json.dumps(data, ensure_ascii=False))


def write_report_csv(path):
    save_analysis_to_csv(make_analysis("Первая вакансия", "apply", 8), path)
    save_analysis_to_csv(make_analysis("Вторая вакансия", "consider", 7, "high"), path)
    save_analysis_to_csv(make_analysis("Третья вакансия", "skip", 3), path)


def test_export_report_creates_markdown_with_summary_and_russian_text(tmp_path) -> None:
    csv_path = tmp_path / "analyses.csv"
    output_dir = tmp_path / "reports"
    write_report_csv(csv_path)

    report_path = export_report(csv_path=csv_path, output_dir=output_dir, limit=10)

    assert report_path.exists()
    assert report_path.parent == output_dir

    content = report_path.read_text(encoding="utf-8")

    assert "# Отчёт по анализу вакансий" in content
    assert "Количество вакансий: 3" in content
    assert "- apply: 1" in content
    assert "- consider: 1" in content
    assert "- skip: 1" in content
    assert "Первая вакансия" in content
    assert "количество high risk по sales_calls_risk: 1" in content


def test_select_analyses_for_report_filters_by_decision(tmp_path) -> None:
    csv_path = tmp_path / "analyses.csv"
    write_report_csv(csv_path)

    rows = select_analyses_for_report(csv_path=csv_path, decision="apply", limit=10)

    assert [row["vacancy_title"] for row in rows] == ["Первая вакансия"]


def test_select_analyses_for_report_filters_by_min_score(tmp_path) -> None:
    csv_path = tmp_path / "analyses.csv"
    write_report_csv(csv_path)

    rows = select_analyses_for_report(csv_path=csv_path, min_score=7, limit=10)

    assert [row["vacancy_title"] for row in rows] == ["Первая вакансия", "Вторая вакансия"]


def test_export_report_raises_when_csv_is_missing(tmp_path) -> None:
    with pytest.raises(ReportError, match="не найдены"):
        export_report(csv_path=tmp_path / "missing.csv", output_dir=tmp_path / "reports")


def test_export_report_raises_when_filters_match_nothing(tmp_path) -> None:
    csv_path = tmp_path / "analyses.csv"
    write_report_csv(csv_path)

    with pytest.raises(ReportError, match="не найдены"):
        export_report(csv_path=csv_path, output_dir=tmp_path / "reports", min_score=10)
