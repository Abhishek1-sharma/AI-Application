# Video Recording Script

Use this as a speaking guide for a 10-15 minute submission video.

## 1. Task Understanding

This assignment asks for an AI-first CRM HCP module. The key screen is Log Interaction. A life-science field representative should be able to record HCP interactions either through a structured form or through a conversational chat interface.

The mandatory technical pieces are React, Redux, FastAPI, LangGraph, Groq `gemma2-9b-it`, and a SQL database.

## 2. Frontend Walkthrough

Show the HCP selector, profile summary, structured logging form, conversational logging tab, AI output panel, recent interactions list, and agent tool demo buttons.

## 3. LangGraph Tool Demo

Click and explain at least these five tools:

- `log_interaction`
- `edit_interaction`
- `suggest_next_best_action`
- `schedule_follow_up`
- `check_compliance`

Then optionally show:

- `retrieve_hcp_profile`
- `summarize_history`

## 4. Code Structure

Explain:

- `backend/app/main.py`: FastAPI routes
- `backend/app/models.py`: SQL tables for HCPs, interactions, and agent runs
- `backend/app/services/agent.py`: LangGraph graph and tool routing
- `backend/app/services/tools.py`: business logic for all tools
- `backend/app/services/llm.py`: Groq integration and fallback analysis
- `frontend/src/App.jsx`: Log Interaction screen
- `frontend/src/store.js`: Redux state and API calls

## 5. Closing Summary

This project helps reps log interactions faster, preserve structured CRM data, generate AI summaries, identify compliance risks, and plan the next best sales action.
