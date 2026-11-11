from io import BytesIO
import json
import logging
import os
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from .charts import build_interactive_figures, compute_chart_data
from .data_loader import preprocess_dataset
from .llm import analyze_dataset

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)   



ALLOWED = {".csv", ".xls", ".xlsx"}
MAX_SIZE = 10 * 1024 * 1024
_last_df: pd.DataFrame | None = None
_last_filename: str | None = None
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


@app.get("/")
async def home():
    index_path = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    return FileResponse(index_path, media_type="text/html")


@app.post("/upload")
@app.post("/")
async def upload(file: Annotated[UploadFile, File()]):
    global _last_df, _last_filename
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(415, f"Upload one of: {', '.join(sorted(ALLOWED))}")

    contents = await file.read()
    if not contents:
        raise HTTPException(400, "File is empty")
    if len(contents) > MAX_SIZE:
        raise HTTPException(413, "File exceeds 10 MB")

    try:
        df = pd.read_csv(BytesIO(contents)) if ext == ".csv" else pd.read_excel(BytesIO(contents))
    except Exception:
        raise HTTPException(400, "Not a valid data file")

    if df.empty:
        raise HTTPException(400, "No tabular data")

    try:
        analysis = analyze_dataset(Path(file.filename).name, df)
        dashboard_data = compute_chart_data(df, analysis)
        dashboard_data["row_count"] = len(df)
        web_dashboard = build_interactive_figures(dashboard_data)
    except Exception as exc:
        logger.exception("Could not analyze uploaded file %s", file.filename)
        detail = str(exc).strip() or "No additional error details were provided."
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if api_key:
            detail = detail.replace(api_key, "[redacted]")
        raise HTTPException(
            502,
            f"Could not analyze this file ({type(exc).__name__}): {detail}",
        ) from exc

    _last_df = df
    _last_filename = Path(file.filename).name
    return {
        "filename": _last_filename,
        "analysis": analysis,
        "dashboard": web_dashboard,
    }


@app.post("/chat")
async def chat_with_data(request: ChatRequest):
    if _last_df is None:
        raise HTTPException(400, "Upload a file before asking a question")

    question = request.question.strip()
    if not question:
        raise HTTPException(422, "Question cannot be blank")

    try:
        from .agents.analyst_graph import create_analyst_graph
        from .services.llm_client import get_config, get_llm

        api_key, model_name = get_config()
    except ValueError as exc:
        raise HTTPException(503, str(exc)) from exc
    except ImportError as exc:
        missing_module = exc.name or "a required module"
        logger.exception("Data chat dependency is unavailable: %s", missing_module)
        raise HTTPException(
            503,
            f"Chat dependency '{missing_module}' is missing. "
            "Run 'python -m pip install -r requirements.txt' and restart the server.",
        ) from exc

    try:
        graph = create_analyst_graph(get_llm(api_key, model_name))
        dataframe = preprocess_dataset(_last_df)
        schema = "\n".join(
            f"- {column}: {dtype}" for column, dtype in dataframe.dtypes.items()
        )
        result = await run_in_threadpool(
            graph.invoke,
            {
                "question": question,
                "df": dataframe,
                "schema": schema,
            },
        )
    except Exception as exc:
        logger.exception("Could not answer a data chat question")
        raise HTTPException(502, "Could not answer this question. Please try again.") from exc

    try:
        result_df = result.get("result_df")
        rows = (
            json.loads(result_df.to_json(
                orient="records",
                date_format="iso",
                force_ascii=False,
            ))
            if result_df is not None
            else None
        )
        intent = result.get("intent")
        answer = result.get("answer")
        if intent == "table":
            answer = "Here are the query results."
        elif not answer:
            answer = "No answer was generated."

        return {
            "answer": answer,
            "sql": result.get("sql"),
            "rows": rows,
            "truncated": result.get("truncated", False),
            "filename": _last_filename,
        }
    except Exception as exc:
        logger.exception("Could not serialize data chat response")
        raise HTTPException(
            502,
            "Could not format the answer. Please try asking a different question.",
        ) from exc


@app.get("/data")
async def get_data():
    if _last_df is None:
        raise HTTPException(400, "Upload a file first")
    return _last_df.to_dict(orient="records")  # list of row objects