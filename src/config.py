from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
CONFIG_DIR = ROOT_DIR / "config"
OUTPUT_DIR = Path(os.getenv("AI_JOB_ANALYZER_OUTPUT_DIR", str(ROOT_DIR / "output")))
SAMPLE_VACANCY_PATH = DATA_DIR / "sample_yandex_fintech.txt"
OUTPUT_CSV_PATH = Path(os.getenv("AI_JOB_ANALYZER_OUTPUT_CSV", str(OUTPUT_DIR / "analyses.csv")))
RISK_WEIGHTS_PATH = CONFIG_DIR / "risk_weights.json"

DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"


@dataclass(frozen=True)
class AppConfig:
    openai_api_key: str
    openai_model: str


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> AppConfig:
    load_dotenv(ROOT_DIR / ".env")

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip()

    return AppConfig(
        openai_api_key=api_key,
        openai_model=model or DEFAULT_OPENAI_MODEL,
    )
