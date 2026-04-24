import json
import os
import subprocess
import sys
from pathlib import Path

from analyzer import parse_analysis_json
from storage import save_analysis_to_csv
from test_analyzer import valid_analysis_data


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAIN_PATH = PROJECT_ROOT / "src" / "main.py"


def make_cli_env(tmp_path) -> dict[str, str]:
    output_dir = tmp_path / "output"
    env = os.environ.copy()
    env["AI_JOB_ANALYZER_OUTPUT_DIR"] = str(output_dir)
    env["AI_JOB_ANALYZER_OUTPUT_CSV"] = str(output_dir / "analyses.csv")
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def write_cli_csv(tmp_path) -> Path:
    output_dir = tmp_path / "output"
    csv_path = output_dir / "analyses.csv"

    data = valid_analysis_data()
    data["vacancy_title"] = "CLI тест"
    analysis = parse_analysis_json(json.dumps(data, ensure_ascii=False))
    save_analysis_to_csv(analysis, csv_path)

    return csv_path


def run_cli(args: list[str], tmp_path, input_text: str | None = None):
    return subprocess.run(
        [sys.executable, str(MAIN_PATH), *args],
        cwd=PROJECT_ROOT,
        env=make_cli_env(tmp_path),
        input=input_text,
        text=True,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )


def test_cli_help(tmp_path) -> None:
    result = run_cli(["--help"], tmp_path)

    assert result.returncode == 0
    assert "usage:" in result.stdout


def test_cli_view_limit(tmp_path) -> None:
    write_cli_csv(tmp_path)

    result = run_cli(["view", "--limit", "5"], tmp_path)

    assert result.returncode == 0
    assert "CLI тест" in result.stdout


def test_cli_view_decision_filter(tmp_path) -> None:
    write_cli_csv(tmp_path)

    result = run_cli(["view", "--decision", "apply", "--limit", "5"], tmp_path)

    assert result.returncode == 0
    assert "CLI тест" in result.stdout


def test_cli_view_min_score_filter(tmp_path) -> None:
    write_cli_csv(tmp_path)

    result = run_cli(["view", "--min-score", "7", "--limit", "5"], tmp_path)

    assert result.returncode == 0
    assert "CLI тест" in result.stdout


def test_cli_export_limit(tmp_path) -> None:
    write_cli_csv(tmp_path)

    result = run_cli(["export", "--limit", "1"], tmp_path)

    assert result.returncode == 0
    assert ".md" in result.stdout
    assert len(list((tmp_path / "output" / "exports").glob("*.md"))) == 1


def test_cli_analyze_file_manual_prompt(tmp_path) -> None:
    result = run_cli(
        ["analyze-file", "data/sample_yandex_fintech.txt", "--mode", "manual_prompt"],
        tmp_path,
    )

    assert result.returncode == 0
    assert "Локальный риск" in result.stdout
    assert "ГОТОВЫЙ ПРОМПТ" in result.stdout


def test_cli_report_limit(tmp_path) -> None:
    write_cli_csv(tmp_path)

    result = run_cli(["report", "--limit", "5"], tmp_path)

    assert result.returncode == 0
    assert ".md" in result.stdout
    assert len(list((tmp_path / "output" / "reports").glob("*.md"))) == 1
