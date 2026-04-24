import json

from pydantic import ValidationError

from config import AppConfig
from prompts import build_api_messages
from schemas import VacancyAnalysis


class AnalysisError(Exception):
    pass


def _format_validation_error(error: ValidationError) -> str:
    messages: list[str] = []

    for item in error.errors():
        field = ".".join(str(part) for part in item["loc"])
        error_type = item["type"]

        if error_type == "missing":
            messages.append(f"Отсутствует обязательное поле: {field}.")
        elif field == "fit_score":
            messages.append("fit_score должен быть целым числом от 1 до 10.")
        elif field == "decision":
            messages.append("decision может быть только: apply, consider, skip.")
        elif field in {"sales_calls_risk", "vague_conditions_risk"}:
            messages.append(f"{field} может быть только: low, medium, high, unknown.")
        else:
            messages.append(f"Поле {field}: {item['msg']}.")

    return " ".join(messages)


def parse_analysis_json(json_text: str) -> VacancyAnalysis:
    if not json_text.strip():
        raise AnalysisError("JSON пустой. Вставьте JSON-ответ от ChatGPT перед строкой END.")

    try:
        raw_data = json.loads(json_text)
    except json.JSONDecodeError as error:
        raise AnalysisError(f"Невалидный JSON: {error.msg} на строке {error.lineno}, столбец {error.colno}.") from error

    try:
        return VacancyAnalysis.model_validate(raw_data)
    except ValidationError as error:
        raise AnalysisError(f"JSON не прошёл валидацию. {_format_validation_error(error)}") from error


def analyze_with_api(vacancy_text: str, config: AppConfig) -> VacancyAnalysis:
    if not config.openai_api_key:
        raise AnalysisError("OPENAI_API_KEY не указан.")

    try:
        from openai import OpenAI
    except ImportError as error:
        raise AnalysisError(
            "Пакет openai не установлен. Установите зависимости командой: pip install -r requirements.txt"
        ) from error

    try:
        client = OpenAI(api_key=config.openai_api_key)
        response = client.chat.completions.create(
            model=config.openai_model,
            messages=build_api_messages(vacancy_text),
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = response.choices[0].message.content
    except Exception as error:
        raise AnalysisError(f"API-запрос не удался: {error}") from error

    if not content:
        raise AnalysisError("API вернул пустой ответ.")

    try:
        return parse_analysis_json(content)
    except AnalysisError as error:
        raise AnalysisError(f"Ответ API не прошёл проверку: {error}") from error
