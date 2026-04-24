import json

from pydantic import ValidationError

from config import AppConfig
from prompts import build_api_messages
from schemas import VacancyAnalysis


class AnalysisError(Exception):
    pass


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
        raw_data = json.loads(content)
    except json.JSONDecodeError as error:
        raise AnalysisError("API вернул невалидный JSON.") from error

    try:
        return VacancyAnalysis.model_validate(raw_data)
    except ValidationError as error:
        raise AnalysisError(f"Ответ API не прошёл валидацию: {error}") from error
