import argparse
import json
import sys

from analyzer import AnalysisError, analyze_with_api, parse_analysis_json
from config import OUTPUT_CSV_PATH, SAMPLE_VACANCY_PATH, ensure_directories, load_config
from heuristics import calculate_local_risk_score
from markdown_export import export_analyses_to_markdown, export_analysis_to_markdown
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
    result = calculate_local_risk_score(vacancy_text)
    flags = result["red_flags"]

    print("\nЛокальная проверка красных флагов:")
    print(f"Локальный риск: {result['risk_score']}/10 — {result['risk_level']}")

    if not flags:
        print("Локальные красные флаги не найдены.")
        return

    print("Найденные флаги:")
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


def ask_result_limit(default: int = 5) -> int:
    value = prompt_input(f"Сколько анализов показать? По умолчанию {default}: ")

    if value is None or not value.strip():
        return default

    try:
        limit = int(value.strip())
    except ValueError:
        return default

    return limit if limit > 0 else default


def apply_saved_filters(
    analyses: list[dict[str, str]],
    decision: str | None = None,
    min_score: int | None = None,
    limit: int = 5,
) -> list[dict[str, str]]:
    return filter_analyses(
        analyses,
        decision=decision,
        min_score=min_score,
        limit=limit,
    )


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
            limit = ask_result_limit()
            print(f"\nПоследние {limit} анализов:")
            print_analyses(all_analyses[-limit:])
        elif choice == "2":
            limit = ask_result_limit()
            print("\nАнализы с решением apply:")
            print_analyses(apply_saved_filters(all_analyses, decision="apply", limit=limit))
        elif choice == "3":
            limit = ask_result_limit()
            print("\nАнализы с решением consider:")
            print_analyses(apply_saved_filters(all_analyses, decision="consider", limit=limit))
        elif choice == "4":
            limit = ask_result_limit()
            print("\nАнализы с решением skip:")
            print_analyses(apply_saved_filters(all_analyses, decision="skip", limit=limit))
        elif choice == "5":
            limit = ask_result_limit()
            print("\nАнализы с fit_score от 7 и выше:")
            print_analyses(apply_saved_filters(all_analyses, min_score=7, limit=limit))
        else:
            print("Введите 0, 1, 2, 3, 4 или 5.")


def run_export_markdown_flow() -> None:
    while True:
        print("\nЭкспорт в Markdown:")
        print("1 — экспортировать один анализ")
        print("2 — экспортировать последние N анализов")
        print("0 — назад")

        choice = prompt_input("Ваш выбор: ")

        if choice is None or choice.strip() == "0":
            return
        if choice.strip() == "1":
            export_single_analysis_interactive()
            return
        if choice.strip() == "2":
            export_recent_analyses_interactive()
            return

        print("Введите 0, 1 или 2.")


def export_single_analysis_interactive() -> None:
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


def export_recent_analyses_interactive() -> None:
    limit = ask_result_limit()
    analyses = load_recent_analyses(limit=limit)

    if not analyses:
        print(f"\nСохранённые анализы не найдены. CSV-файл ещё не создан или пустой: {OUTPUT_CSV_PATH}")
        return

    export_paths = export_analyses_to_markdown(analyses)

    print("\nСозданы Markdown-файлы:")
    for path in export_paths:
        print(f"- {path}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Job Vacancy Analyzer CLI")
    subparsers = parser.add_subparsers(dest="command")

    view_parser = subparsers.add_parser("view", help="Показать сохранённые анализы")
    view_parser.add_argument("--limit", type=int, default=5, help="Сколько последних анализов показать")
    view_parser.add_argument("--decision", choices=["apply", "consider", "skip"], help="Фильтр по решению")
    view_parser.add_argument("--min-score", type=int, help="Минимальный fit_score")

    export_parser = subparsers.add_parser("export", help="Экспортировать последние анализы в Markdown")
    export_parser.add_argument("--limit", type=int, default=5, help="Сколько последних анализов экспортировать")

    return parser


def run_view_command(args: argparse.Namespace) -> None:
    limit = normalize_limit(args.limit)
    analyses = load_saved_analyses()

    if not analyses:
        print(f"Сохранённые анализы не найдены. CSV-файл ещё не создан или пустой: {OUTPUT_CSV_PATH}")
        return

    filtered = apply_saved_filters(
        analyses,
        decision=args.decision,
        min_score=args.min_score,
        limit=limit,
    )

    print_analyses(filtered)


def run_export_command(args: argparse.Namespace) -> None:
    limit = normalize_limit(args.limit)
    analyses = load_recent_analyses(limit=limit)

    if not analyses:
        print(f"Сохранённые анализы не найдены. CSV-файл ещё не создан или пустой: {OUTPUT_CSV_PATH}")
        return

    export_paths = export_analyses_to_markdown(analyses)

    print("Созданы Markdown-файлы:")
    for path in export_paths:
        print(f"- {path}")


def normalize_limit(value: int, default: int = 5) -> int:
    return value if value > 0 else default


def main() -> None:
    configure_output_encoding()
    ensure_directories()

    parser = build_arg_parser()
    args = parser.parse_args()

    if args.command == "view":
        run_view_command(args)
        return
    if args.command == "export":
        run_export_command(args)
        return

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
