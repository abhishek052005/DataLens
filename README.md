# AI Dashboard
live https://datalens-qvk4.onrender.com/
## Project layout

```text
.
|-- backend/
|   |-- agents/       # LangGraph analyst
|   |-- chains/       # Intent, SQL, and answer prompts
|   |-- services/     # LLM client and guarded query execution
|   |-- app.py        # FastAPI API
|-- data/             # Local datasets; ignored by Git
|-- docs/architecture/ # Architecture diagram
|-- frontend/
|   `-- index.html    # Browser dashboard and data chat
|-- legacy/           # Unused UI fragments retained for reference
|-- app.py            # ASGI launcher
|-- .env.example      # Environment variable template
`-- requirements.txt
```

`backend/dashboard.py` contains the static image renderer; `backend/charts.py` builds the interactive dashboard charts.

## Run locally

Install dependencies, copy `.env.example` to `.env`, and set your `GROQ_API_KEY`. The dashboard uses `openai/gpt-oss-120b` by default; set `GROQ_MODEL` to another Groq-supported model if needed. Start the FastAPI dashboard with:

```powershell
pip install -r requirements.txt
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000`, upload a CSV or Excel file, then choose **Chat on data** to ask questions about that upload.
