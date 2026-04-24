RED_FLAG_PATTERNS = {
    "активные продажи": ["активные продажи", "активных продаж"],
    "холодные звонки": ["холодные звонки", "холодных звонков"],
    "обзвон": ["обзвон", "обзванивать"],
    "работа с возражениями": ["работа с возражениями", "отработка возражений"],
    "поиск клиентов": ["поиск клиентов", "искать клиентов"],
    "план продаж": ["план продаж", "планы продаж"],
    "личный автомобиль": ["личный автомобиль", "личного автомобиля", "личное авто"],
    "курьер": ["курьер", "курьерская"],
    "грузчик": ["грузчик", "разгрузка", "погрузка"],
    "промоутер": ["промоутер", "промо-акции"],
    "доход без потолка": ["доход без потолка"],
    "быстрый карьерный рост": ["быстрый карьерный рост"],
    "научим зарабатывать": ["научим зарабатывать"],
    "зарплата только процентом": ["только процент", "только за процент", "зарплата процент"],
    "высокий стресс": ["высокий стресс", "стрессоустойчивость", "стрессовая"],
    "физическая нагрузка": ["физическая нагрузка", "физические нагрузки", "физически активная"],
}


RED_FLAG_WEIGHTS = {
    "активные продажи": 3,
    "холодные звонки": 3,
    "зарплата только процентом": 3,
    "личный автомобиль": 3,
    "курьер": 3,
    "грузчик": 3,
    "обзвон": 2,
    "работа с возражениями": 2,
    "поиск клиентов": 2,
    "план продаж": 2,
    "промоутер": 2,
    "доход без потолка": 2,
    "научим зарабатывать": 2,
    "быстрый карьерный рост": 1,
    "высокий стресс": 1,
    "физическая нагрузка": 1,
}


def detect_red_flags(vacancy_text: str) -> list[str]:
    normalized_text = vacancy_text.lower()
    found_flags: list[str] = []

    for flag_name, patterns in RED_FLAG_PATTERNS.items():
        if any(pattern in normalized_text for pattern in patterns):
            found_flags.append(flag_name)

    return found_flags


def calculate_local_risk_score(vacancy_text: str) -> dict:
    red_flags = detect_red_flags(vacancy_text)
    score = min(sum(RED_FLAG_WEIGHTS.get(flag, 1) for flag in red_flags), 10)
    level = _risk_level(score)

    return {
        "risk_score": score,
        "risk_level": level,
        "red_flags": red_flags,
        "summary": _risk_summary(score, level, red_flags),
    }


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
