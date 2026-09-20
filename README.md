# Copy Editing Assistant

An internal training assistant for a journal copy-editing team. Trainees ask editorial questions (for example about author names, affiliations and corresponding authors), and the assistant will eventually find the relevant approved rule, give a clear decision, explain why, and say when a query must go to a lead.

**This is Stage 1: the project foundation only.** There is no AI yet. The app can store questions, feedback and rules, and show the draft rules.

## 1. Architecture

```
copy-editing-assistant/
├── frontend/            Next.js + TypeScript (user interface only)
│   ├── app/             Pages: / (ask a question), /rules (draft rules)
│   ├── components/      QuestionForm, RuleList
│   ├── lib/api.ts       The only place that talks to the backend
│   └── types/           TypeScript types matching the API
├── backend/             Python + FastAPI (all logic and data access)
│   ├── app/
│   │   ├── main.py      App creation, CORS, router registration
│   │   ├── config.py    All settings (reads .env)
│   │   ├── database.py  SQLAlchemy engine/session
│   │   ├── models/      Database tables: Rule, Example, Question, Feedback
│   │   ├── schemas/     Pydantic request/response models
│   │   ├── routes/      HTTP endpoints (thin)
│   │   ├── services/    Database logic (rules, questions, seeding)
│   │   └── seed.py      Command to create tables and load seed rules
│   └── tests/           Automated API tests
└── data/
    └── seed/rules.json  The 20 initial draft rules
```

The five concerns are kept apart: editorial knowledge lives in the database (seeded from `data/seed/`), question handling is in `services/question_service.py`, the UI is in `frontend/`, and the places for decision logic and LLM integration are reserved for later stages (no editorial rules are hard-coded in the frontend).

## 2. Prerequisites

- Python 3.11+ (tested with 3.12)
- Node.js 20+ and npm (tested with Node 22)
- Git

## 3. Install and run

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # optional; defaults work without it
python -m app.seed                # create the SQLite database and load the 20 rules
uvicorn app.main:app --reload --port 8000
```

- API docs (interactive): http://localhost:8000/docs
- The database file is created at `data/copy_editing.db` unless you set `DATABASE_URL` in `backend/.env`.

### Frontend (in a second terminal)

```bash
cd frontend
npm install
cp .env.example .env.local        # points the frontend at http://localhost:8000
npm run dev
```

Open http://localhost:3000.

### Seeding the database

```bash
cd backend && source venv/bin/activate
python -m app.seed             # safe to repeat: only missing rules are inserted
python -m app.seed --reset     # WARNING: deletes all data (questions, feedback) first
```

### Tests

```bash
cd backend && source venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q            # uses a temporary database, not your real one
```

## 4. API endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Returns `{"status": "ok"}` |
| GET | `/rules` | List rules (optional `?category=` and `?status=`) |
| GET | `/rules/{rule_id}` | One rule by numeric id (404 if missing) |
| POST | `/questions` | Save a question. Body: `{"question_text": "...", "category": null}`. Returns 201 |
| GET | `/questions` | List saved questions, newest first (`?limit=` `?offset=`) |
| POST | `/feedback` | Save feedback. Body: `{"question_id": 1, "rating": 1-5, "trainee_comment": "...", "lead_correction": "..."}`. 404 if the question does not exist |
| GET | `/examples/{rule_id}` | Examples for a rule (404 if the rule does not exist) |

Example:

```bash
curl -X POST http://localhost:8000/questions \
  -H "Content-Type: application/json" \
  -d '{"question_text": "How do I tag a nickname?"}'
```

## 5. Current limitations

- **No AI.** `POST /questions` only saves the question; `matched_rule_id` stays empty.
- **All 20 rules are drafts** (`source = "Initial team guidance"`, `status = "draft"`). They are not confirmed against the official style manual. Only the fields provided by the team are filled: `action`, `exception`, `question_pattern` and `source_section` are empty. `escalation` is filled only where the rule text itself says to raise a query (AUTHOR-002, 004, 010, 016).
- AUTHOR-018 (more than two family names) needs clarification from the team; its wording is stored exactly as supplied.
- **No examples yet.** The `examples` table exists but is empty, so `GET /examples/{rule_id}` returns `[]`.
- No authentication, no pagination on `/rules`, no admin screen for editing rules.
- No database migrations: tables are created with `create_all`. If you change a model, delete `data/copy_editing.db` and re-seed (or add Alembic later).
- SQLite drops time zone information, so timestamps are returned without one; they are stored in UTC.

## 6. Planned next stages

1. Question understanding and rule retrieval (find the most relevant rule for a question).
2. Decision logic with structured answers (decision, action, reason, example, "raise a query" flag), never inventing a rule when none matches.
3. LLM integration for clear explanations (`LLM_API_KEY` is already reserved in `backend/.env.example`).
4. Import of the official style manual as the primary source of truth; promote confirmed rules from `draft`.
5. Lead review screen for feedback and corrections.
