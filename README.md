# AI Job Vacancy Analyzer

CLI-инструмент для анализа вакансий под профиль кандидата начального уровня с использованием LLM, ручного JSON-режима, локальной эвристики красных флагов, CSV-хранилища и Markdown-отчётов.

## Зачем нужен проект

Проект помогает кандидату быстрее и спокойнее разбирать вакансии, особенно когда описание выглядит неоднозначно.

Он позволяет:
- анализировать вакансии по заданному профилю кандидата;
- выявлять продажи, звонки, мутные условия и другие красные флаги;
- сохранять результаты анализа;
- формировать Markdown-отчёты;
- работать даже без API-ключа через ручной JSON-режим.

## Возможности

- интерактивный CLI;
- анализ вакансии из ручного ввода;
- анализ вакансии из `.txt` файла;
- `manual_prompt` режим;
- `manual_json_save` режим;
- OpenAI API режим с fallback в ручной prompt;
- локальный risk score;
- настройка risk score через `config/risk_weights.json`;
- сохранение анализов в CSV;
- просмотр сохранённых анализов;
- фильтры по `decision` и `fit_score`;
- экспорт одного или нескольких анализов в Markdown;
- общий Markdown-отчёт;
- автотесты.

## Технологии

- Python;
- OpenAI SDK;
- Pydantic;
- pytest;
- argparse;
- CSV;
- Markdown;
- JSON config.

## Структура проекта

```text
ai-job-vacancy-analyzer/
├── config/
│   └── risk_weights.json
├── data/
│   └── sample_yandex_fintech.txt
├── docs/
│   ├── architecture.md
│   ├── portfolio_note.md
│   └── stage_history.md
├── examples/
│   ├── sample_analysis.json
│   ├── sample_report.md
│   └── sample_vacancy.txt
├── output/
│   └── .gitkeep
├── src/
│   ├── analyzer.py
│   ├── candidate_profile.py
│   ├── config.py
│   ├── heuristics.py
│   ├── main.py
│   ├── markdown_export.py
│   ├── prompts.py
│   ├── report.py
│   ├── schemas.py
│   └── storage.py
├── tests/
│   ├── conftest.py
│   ├── test_analyzer.py
│   ├── test_cli_commands.py
│   ├── test_heuristics.py
│   ├── test_markdown_export.py
│   ├── test_report.py
│   └── test_storage.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Быстрый старт на Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/main.py
```

## Использование без API-ключа

Проект можно использовать без OpenAI API.

В режиме `manual_prompt` приложение выводит готовый prompt для ChatGPT. Пользователь копирует prompt, вставляет его в ChatGPT и получает JSON-ответ.

В режиме `manual_json_save` приложение:
- выводит prompt;
- принимает JSON-ответ от ChatGPT;
- валидирует его через Pydantic;
- сохраняет результат в `output/analyses.csv`.

## Использование с OpenAI API

Создайте `.env` из примера:

```powershell
copy .env.example .env
```

Заполните переменные:

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
```

Реальный API-ключ нельзя коммитить в репозиторий.

Если `OPENAI_API_KEY` не указан, API-режим не падает и переключается в `manual_prompt`.

## Примеры команд

```powershell
python src/main.py
python src/main.py --help
python src/main.py analyze-file data/sample_yandex_fintech.txt --mode manual_prompt
python src/main.py analyze-file data/sample_yandex_fintech.txt --mode manual_json_save
python src/main.py view --limit 10
python src/main.py view --decision apply --limit 10
python src/main.py view --min-score 7 --limit 10
python src/main.py export --limit 5
python src/main.py report --decision apply --min-score 7 --limit 10
```

## Пример результата анализа

Компактный пример результата:

```json
{
  "vacancy_title": "Специалист сопровождения платёжных сервисов в Финтех",
  "decision": "apply",
  "fit_score": 8,
  "risks": {
    "sales_calls_risk": "low",
    "vague_conditions_risk": "low"
  },
  "cover_letter": "Здравствуйте! Меня заинтересовала вакансия, потому что она связана с техническими процессами, внутренними системами и разбором инцидентов."
}
```

Полная структура результата описана в prompt и валидируется через Pydantic.

## Где сохраняются результаты

- `output/analyses.csv` — сохранённые структурированные анализы;
- `output/exports/` — Markdown-файлы отдельных анализов;
- `output/reports/` — общие Markdown-отчёты.

Рабочие output-файлы не предназначены для коммита в Git.

## Настройка локального risk score

Локальный risk score настраивается через:

```text
config/risk_weights.json
```

Файл содержит веса для красных флагов вроде продаж, холодных звонков, курьерки, грузчика, личного автомобиля и оплаты только процентом.

Если файл отсутствует или содержит невалидный JSON, приложение использует встроенные веса и продолжает работу.

## Тесты

```powershell
python -m compileall src
python -m pytest
```

На текущем этапе проходит 35 тестов.

## Ограничения

- локальный risk score — эвристика, а не полноценный анализ вакансии;
- API с реальным ключом нужно проверять отдельно;
- проект не парсит сайты;
- проект не использует hh.ru API;
- `manual_json_save` требует ручной вставки JSON-ответа.

## Roadmap

Будущие идеи:
- web-интерфейс;
- интеграция с hh.ru API;
- пакетный импорт вакансий;
- RAG по резюме кандидата;
- агентная проверка вакансий;
- автоматическая генерация откликов под разные резюме.
