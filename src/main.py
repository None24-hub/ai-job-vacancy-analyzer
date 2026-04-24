import json
import sys

from analyzer import AnalysisError, analyze_with_api, parse_analysis_json
from config import OUTPUT_CSV_PATH, SAMPLE_VACANCY_PATH, ensure_directories, load_config
from heuristics import detect_red_flags
from markdown_export import export_analysis_to_markdown
from prompts import build_manual_prompt
from schemas import VacancyAnalysis
from storage import filter_analyses, load_recent_analyses, load_saved_analyses, save_analysis_to_csv


def configure_output_encoding() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def prompt_input(prompt: str) -> str | None:
    try:
        return input(prompt)
    except EOFError:
        return None


def read_multiline_text(title: str) -> str:
    print(title)
    print("Когда закончите, введите END на отдельной строке и нажмите Enter.")

    lines: list[str] = []

    while True:
        line = prompt_input("")

        if line is None:
            break
        if line.strip().upper() == "END":
            break

        lines.append(line)

    return "\n".join(lines).strip()


def read_sample_vacancy() -> str:
    if not SAMPLE_VACANCY_PATH.exists():
        print(f"Файл примера не найден: {SAMPLE_VACANCY_PATH}")
        print("Можно вставить текст вакансии вручную.")
        return read_vacancy_from_user()

    return SAMPLE_VACANCY_PATH.read_text(encoding="utf-8")


def read_vacancy_from_user() -> str:
    return read_multiline_text("Вставьте текст вакансии.")


def read_json_from_user() -> str:
    return read_multiline_text("Вставьте JSON-ответ от ChatGPT.")


def choose_main_action() -> str | None:
    while True:
        print("\nГлавное меню:")
        print("1 — проанализировать вакансию")
        print("2 — посмотреть сохранённые анализы")
        print("3 — экспортировать анализ в Markdown")
        print("0 — выход")

        choice = prompt_input("Ваш выбор: ")

        if choice is None:
            return None

        choice = choice.strip()

        if choice in {"0", "1", "2", "3"}:
            return choice

        print("Введите 0, 1, 2 или 3.")


def choose_vacancy_source() -> str | None:
    while True:
        print("\nВыберите источник вакансии:")
        print("1 — загрузить пример из data/sample_yandex_fintech.txt")
        print("2 — вставить текст вручную")
        print("0 — назад в главное меню")

        choice = prompt_input("Ваш выбор: ")

        if choice is None:
            return None

        choice = choice.strip()

        if choice == "1":
            return read_sample_vacancy()
        if choice == "2":
            return read_vacancy_from_user()
        if choice == "0":
            return None

        print("Введите 0, 1 или 2.")


def choose_analysis_mode() -> str | None:
    while True:
        print("\nВыберите режим анализа:")
        print("1 — manual_prompt: подготовить промпт для ChatGPT")
        print("2 — manual_json_save: подготовить промпт, принять JSON и сохранить CSV")
        print("3 — api: отправить вакансию в OpenAI API")
        print("0 — назад в главное меню")

        choice = prompt_input("Ваш выбор: ")

        if choice is None:
            return None

        choice = choice.strip()

        if choice == "1":
            return "manual_prompt"
        if choice == "2":
            return "manual_json_save"
        if choice == "3":
            return "api"
        if choice == "0":
            return None

        print("Введите 0, 1, 2 или 3.")


def print_local_red_flags(vacancy_text: str) -> None:
    flags = detect_red_flags(vacancy_text)

    print("\nЛокальная проверка красных флагов:")

    if not flags:
        print("Локальные красные флаги не найдены.")
        return

    for flag in flags:
        print(f"- {flag}")

    print("Это предварительная подсказка. Она не заменяет LLM-анализ.")


def print_manual_prompt(vacancy_text: str) -> None:
    print("\n" + "=" * 80)
    print("ГОТОВЫЙ ПРОМПТ ДЛЯ CHATGPT")
    print("=" * 80)
    print(build_manual_prompt(vacancy_text))


def print_save_summary(analysis: VacancyAnalysis, output_path) -> None:
    print("\nАнализ сохранён.")
    print(f"Вакансия: {analysis.vacancy_title}")
    print(f"Решение: {analysis.decision}")
    print(f"Score: {analysis.fit_score}")
    print(f"CSV-файл: {output_path}")


