# Backend

FastAPI service for the AI-first CRM HCP Log Interaction module.

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Set `GROQ_API_KEY` in `.env` to use Groq `gemma2-9b-it`. Without a key, the app uses a deterministic local fallback so the demo still works.
