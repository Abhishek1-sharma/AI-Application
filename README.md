# AI-First CRM HCP Module - Log Interaction Screen

Round 1 technical assignment implementation for an AI-first Customer Relationship Management system focused on Healthcare Professional interaction logging.

The project includes:

- React frontend with Redux state management
- Python FastAPI backend
- LangGraph AI agent orchestration
- Groq LLM integration using `gemma2-9b-it`
- SQL persistence with Postgres/MySQL support through SQLAlchemy
- A dual-mode Log Interaction screen: structured form and conversational chat
- Seven sales-focused LangGraph tools, including the required Log Interaction and Edit Interaction tools

Extra reviewer files:

- `docs/ARCHITECTURE.md` maps each assignment requirement to the implementation.
- `docs/API_EXAMPLES.md` gives curl commands for backend demos.
- `docs/schema.sql` shows the SQL schema.
- `docs/ACCEPTANCE_CHECKLIST.md` gives the final submission checklist.

## Product Understanding

Field representatives need to record HCP engagements quickly while preserving compliant, structured CRM data. This implementation lets the rep either complete a structured form or write naturally in chat. The LangGraph agent routes the request to the correct tool, enriches interaction notes with LLM summarization and entity extraction, checks compliance-sensitive language, and helps the rep decide the next best action.

## LangGraph Agent Tools

The backend exposes these tools through `backend/app/services/agent.py`:

1. `log_interaction`
   Captures HCP, channel, product, objective, notes, commitments, next steps, and follow-up data. The LLM creates a summary, sentiment, extracted entities, and compliance flags before the record is saved.

2. `edit_interaction`
   Updates an existing interaction. If notes or product details change, the AI-generated summary, sentiment, entities, and compliance flags are refreshed.

3. `suggest_next_best_action`
   Recommends the best next sales action using HCP profile, interaction history, sentiment, and prior commitments.

4. `schedule_follow_up`
   Creates a follow-up plan with due date, preferred channel, HCP, and purpose.

5. `retrieve_hcp_profile`
   Retrieves specialty, territory, segment, preferred channel, and recent interaction context.

6. `check_compliance`
   Reviews notes for sensitive words such as off-label, guarantees, gifts, or cash-like language.

7. `summarize_history`
   Summarizes recent HCP interactions for pre-call planning.

## Project Structure

```text
.
├── backend
│   ├── app
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── services
│   │       ├── agent.py
│   │       ├── llm.py
│   │       └── tools.py
│   ├── requirements.txt
│   └── .env.example
├── frontend
│   ├── src
│   │   ├── App.jsx
│   │   ├── store.js
│   │   └── styles.css
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Run With Postgres

Start Postgres:

```bash
docker compose up -d db
```

Create backend environment:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env` and add your Groq key:

```text
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=gemma2-9b-it
DATABASE_URL=postgresql+psycopg://crm_user:crm_password@localhost:5432/hcp_crm
```

Run backend:

```bash
uvicorn app.main:app --reload
```

Run frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

Backend API docs:

```text
http://localhost:8000/docs
```

## Verify Before Submission

Run backend tests:

```bash
cd backend
.venv\Scripts\activate
pytest
```

Run frontend production build:

```bash
cd frontend
npm run build
```

The repository also includes GitHub Actions CI in `.github/workflows/ci.yml`.

## MySQL Option

Use a MySQL connection string in `backend/.env`:

```text
DATABASE_URL=mysql+pymysql://crm_user:crm_password@localhost:3306/hcp_crm
```

## Demo Notes For The 10-15 Minute Video

1. Start with the task summary:
   "This is an AI-first CRM HCP Log Interaction module for field representatives. It supports structured logging and conversational logging, then uses LangGraph and Groq to enrich the CRM data."

2. Show the frontend:
   Select an HCP, fill the structured form, and click Log Interaction. Point out the HCP profile panel, recent interactions, and AI output.

3. Show conversational logging:
   Switch to Conversational mode, type a natural interaction note, and submit it. Explain that the backend routes it through the LangGraph agent.

4. Demo editing:
   In Recent Interactions, click Edit, update notes, and click Update Interaction. Explain this uses the required Edit Interaction flow.

5. Demo five tools:
   Use Demo All Tools or click `log_interaction`, `edit_interaction`, `suggest_next_best_action`, `schedule_follow_up`, and `check_compliance`. You can also show `retrieve_hcp_profile` and `summarize_history`.

6. Explain the code:
   `frontend/src/App.jsx` is the main screen, `frontend/src/store.js` handles Redux state and API calls, `backend/app/main.py` exposes FastAPI routes, `backend/app/services/agent.py` defines the LangGraph graph, and `backend/app/services/tools.py` contains the tool logic.

7. Close with:
   "The system is designed for life-science field reps: fast capture, compliant notes, AI summarization, next-best action planning, and structured CRM persistence."

## Submission Checklist

- Push this full folder to one GitHub repository.
- Add your Groq API key only in local `.env`; do not commit the real key.
- Run the final demo with Postgres using `docker compose up -d db`.
- Record the 10-15 minute walkthrough.
- Submit the GitHub repo link and video through the Google Form:
  `https://forms.gle/XdvLNBJkbdVDGADM8`
