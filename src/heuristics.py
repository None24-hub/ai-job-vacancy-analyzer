import json
from pathlib import Path
from typing import Any

from config import RISK_WEIGHTS_PATH


RED_FLAG_DEFINITIONS = [
    {
        "key": "active_sales",
        "name": "активные продажи",
        "patterns": ["активные продажи", "активных продаж"],
    },
    {
        "key": "cold_calls",
        "name": "холодные звонки",
        "patterns": ["холодные звонки", "холодных звонков"],
    },
    {
        "key": "client_calls",
        "name": "обзвон",
        "patterns": ["обзвон", "обзванивать"],
    },
    {
        "key": "objections",
        "name": "работа с возражениями",
        "patterns": ["работа с возражениями", "отработка возражений"],
    },
    {
        "key": "client_search",
        "name": "поиск клиентов",
        "patterns": ["поиск клиентов", "искать клиентов"],
    },
    {
        "key": "sales_plan",
        "name": "план продаж",
        "patterns": ["план продаж", "планы продаж"],
    },
    {
        "key": "personal_car",
        "name": "личный автомобиль",
        "patterns": ["личный автомобиль", "личного автомобиля", "личное авто"],
    },
    {
        "key": "courier",
        "name": "курьер",
        "patterns": ["курьер", "курьерская"],
    },
    {
        "key": "loader",
        "name": "грузчик",
        "patterns": ["грузчик", "разгрузка", "погрузка"],
    },
    {
        "key": "promoter",
        "name": "промоутер",
        "patterns": ["промоутер", "промо-акции"],
    },
    {
        "key": "unlimited_income",
        "name": "доход без потолка",
        "patterns": ["доход без потолка"],
    },
    {
        "key": "fast_career_growth",
        "name": "быстрый карьерный рост",
        "patterns": ["быстрый карьерный рост"],
    },
    {
        "key": "teach_to_earn",
        "name": "научим зарабатывать",
        "patterns": ["научим зарабатывать"],
    },
    {
        "key": "commission_only",
        "name": "зарплата только процентом",
        "patterns": ["только процент", "только за процент", "зарплата процент"],
    },
    {
        "key": "high_stress",
        "name": "высокий стресс",
        "patterns": ["высокий стресс", "стрессоустойчивость", "стрессовая"],
    },
    {
        "key": "physical_load",
        "name": "физическая нагрузка",
        "patterns": ["физическая нагрузка", "физические нагрузки", "физически активная"],
    },
]


DEFAULT_RISK_WEIGHTS = {
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
    "high_stress": 2,
}


def detect_red_flags(vacancy_text: str) -> list[str]:
    normalized_text = vacancy_text.lower()
    found_flags: list[str] = []

    for definition in RED_FLAG_DEFINITIONS:
        patterns = definition["patterns"]
        if any(pattern in normalized_text for pattern in patterns):
            found_flags.append(definition["name"])

    return found_flags


def calculate_local_risk_score(
    vacancy_text: str,
    weights_path: Path = RISK_WEIGHTS_PATH,
) -> dict:
    matched_definitions = _detect_red_flag_definitions(vacancy_text)
    red_flags = [definition["name"] for definition in matched_definitions]
    weights = load_risk_weights(weights_path)
    score = min(sum(weights.get(definition["key"], 1) for definition in matched_definitions), 10)
    level = _risk_level(score)

    return {
        "risk_score": score,
        "risk_level": level,
        "red_flags": red_flags,
        "summary": _risk_summary(score, level, red_flags),
    }


def load_risk_weights(path: Path = RISK_WEIGHTS_PATH) -> dict[str, int]:
    if not path.exists():
        return DEFAULT_RISK_WEIGHTS.copy()

    try:
        raw_data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_RISK_WEIGHTS.copy()

    if not isinstance(raw_data, dict):
        return DEFAULT_RISK_WEIGHTS.copy()

    weights = DEFAULT_RISK_WEIGHTS.copy()

    for key, value in raw_data.items():
        if key in weights and isinstance(value, int) and value >= 0:
            weights[key] = value

    return weights


def _detect_red_flag_definitions(vacancy_text: str) -> list[dict[str, Any]]:
    normalized_text = vacancy_text.lower()
    found: list[dict[str, Any]] = []

    for definition in RED_FLAG_DEFINITIONS:
        patterns = definition["patterns"]
        if any(pattern in normalized_text for pattern in patterns):
            found.append(definition)

    return found


def _risk_level(score: int) -> str:
    if score >= 6:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def _risk_summary(score: int, level: str, red_flags: list[str]) -> str:
    if not red_flags:
        return "Локальные красные флаги не найдены. Это не заменяет LLM-анализ."

    return (
        f"Найдено локальных красных флагов: {len(red_flags)}. "
        f"Предварительный риск: {score}/10 — {level}. "
        "Это не заменяет LLM-анализ."
    )
