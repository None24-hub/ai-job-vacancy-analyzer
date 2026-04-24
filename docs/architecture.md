# Architecture

Проект устроен как простой CLI-инструмент без базы данных, web-интерфейса и фоновых сервисов.

## Основные модули

- `main.py` — CLI и маршрутизация команд. Здесь находится интерактивное меню и `argparse`-команды `view`, `export`, `analyze-file`, `report`.
- `analyzer.py` — API-анализ, JSON-разбор и валидационные ошибки. Здесь вызывается OpenAI SDK и обрабатывается fallback.
- `schemas.py` — Pydantic-схема `VacancyAnalysis`, которая фиксирует структуру результата анализа.
- `storage.py` — CSV-хранилище: сохранение анализов, чтение сохранённых строк, фильтрация по `decision` и `fit_score`.
- `heuristics.py` — локальные красные флаги и risk score. Веса можно настраивать через `config/risk_weights.json`.
- `markdown_export.py` — экспорт одного или нескольких анализов в отдельные Markdown-файлы.
- `report.py` — общий Markdown-отчёт по нескольким анализам с краткой сводкой.
- `config.py` — настройки путей, `.env`, output-директорий и имени модели.
- `candidate_profile.py` — профиль кандидата, подходящие направления, нежелательные направления, красные флаги и правила оценки.
- `prompts.py` — сборка prompt для ChatGPT/OpenAI API.

## Поток manual_prompt

1. Пользователь вводит вакансию или выбирает `.txt` файл.
2. CLI показывает локальный risk score.
3. Приложение печатает prompt.
4. Пользователь вручную вставляет prompt в ChatGPT.

## Поток manual_json_save

1. CLI выводит prompt.
2. Пользователь вставляет JSON-ответ от ChatGPT.
3. `analyzer.py` парсит JSON.
4. `schemas.py` валидирует структуру.
5. `storage.py` сохраняет результат в CSV.

## Поток api

1. CLI проверяет `OPENAI_API_KEY`.
2. Если ключа нет, включается fallback в `manual_prompt`.
3. Если ключ есть, OpenAI SDK отправляет prompt в модель.
4. Ответ валидируется и сохраняется в CSV.

## Отчёты

- `markdown_export.py` создаёт отдельные Markdown-файлы по анализам.
- `report.py` создаёт общий Markdown-отчёт по нескольким строкам из CSV.

## Хранение данных

Проект использует файловое хранение:

- `output/analyses.csv`;
- `output/exports/`;
- `output/reports/`.

Эти файлы считаются рабочими артефактами и не должны попадать в Git.
