# Copy Editing Assistant

An internal training assistant for a journal copy-editing team. Trainees ask editorial questions (for example about author names, affiliations and corresponding authors), and the assistant will eventually find the relevant approved rule, give a clear decision, explain why, and say when a query must go to a lead.

**This is Stage 2: rule engine + question matching.** There is still no AI/LLM. A trainee's question is matched to one of the stored rules with a simple, deterministic keyword-scoring engine. The answer is built only from the stored rule; if no rule fits (or several fit equally well), the app says so instead of guessing.

## 1. Architecture

```
copy-editing-assistant/
├── frontend/            Next.js + TypeScript (user interface only)
│   ├── app/             Pages: / (ask a question), /rules (draft rules)
│   ├── components/      QuestionForm, AnswerCard, RuleList
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
│   │   ├── services/
│   │   │   ├── rule_engine.py     Matching and scoring (no DB, no HTTP)
│   │   │   ├── rule_keywords.py   Keyword map per rule - edit this to tune matching
│   │   │   ├── answer_builder.py  Turns a match into decision/action/reason/escalation
│   │   │   ├── question_service.py  Ties it together and saves the question
│   │   │   └── rule_service.py, seed_service.py
│   │   └── seed.py      Command to create tables and load seed rules
│   └── tests/           Automated API tests
└── data/
    └── seed/rules.json  The 20 initial draft rules
```

Request flow: `routes → question_service → rule_engine + answer_builder → database`. The route contains no matching logic.

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
python -m app.seed --update    # also update existing rules to match data/seed/rules.json (bumps their version)
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
| POST | `/questions` | Match the question to a rule, save it (with the matched rule), return the answer. Returns 201 |
| GET | `/questions` | List saved questions, newest first (`?limit=` `?offset=`) |
| POST | `/feedback` | Save feedback. Body: `{"question_id": 1, "rating": 1-5, "trainee_comment": "...", "lead_correction": "..."}`. 404 if the question does not exist |
| GET | `/examples/{rule_id}` | Examples for a rule (404 if the rule does not exist) |

### POST /questions

```bash
curl -X POST http://localhost:8000/questions \
  -H "Content-Type: application/json" \
  -d '{"question_text": "Can I change the order of authors?"}'
```

```json
{
  "id": 4, "question_id": 4,
  "question_text": "Can I change the order of authors?",
  "category": "Author", "matched_rule_id": 9, "created_at": "2026-09-20T14:56:28",
  "matched_rule": {"rule_id": 9, "rule_code": "AUTHOR-009", "topic": "Author order", "version": 2},
  "answer": {
    "matched": true,
    "match_status": "matched",
    "decision": "Do not change the author order without author approval.",
    "action": "Keep the supplied author order. If a change is requested, obtain author approval before changing it.",
    "reason": "Your question matches rule AUTHOR-009 (Author order) on the words: \u201corder of authors\u201d.",
    "rule_code": "AUTHOR-009", "rule_topic": "Author order",
    "source": "Initial team guidance", "status": "draft",
    "status_notice": "This is draft internal team guidance. It has not yet been confirmed against the official style manual.",
    "exception": null,
    "confidence": 0.75,
    "matched_terms": ["order of authors"],
    "escalation_required": true,
    "escalation_reason": "The matched rule requires a query/lead confirmation: If author approval is needed.",
    "candidates": []
  }
}
```

`match_status` is one of `matched`, `no_match` or `ambiguous`. For the last two, `matched` is `false`, `matched_rule` is `null`, `escalation_required` is `true`, and (for `ambiguous`) `candidates` lists the rules that could apply. The original Stage 1 fields (`id`, `question_text`, `category`, `matched_rule_id`, `created_at`) are still returned.

## 5. How rule matching works

The matching code is `backend/app/services/rule_engine.py`; the keywords are in `backend/app/services/rule_keywords.py`.

1. **Normalise** the question: lower case, punctuation removed, `the/a/an` removed, plurals folded (`Emails` = `email`, `IDs` = `id`).
2. **Score every rule.** Terms found in the question add to that rule's score:

   | Term | Weight |
   | --- | --- |
   | The rule's own topic (from the database) | 1.0 |
   | A *strong* keyword phrase, or an *all_of* group (all parts present anywhere) | 0.75 |
   | A *weak* keyword | 0.15 each, capped at 0.3 in total |

   Weak keywords can never trigger a match on their own; they only add confidence. A phrase is ignored when another rule matched a longer phrase containing it (`common particle names` beats `particle names`), and the same words are never counted twice for one rule.
3. **Decide.**
   - Best score below `0.5` → `no_match`.
   - Runner-up also `>= 0.5` and at least 70% of the best score → `ambiguous` (the app does not choose).
   - Otherwise → `matched`. Confidence is the score capped at 0.95 (High >= 90%, Medium >= 70%).

The thresholds are constants at the top of `rule_engine.py`.

**Escalation.** A matched rule with a non-empty `escalation` field gives `escalation_required = true` with that text as the reason; a matched rule with none gives `false`. `no_match` and `ambiguous` always give `true`, because the system itself cannot identify a rule.

**Decision vs action.** `decision` is the stored `rule_text`, unchanged. `action` is the rule's `action` field; when a rule has none stored, a generic "apply this rule as written, or check the style manual / raise a query" is used. Nothing is invented.

**Tuning.** To improve matching, add phrases to `RULE_TERMS` in `rule_keywords.py` and add a test case. A rule with no entry there still matches on its topic.

### Known overlaps (documented, not resolved)

These pairs of draft rules overlap, so some questions are deliberately reported as ambiguous. Their wording has not been changed.

- AUTHOR-003 and AUTHOR-007 (particle names): "Is 'van der' a particle name?"
- AUTHOR-004 and AUTHOR-005 (corresponding authors and their emails)
- AUTHOR-001, AUTHOR-014 and AUTHOR-018 (name structure)
- AUTHOR-010 and AUTHOR-016 (corresponding author details): "The corresponding author's affiliation ID is missing"

## 6. Current limitations

- **Keyword matching, not understanding.** Questions worded very differently from the keyword list return "no matching rule" (for example "the author only gave a surname"). That is the intended safe behaviour, and the fix is to add keywords.
- **A match is not a guarantee the rule answers the question.** For "How many email addresses can the corresponding author have?" the closest rule is AUTHOR-005, which does not state a limit. The trainee sees the rule as written.
- **All 20 rules are drafts** (`source = "Initial team guidance"`, `status = "draft"`), not confirmed against the official style manual. Every matched answer shows a draft notice.
- **Only AUTHOR-009 has an `action` stored** (it came from your Stage 2 example). The other 19 use the generic action until the team supplies real ones. `escalation` is filled for AUTHOR-002, 004, 009, 010 and 016.
- AUTHOR-018 (more than two family names) still needs clarification from the team.
- The reason text is a template ("matches rule X on the words..."); real explanations come with the LLM stage.
- **No examples yet.** The `examples` table is empty.
- No authentication, no pagination on `/rules`, no admin screen for editing rules.
- No database migrations: tables are created with `create_all`.
- SQLite drops time zone information, so timestamps are returned without one; they are stored in UTC.

## 7. Planned next stages

1. Use the saved questions with no matched rule to grow the keyword list and add tests.
2. Fill `action`, `exception` and examples for each rule with the team.
3. LLM integration for clear explanations of an already-matched rule (`LLM_API_KEY` is reserved in `backend/.env.example`). The rule engine stays the source of truth.
4. Import of the official style manual as the primary source of truth; promote confirmed rules from `draft`.
5. Lead review screen for feedback and corrections.
