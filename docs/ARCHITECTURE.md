# AI-First CRM HCP Module Architecture

## Assignment Mapping

| Requirement | Implementation |
| --- | --- |
| Log Interaction Screen | `frontend/src/App.jsx` |
| Structured form logging | Structured tab in the React UI |
| Conversational chat logging | Conversational tab, `/api/agent/chat` |
| React UI | Vite + React |
| Redux state management | `frontend/src/store.js` |
| Python backend | FastAPI in `backend/app/main.py` |
| LangGraph mandatory | `backend/app/services/agent.py` |
| LLM mandatory | Groq `gemma2-9b-it` in `backend/app/services/llm.py` |
| SQL database | SQLAlchemy models in `backend/app/models.py` |
| MySQL/Postgres | Controlled by `DATABASE_URL`; Postgres compose included |
| Google Inter font | Loaded in `frontend/index.html` |
| Minimum 5 tools | Seven tools implemented |

## Key Components

### Frontend

The frontend is a CRM work screen for field representatives. It includes:

- HCP selector and profile context
- Structured interaction form
- Conversational interaction capture
- LangGraph tool demo panel
- AI output panel
- Agent trace panel
- Recent interaction history

Redux owns HCPs, interactions, agent tools, agent runs, selected HCP, current mode, chat messages, and save state.

### Backend

FastAPI exposes:

- HCP list
- Interaction create/update/list
- Agent chat endpoint
- Agent tool metadata
- Agent demo endpoint
- Agent run history

SQLAlchemy stores HCPs, interactions, and agent run logs.

### LangGraph Agent

The LangGraph agent has two nodes:

1. `router`
   Uses Groq `gemma2-9b-it` to select the correct tool for the user message. If the Groq API key is not configured, it uses deterministic fallback routing.

2. `execute_tool`
   Runs the selected CRM tool, persists tool output, and returns the result to the frontend.

This keeps the agent explicit and demo-friendly while still satisfying the AI-first requirement.

### LLM Responsibilities

Groq `gemma2-9b-it` is used for:

- Tool/intent selection
- Conversational note to structured CRM payload extraction
- Interaction summarization
- Sentiment detection
- Entity extraction
- Compliance flag detection

The fallback exists only so the demo can still run without leaking or depending on a real API key.

## LangGraph Tools

1. `log_interaction`
2. `edit_interaction`
3. `suggest_next_best_action`
4. `schedule_follow_up`
5. `retrieve_hcp_profile`
6. `check_compliance`
7. `summarize_history`

## Database Entities

### HCP

Stores name, specialty, territory, segment, preferred channel, and last contact date.

### Interaction

Stores structured field-rep notes, AI summary, sentiment, commitments, next steps, entities, and compliance flags.

### AgentRun

Stores each LangGraph tool execution, selected tool, input message, and result for traceability.
