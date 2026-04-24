import json

from analyzer import parse_analysis_json
from markdown_export import export_analysis_to_markdown
from test_analyzer import valid_analysis_data


def test_export_analysis_to_markdown_creates_file_with_expected_content(tmp_path) -> None:
    analysis = parse_analysis_json(json.dumps(valid_analysis_data(), ensure_ascii=False))

    export_path = export_analysis_to_markdown(analysis, tmp_path)

    assert export_path.exists()
    assert export_path.parent == tmp_path
    assert export_path.name.startswith("analysis_")
    assert export_path.suffix == ".md"

    content = export_path.read_text(encoding="utf-8")

    assert "# Тестовая вакансия" in content
    assert "Компания: Тестовая компания" in content
    assert "Оценка: 8" in content
    assert "- работа за компьютером" in content
    assert "Здравствуйте! Готов обсудить вакансию." in content
