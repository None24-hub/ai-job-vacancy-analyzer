# ai-job-vacancy-analyzer

`ai-job-vacancy-analyzer` — CLI-приложение для анализа вакансий под профиль начинающего кандидата, которому интересны офисные, удалённые, back-office, support, QA, data, content, Python и automation-задачи.

Проект помогает:
- оценить вакансию через ChatGPT/OpenAI API или ручной JSON-ответ;
- увидеть локальные красные флаги и предварительный risk score;
- сохранить структурированный анализ в CSV;
- просмотреть и отфильтровать сохранённые анализы;
- экспортировать отдельные Markdown-файлы и общие Markdown-отчёты.

## Установка на Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/main.py
```

Альтернативный запуск без активации:

```powershell
.\.venv\Scripts\python.exe src\main.py
```

## Тесты

```powershell
python -m pytest
```

## Настройка `.env`

```powershell
copy .env.example .env
```

Для ручных режимов API-ключ не нужен.

Для API-режима заполните `.env`:

```env
OPENAI_API_KEY=ваш_api_ключ
OPENAI_MODEL=gpt-4.1-mini
```

## Интерактивный режим

```powershell
python src/main.py
```

Главное меню:

```text
1 — проанализировать вакансию
2 — посмотреть сохранённые анализы
3 — экспортировать анализ в Markdown
0 — выход
```

## Анализ вакансии

Интерактивный режим позволяет выбрать sample-вакансию или вставить текст вручную.

После выбора вакансии CLI показывает локальный risk score:

```text
Локальный риск: 3/10 — medium
Найденные флаги:
- ...
```

Если флагов нет:

```text
Локальный риск: 0/10 — low
Локальные красные флаги не найдены.
```

Это предварительная локальная подсказка, не замена LLM-анализу.

Доступные режимы анализа:
- `manual_prompt` — только вывести готовый prompt для ChatGPT;
- `manual_json_save` — вывести prompt, принять JSON до строки `END`, проверить и сохранить CSV;
- `api` — отправить вакансию в OpenAI API, а без ключа переключиться в `manual_prompt`.

## Анализ `.txt` файла

Команда:

```powershell
python src/main.py analyze-file data/sample_yandex_fintech.txt
```

По умолчанию используется режим `manual_prompt`.

Явный выбор режима:

```powershell
python src/main.py analyze-file data/sample_yandex_fintech.txt --mode manual_prompt
python src/main.py analyze-file data/sample_yandex_fintech.txt --mode manual_json_save
python src/main.py analyze-file data/sample_yandex_fintech.txt --mode api
```

Если файл не найден или пустой, CLI покажет понятную ошибку.

## Просмотр сохранённых анализов

Интерактивно: пункт `2 — посмотреть сохранённые анализы`.

Через команду:

```powershell
python src/main.py view --limit 10
python src/main.py view --decision apply --limit 10
python src/main.py view --min-score 7 --limit 10
```

Данные читаются из:

```text
output/analyses.csv
```

## Экспорт отдельных Markdown-файлов

Интерактивно: пункт `3 — экспортировать анализ в Markdown`.

Через команду:

```powershell
python src/main.py export --limit 5
```

Файлы создаются в:

```text
output/exports/
```

## Общий Markdown-отчёт

Команда `report` создаёт один общий Markdown-файл по нескольким сохранённым анализам:

```powershell
python src/main.py report --limit 10
python src/main.py report --decision apply --limit 10
python src/main.py report --min-score 7 --limit 10
python src/main.py report --decision apply --min-score 7 --limit 10
```

Отчёты создаются в:

```text
output/reports/
```

Отчёт содержит:
- дату создания;
- применённые фильтры;
- количество вакансий;
- сводку по `apply / consider / skip`;
- средний `fit_score`;
- количество high risk по `sales_calls_risk`;
- количество high risk по `vague_conditions_risk`;
- краткие блоки по каждой вакансии.

## Настройка весов risk score

Веса локального risk score лежат в:

```text
config/risk_weights.json
```

Пример:

```json
{
  "active_sales": 4,
  "cold_calls": 4,
  "client_calls": 3,
  "objections": 3,
  "client_search": 4,
  "sales_plan": 4,
  "personal_car": 4,
  "courier": 5,
  "loader": 5,
  "promoter": 4,
  "commission_only": 5,
  "unlimited_income": 3,
  "fast_career_growth": 1,
  "teach_to_earn": 3,
  "physical_load": 4,
  "high_stress": 2
}
```

Если файл отсутствует или содержит невалидный JSON, приложение использует встроенные веса и не падает.

## Пример рабочего сценария

```powershell
python src/main.py analyze-file data/sample_yandex_fintech.txt --mode manual_prompt
python src/main.py view --limit 10
python src/main.py report --decision apply --min-score 7 --limit 10
```

## Файлы в `output`

```text
output/analyses.csv
output/exports/
output/reports/
```

CSV создаётся после успешного API-анализа или успешного режима `manual_json_save`.

## Этап 7

На следующем этапе можно добавить:
- CLI-команду `analyze-file --save-prompt`;
- экспорт отфильтрованного списка в CSV;
- более подробную таблицу локальных флагов в Markdown-отчёте;
- тесты интерактивного меню через subprocess;
- настройку пути к CSV и папкам output через аргументы CLI.

Streamlit, база данных, агенты, RAG, hh.ru API, парсинг сайтов и Docker не входят в текущую версию.
