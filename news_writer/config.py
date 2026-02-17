from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class AppConfig:
    google_api_key: str | None = os.getenv("GOOGLE_API_KEY")
    tavily_api_key: str | None = os.getenv("TAVILY_API_KEY")

    langsmith_api_key: str | None = os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")
    langchain_project: str | None = os.getenv("LANGCHAIN_PROJECT")
    langchain_tracing_v2: str | None = os.getenv("LANGCHAIN_TRACING_V2")


def apply_runtime_overrides(
    google_api_key: str | None,
    tavily_api_key: str | None,
    enable_tracing: bool,
    langsmith_api_key: str | None,
    project_name: str | None,
) -> None:
    if google_api_key:
        os.environ["GOOGLE_API_KEY"] = google_api_key
    if tavily_api_key:
        os.environ["TAVILY_API_KEY"] = tavily_api_key

    if enable_tracing:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        if langsmith_api_key:
            os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key
            os.environ["LANGSMITH_API_KEY"] = langsmith_api_key
        if project_name:
            os.environ["LANGCHAIN_PROJECT"] = project_name
    else:
        os.environ.pop("LANGCHAIN_TRACING_V2", None)
