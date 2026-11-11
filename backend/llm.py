import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from .prompt import build_universal_prompt
from .data_prepare import profile_data
from langchain_groq import ChatGroq

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def analyze_dataset(filename: str, dataframe: pd.DataFrame) -> dict:
    profile = profile_data(dataframe)
    prompt = build_universal_prompt(
        filename=filename,
        row_count=profile["row_count"],
        col_count=profile["col_count"],
        numeric_stats=profile["numerical_stats"],
        categorical_stats=profile["categorical_stats"],
        datetime_stats=profile["date_stats"],
    )

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing. Set it in the project .env file.")

    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
    if not model:
        raise ValueError("GROQ_MODEL cannot be empty.")

    llm = ChatGroq(
        api_key=api_key,
        model=model,
        temperature=0,
        max_retries=2,
    )
    response = llm.invoke(prompt)
    try:
        plan = json.loads(response.content)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(
            "The Groq model returned an invalid dashboard response. "
            "Check GROQ_MODEL or try another supported model."
        ) from exc
    if not isinstance(plan, dict):
        raise ValueError("LLM response must be a JSON object")
    return plan


if __name__ == "__main__":
    sample_data = Path(__file__).resolve().parents[1] / "data" / "sales_data.csv"
    result = profile_data(pd.read_csv(sample_data))
    plan = analyze_dataset("sales_data.csv", result["df"])
    print(json.dumps(plan, indent=2))
    
