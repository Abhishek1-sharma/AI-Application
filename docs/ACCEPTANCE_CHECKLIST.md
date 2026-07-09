# Acceptance Checklist

Use this before pushing to GitHub and recording the video.

## Mandatory Technical Stack

- React UI: `frontend/src/App.jsx`
- Redux state management: `frontend/src/store.js`
- FastAPI backend: `backend/app/main.py`
- LangGraph framework: `backend/app/services/agent.py`
- LLM integration: `backend/app/services/llm.py`
- Groq model: `gemma2-9b-it` configured by `GROQ_MODEL`
- Postgres SQL: `docker-compose.yml` and `DATABASE_URL`
- MySQL optional support: `mysql+pymysql://...` connection string in README
- Google Inter font: `frontend/index.html`

## Required Functional Flow

- Structured logging: Structured tab in the main UI
- Conversational logging: Conversational tab in the main UI
- Log Interaction tool: `log_interaction` LangGraph node
- Edit Interaction tool: recent interaction Edit button and `edit_interaction` LangGraph node
- Minimum 5 tools: 7 tools are implemented
- Tool demo: Agent Tools panel and Demo All Tools button
- AI enrichment: summary, sentiment, entities, compliance flags
- Agent traceability: Agent Trace panel and `/api/agent/runs`

## Video Recording Flow

1. Show README and explain the task.
2. Show `docker compose up -d db`.
3. Start FastAPI and React.
4. Open the UI and select an HCP.
5. Log an interaction through the structured form.
6. Edit the interaction from Recent Interactions.
7. Switch to Conversational and submit a natural language note.
8. Click Demo All Tools and show Agent Trace.
9. Show `/docs` FastAPI Swagger briefly.
10. Explain the main files and LangGraph nodes.

## Do Not Submit Without

- Real `GROQ_API_KEY` present locally in `backend/.env`
- Postgres running for the recorded demo
- GitHub repository contains frontend, backend, docs, README, and docker-compose
- Real API key is not committed
- Video shows at least 5 tools working