def print_analyses(analyses: list[dict[str, str]]) -> None:
    if not analyses:
        print("\nСохранённые анализы не найдены.")
        return

    for index, row in enumerate(analyses, start=1):
        print(f"\n{index}. {row.get('vacancy_title', 'не указано')}")
        print(f"   Компания: {row.get('company', 'не указано')}")
        print(f"   Зарплата: {row.get('salary', 'не указано')}")
        print(f"   Score: {row.get('fit_score', 'не указано')}")
        print(f"   Решение: {row.get('decision', 'не указано')}")
        print(f"   Sales/calls risk: {row.get('sales_calls_risk', 'не указано')}")
        print(f"   Vague conditions risk: {row.get('vague_conditions_risk', 'не указано')}")


def run_manual_json_save_mode(vacancy_text: str) -> None:
    print_manual_prompt(vacancy_text)
    print("\nСкопируйте промпт выше в ChatGPT.")
    print("Затем вставьте сюда JSON-ответ от ChatGPT.")

    json_text = read_json_from_user()

    try:
        analysis = parse_analysis_json(json_text)
    except AnalysisError as error:
        print(f"\nДанные не сохранены: {error}")
        return

    output_path = save_analysis_to_csv(analysis)
    print_save_summary(analysis, output_path)


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
    print_save_summary(analysis, output_path)


def run_analysis_flow() -> None:
    vacancy_text = choose_vacancy_source()

    if vacancy_text is None:
        return

    if not vacancy_text:
        print("Текст вакансии пустой. Анализ не запущен.")
        return

    print_local_red_flags(vacancy_text)
    mode = choose_analysis_mode()

    if mode == "manual_prompt":
        print_manual_prompt(vacancy_text)
    elif mode == "manual_json_save":
        run_manual_json_save_mode(vacancy_text)
    elif mode == "api":
        run_api_mode(vacancy_text)


def run_view_saved_menu() -> None:
    while True:
        all_analyses = load_saved_analyses()

        if not all_analyses:
            print(f"\nСохранённые анализы не найдены. CSV-файл ещё не создан или пустой: {OUTPUT_CSV_PATH}")
            return

        print("\nПросмотр сохранённых анализов:")
        print("1 — показать последние 5")
        print("2 — показать только apply")
        print("3 — показать только consider")
        print("4 — показать только skip")
        print("5 — показать вакансии с fit_score от 7 и выше")
        print("0 — назад в главное меню")

        choice = prompt_input("Ваш выбор: ")

        if choice is None or choice.strip() == "0":
            return

        choice = choice.strip()

        if choice == "1":
            print("\nПоследние 5 анализов:")
            print_analyses(all_analyses[-5:])
        elif choice == "2":
            print("\nАнализы с решением apply:")
            print_analyses(filter_analyses(all_analyses, decision="apply"))
        elif choice == "3":
            print("\nАнализы с решением consider:")
            print_analyses(filter_analyses(all_analyses, decision="consider"))
        elif choice == "4":
            print("\nАнализы с решением skip:")
            print_analyses(filter_analyses(all_analyses, decision="skip"))
        elif choice == "5":
            print("\nАнализы с fit_score от 7 и выше:")
            print_analyses(filter_analyses(all_analyses, min_score=7))
        else:
            print("Введите 0, 1, 2, 3, 4 или 5.")


def run_export_markdown_flow() -> None:
    analyses = load_recent_analyses(limit=5)

    if not analyses:
        print(f"\nСохранённые анализы не найдены. CSV-файл ещё не создан или пустой: {OUTPUT_CSV_PATH}")
        return

    print("\nВыберите анализ для экспорта:")
    print_analyses(analyses)

    choice = prompt_input("\nВведите номер анализа или 0 для возврата: ")

    if choice is None or choice.strip() == "0":
        return

    try:
        index = int(choice.strip())
    except ValueError:
        print("Нужно ввести номер анализа.")
        return

    if index < 1 or index > len(analyses):
        print("Анализа с таким номером нет.")
        return

    export_path = export_analysis_to_markdown(analyses[index - 1])
    print(f"\nMarkdown-файл создан: {export_path}")


def main() -> None:
    configure_output_encoding()
    ensure_directories()

    print("AI Job Vacancy Analyzer — MVP CLI")

    while True:
        action = choose_main_action()

        if action is None or action == "0":
            print("Выход.")
            return
        if action == "1":
            run_analysis_flow()
        elif action == "2":
            run_view_saved_menu()
        elif action == "3":
            run_export_markdown_flow()


if __name__ == "__main__":
    main()
