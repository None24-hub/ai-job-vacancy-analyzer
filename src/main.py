import json
import sys

from analyzer import AnalysisError, analyze_with_api
from config import SAMPLE_VACANCY_PATH, ensure_directories, load_config
from prompts import build_manual_prompt
from storage import save_analysis_to_csv


def configure_output_encoding() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def read_sample_vacancy() -> str:
    if not SAMPLE_VACANCY_PATH.exists():
        print(f"Файл примера не найден: {SAMPLE_VACANCY_PATH}")
        print("Можно вставить текст вакансии вручную.")
        return read_vacancy_from_user()

    return SAMPLE_VACANCY_PATH.read_text(encoding="utf-8")


def read_vacancy_from_user() -> str:
    print("Вставьте текст вакансии.")
    print("Когда закончите, введите END на отдельной строке и нажмите Enter.")

    lines: list[str] = []

    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)

    return "\n".join(lines).strip()


def choose_vacancy_source() -> str:
    while True:
        print("\nВыберите источник вакансии:")
        print("1 — загрузить пример из data/sample_yandex_fintech.txt")
        print("2 — вставить текст вручную")

        choice = input("Ваш выбор: ").strip()

        if choice == "1":
            return read_sample_vacancy()
        if choice == "2":
            return read_vacancy_from_user()

        print("Введите 1 или 2.")


def choose_analysis_mode() -> str:
    while True:
        print("\nВыберите режим анализа:")
        print("1 — manual_prompt: подготовить промпт для ChatGPT")
        print("2 — api: отправить вакансию в OpenAI API")

        choice = input("Ваш выбор: ").strip()

        if choice == "1":
            return "manual_prompt"
        if choice == "2":
            return "api"

        print("Введите 1 или 2.")


def print_manual_prompt(vacancy_text: str) -> None:
    print("\n" + "=" * 80)
    print("ГОТОВЫЙ ПРОМПТ ДЛЯ CHATGPT")
    print("=" * 80)
    print(build_manual_prompt(vacancy_text))


def run_api_mode(vacancy_text: str) -> None:
    config = load_config()

    if not config.openai_api_key:
        print("\nOPENAI_API_KEY не указан или пустой.")
        print("API-запрос не выполняется. Переключаюсь в manual_prompt режим.")
        print_manual_prompt(vacancy_text)
        return

    try:
        analysis = analyze_with_api(vacancy_text, config)
    except AnalysisError as error:
        print(f"\nНе удалось выполнить API-анализ: {error}")
        print("Переключаюсь в manual_prompt режим.")
        print_manual_prompt(vacancy_text)
        return

    output_path = save_analysis_to_csv(analysis)

    print("\nСтруктурированный анализ:")
    print(json.dumps(analysis.model_dump(), ensure_ascii=False, indent=2))
    print(f"\nРезультат сохранён в {output_path}")


def main() -> None:
    configure_output_encoding()
    ensure_directories()

    print("AI Job Vacancy Analyzer — MVP CLI")
    vacancy_text = choose_vacancy_source()

    if not vacancy_text:
        print("Текст вакансии пустой. Анализ не запущен.")
        return

    mode = choose_analysis_mode()

    if mode == "manual_prompt":
        print_manual_prompt(vacancy_text)
    else:
        run_api_mode(vacancy_text)


if __name__ == "__main__":
    main()
