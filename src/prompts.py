from candidate_profile import (
    CANDIDATE_PROFILE,
    RED_FLAGS,
    SCORING_RULES,
    SUITABLE_DIRECTIONS,
    UNWANTED_DIRECTIONS,
)


RESPONSE_STRUCTURE = """\
Верни ответ строго в формате валидного JSON.
Не используй Markdown.
Не добавляй пояснения.
Не добавляй текст до или после JSON.

JSON должен иметь такую структуру:

{
  "vacancy_title": "название вакансии или не указано",
  "company": "компания или не указано",
  "work_format": "офис / удалёнка / гибрид / не указано",
  "salary": "зарплата или не указано",
  "responsibilities_summary": "краткое резюме обязанностей",
  "requirements_summary": "краткое резюме требований",
  "why_it_fits": [
    "причина 1",
    "причина 2"
  ],
  "concerns": [
    "риск 1",
    "риск 2"
  ],
  "sales_calls_risk": "low",
  "vague_conditions_risk": "low",
  "fit_score": 7,
  "decision": "apply",
  "questions_for_employer": [
    "вопрос 1",
    "вопрос 2"
  ],
  "cover_letter": "короткий сопроводительный текст"
}

Ограничения:
- sales_calls_risk может быть только: low, medium, high, unknown;
- vague_conditions_risk может быть только: low, medium, high, unknown;
- decision может быть только: apply, consider, skip;
- fit_score должен быть целым числом от 1 до 10;
- если информации нет в вакансии, писать "не указано";
- не выдумывать данные.
"""


API_JSON_INSTRUCTION = """\
Ответь только валидным JSON без Markdown, без пояснений и без текста до или после JSON.
Соблюдай ограничения из требуемой JSON-структуры.
"""


def build_manual_prompt(vacancy_text: str) -> str:
    return f"""\
Ты — помощник по анализу вакансий для начинающего IT/office/back-office кандидата.

{CANDIDATE_PROFILE}

{SUITABLE_DIRECTIONS}

{UNWANTED_DIRECTIONS}

{RED_FLAGS}

{SCORING_RULES}

{RESPONSE_STRUCTURE}

Текст вакансии:
---
{vacancy_text.strip()}
---
"""


def build_api_messages(vacancy_text: str) -> list[dict[str, str]]:
    system_prompt = (
        "Ты анализируешь вакансии на русском языке для кандидата начального уровня. "
        "Оценивай аккуратно, не выдумывай факты, соблюдай заданную JSON-структуру."
    )

    user_prompt = f"""\
{build_manual_prompt(vacancy_text)}

{API_JSON_INSTRUCTION}
"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
