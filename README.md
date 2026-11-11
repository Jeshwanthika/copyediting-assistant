# Redline — Copy editing virtual assistant

To rename the app, edit `frontend/lib/brand.ts` (name, logo letters, tagline).

An internal training assistant for a journal copy-editing team. Trainees ask editorial questions (for example about author names, affiliations and corresponding authors), and the assistant will eventually find the relevant approved rule, give a clear decision, explain why, and say when a query must go to a lead.

**This is Stage 4: logins, roles and the Errors & solutions library (on top of the Stage 3 rule review workflow).** Everyone signs in. Leads/admins maintain rules, the knowledge base and the PDF library; trainees can read rules and PDFs and ask questions, nothing else. The UI uses a charcoal / red / white theme.

Stage 3 recap: There is still no AI/LLM. Leads can now review each rule, see what is missing, complete it and change its status. A trainee's question is matched to one of the stored rules with a simple, deterministic keyword-scoring engine. The answer is built only from the stored rule; if no rule fits (or several fit equally well), the app says so instead of guessing.

## 1. Architecture

```
copy-editing-assistant/
├── frontend/            Next.js + TypeScript (user interface only)
│   ├── app/             Pages: /login, / (ask a question), /rules (style manual), /faqs,
│   │                    /review (knowledge base, leads only), /errors-solutions (PDF library)
│   ├── components/      AppShell, AuthProvider (login state + LeadOnly guard), ErrorsSolutions,
│   │                    QuestionForm, AnswerCard, ReviewDashboard, RuleEditor, ExampleManager, StatusBadge
│   ├── lib/api.ts       The only place that talks to the backend (adds the login token)
│   ├── lib/session.ts   Keeps the login token in the browser
│   └── types/           TypeScript types matching the API
├── backend/             Python + FastAPI (all logic and data access)
│   ├── app/
│   │   ├── main.py      App creation, CORS, router registration
│   │   ├── config.py    All settings (reads .env)
│   │   ├── database.py  SQLAlchemy engine/session
│   │   ├── auth.py      current_user / require_lead checks used by every route
│   │   ├── users.py     Command line tool to manage login accounts
│   │   ├── models/      Database tables: Rule, Example, Question, Feedback, User, Document
│   │   ├── schemas/     Pydantic request/response models
│   │   ├── routes/      HTTP endpoints (thin)
│   │   ├── services/
│   │   │   ├── rule_engine.py     Matching and scoring (no DB, no HTTP)
│   │   │   ├── rule_keywords.py   Keyword map per rule - edit this to tune matching
│   │   │   ├── answer_builder.py  Turns a match into decision/action/reason/escalation
│   │   │   ├── rule_completeness.py  Is a rule complete enough to be used?
│   │   │   ├── rule_review_service.py  Review reports and controlled rule updates
│   │   │   ├── auth_service.py   Password hashing, login tokens, accounts
│   │   │   ├── document_service.py  Errors & solutions PDFs (stored in data/documents/)
│   │   ├── migrations.py  Upgrades databases created by an earlier stage
│   │   │   ├── question_service.py  Ties it together and saves the question
│   │   │   └── rule_service.py, seed_service.py
│   │   └── seed.py      Command to create tables and load seed rules
│   └── tests/           Automated API tests
└── data/
    ├── seed/            rules.json (the 20 initial draft rules), examples.json (team-written examples only)
    │   └── documents/   Put PDFs here to have `python -m app.seed` add them to Errors & solutions
    └── documents/       Uploaded PDFs (created automatically, not committed)
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
python -m app.seed                # create the database, load the 20 rules, create the two default logins
uvicorn app.main:app --reload --port 8000
```

**Upgrading from Stage 3?** Run `pip install -r requirements.txt` again: PDF uploads need the new `python-multipart` package, and the backend will not start without it.

**Default logins** (created the first time the backend starts with no users):

| Account | Username | Password | Can |
| --- | --- | --- | --- |
| Lead / Admin | `lead` | `lead12345` | Everything: edit rules, knowledge base, upload/edit/delete PDFs |
| Trainee | `trainee` | `trainee12345` | Ask questions, read the style manual, FAQs and PDFs |

Change these before anyone else uses the app: either set `DEFAULT_LEAD_PASSWORD` / `DEFAULT_TRAINEE_PASSWORD` in `backend/.env` **before the first start**, or afterwards run `python -m app.users set-password lead` (and `trainee`). See section 7 for adding more people.

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
python -m app.seed --update    # also update existing rules to match data/seed/rules.json (bumps their version).
                               # WARNING: overwrites edits made on the /review page for the fields in the seed file
python -m app.seed --reset     # WARNING: deletes all data (questions, feedback) first
```

### Tests

```bash
cd backend && source venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q            # uses a temporary database, not your real one
```

### Upgrading an existing database

Nothing to do. On startup the backend adds the new `rules.condition` and `feedback.feedback_type` columns to a database created by an earlier stage and keeps all existing data (see `backend/app/migrations.py`). Run `python -m app.seed` once to add the AUTHOR-009 example. Stage 4 adds the `users` and `documents` tables automatically and creates the default logins on first start.

## 4. API endpoints

Every endpoint except `/health` and `/auth/login` needs a login token: `Authorization: Bearer <access_token>`. Without one the API returns **401**; a trainee calling a lead-only endpoint gets **403**. In http://localhost:8000/docs, call `POST /auth/login`, copy `access_token` and paste it into the **Authorize** button.

**Who can call what:** *Any* = any signed-in user. *Lead* = leads/admins only.

| Method | Path | Who | Description |
| --- | --- | --- | --- |
| GET | `/health` | Open | Returns `{"status": "ok"}` |
| POST | `/auth/login` | Open | `{"username", "password"}` → `{"access_token", "expires_at", "user": {"role", ...}}`. 401 if wrong |
| GET | `/auth/me` | Any | The signed-in user |
| POST | `/auth/change-password` | Any | `{"current_password", "new_password"}` (8+ characters) |
| GET | `/documents` | Any | List Errors & solutions PDFs |
| GET | `/documents/{id}` / `/documents/{id}/file` | Any | Details / the PDF itself (inline; `?download=true` to download) |
| POST | `/documents` | Lead | Upload a PDF (multipart form: `file`, optional `title`, `description`). Only real PDFs, max 25 MB |
| PATCH | `/documents/{id}` | Lead | Change `title`, `description`, `sort_order` |
| PUT | `/documents/{id}/file` | Lead | Replace the PDF, keep the details |
| DELETE | `/documents/{id}` | Lead | Delete the PDF |

The rule, question and feedback endpoints below work as before, with these access rules: reading rules and examples, `POST /questions` and trainee `POST /feedback` → *Any*. `/rules/review`, `/rules/{id}/review`, `PATCH /rules/{id}`, all example changes, `GET /questions`, `GET /feedback` and lead corrections → *Lead*.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/rules` | List rules (optional `?category=` and `?status=`) |
| GET | `/rules/{rule_id}` | One rule by numeric id (404 if missing) |
| GET | `/rules/review` | Every rule with status, completeness and missing fields |
| GET | `/rules/{rule_id}/review` | Full review information for one rule: rule, completeness, examples, allowed status changes |
| PATCH | `/rules/{rule_id}` | Update only the allowed fields (see below). 422 if a field or status change is not allowed |
| POST | `/rules/{rule_id}/examples` | Add an example (`input_text`, `correct_output`, optional `explanation`) |
| PATCH / DELETE | `/rules/{rule_id}/examples/{example_id}` | Edit or delete an example |
| POST | `/questions` | Match the question to a rule, save it (with the matched rule), return the answer. Returns 201 |
| GET | `/questions` | List saved questions, newest first (`?limit=` `?offset=`) |
| POST | `/feedback` | Trainee feedback `{"question_id": 1, "rating": 1-5, "trainee_comment": "..."}` or a lead correction `{"question_id": 1, "feedback_type": "lead_correction", "lead_correction": "..."}` (no rating). 404 if the question does not exist |
| GET | `/feedback` | List feedback (`?feedback_type=` `?question_id=`) |
| GET | `/examples/{rule_id}` | Examples for a rule (404 if the rule does not exist) |

### POST /questions

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" \
  -d '{"username": "trainee", "password": "trainee12345"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8000/questions \
  -H "Authorization: Bearer $TOKEN" \
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
    "status_notice": "Draft team guidance \u2014 not yet confirmed against the official style manual.",
    "rule_complete": true,
    "missing_fields": [],
    "incomplete_notice": null,
    "condition": null,
    "exception": null,
    "examples": [
      {"input_text": "Can I reorder the authors?",
       "correct_output": "Do not change the author order without author approval.",
       "explanation": "Author order should not be changed without approval."}
    ],
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

**Escalation.** A matched, complete rule with a non-empty `escalation` field gives `escalation_required = true` with that text as the reason; a complete rule with none gives `false`. `no_match`, `ambiguous` and matches to an **incomplete** rule always give `true`, because the system cannot give confident guidance.

**Decision vs action.** `decision` is the stored `rule_text`, unchanged. `action` is the rule's `action` field. When a rule has no action stored it is incomplete, and the trainee is told to check the style manual or raise the question with a lead (see section 6). Nothing is invented.

**Tuning.** To improve matching, add phrases to `RULE_TERMS` in `rule_keywords.py` and add a test case. A rule with no entry there still matches on its topic.

### Known overlaps (documented, not resolved)

These pairs of draft rules overlap, so some questions are deliberately reported as ambiguous. Their wording has not been changed.

- AUTHOR-003 and AUTHOR-007 (particle names): "Is 'van der' a particle name?"
- AUTHOR-004 and AUTHOR-005 (corresponding authors and their emails)
- AUTHOR-001, AUTHOR-014 and AUTHOR-018 (name structure)
- AUTHOR-010 and AUTHOR-016 (corresponding author details): "The corresponding author's affiliation ID is missing"

## 6. Rule review workflow (leads)

Sign in as a lead and open **Knowledge base** in the sidebar (http://localhost:3000/review). Trainees do not see this item, and the page and its API refuse them. In the **Style manual**, leads also get an **Edit rule** button on each rule that opens it here. It lists every rule with its status, whether it is complete, and what is missing. Click a rule to edit it, add examples, and change its status.

**Statuses**

| Status | Meaning | Shown to trainees as |
| --- | --- | --- |
| `draft` | Initial team guidance, not confirmed | "Draft team guidance — not yet confirmed against the official style manual." |
| `reviewed` | A lead has checked the content, but not against the official style manual | "Reviewed team guidance — checked by a lead, but not yet confirmed..." |
| `confirmed` | A lead has explicitly confirmed it against the official style manual | "Confirmed guidance." |
| `superseded` | Replaced by newer guidance. Never used to answer questions | — |

All 20 rules are `draft` (including AUTHOR-009). **Nothing is ever promoted automatically.** Only an explicit `PATCH` changes a status, and only along these paths: `draft → reviewed → confirmed`, plus `reviewed → draft`, `confirmed → draft` (reopen) and `→ superseded`. A rule cannot jump from `draft` to `confirmed`, and an **incomplete rule cannot be confirmed**.

**Completeness.** A rule is *complete* when `rule_text`, `action`, `source` and `status` are all filled in. Also reported, but not required: condition, exception, escalation, source section and examples (some rules legitimately have none). `GET /rules/review` returns, for example, `{"rule_code": "AUTHOR-001", "complete": false, "missing_fields": ["action"], ...}`. Right now only AUTHOR-009 is complete; the other 19 are missing an action.

**What PATCH /rules/{id} can change:** `condition`, `rule_text`, `action`, `exception`, `escalation`, `source`, `source_section`, `status`, `version`. Any other field (`rule_code`, `topic`, `id`, timestamps, ...) is rejected with a 422. Sending an empty string clears an optional field; `rule_text` and `source` can never be blank. Two safety rules apply:
- Editing the **content** (condition, rule text, action, exception, escalation) of a `reviewed` or `confirmed` rule, without explicitly changing its status, sends the rule back to `draft`, because the review no longer applies to what it says.
- If the content changed and no `version` was sent, the version goes up by one.

**Incomplete rules in trainee answers.** If a question matches a rule that is incomplete, the trainee sees "Guidance found, but this rule is incomplete.", the recorded rule text, and the action "Check the style manual or raise the question with a lead." Escalation is required. The missing action is never filled in. Examples are shown when a rule has them, otherwise "No example has been added yet."

**Examples.** Stored in the existing `examples` table; a rule can have several. Only the AUTHOR-009 example you supplied is seeded (`data/seed/examples.json`).

**Feedback.** Each row has a `feedback_type`: `trainee_feedback` (needs a rating) or `lead_correction` (needs the correction text, no rating). The API rejects mixtures of the two.

## 7. Logins, roles and Errors & solutions

**Two kinds of account.** The sign-in page has a **Lead / Admin** tab and a **Trainee** tab; you must pick the tab that matches your account.

| | Lead / Admin | Trainee (and other staff) |
| --- | --- | --- |
| AI assistant, Style manual, FAQs | Yes | Yes |
| Edit rules, add examples, change status | Yes | No |
| Knowledge base (sidebar item and page) | Yes | Hidden |
| Errors & solutions: read the PDFs | Yes | Yes |
| Errors & solutions: upload, rename, replace, delete | Yes | No |

The frontend hides what a trainee cannot use, but the **backend enforces every rule** (401/403), so editing the browser's storage or calling the API directly does not get around it.

**Managing accounts** (from `backend/`, venv active). Passwords are typed in, never put on the command line:

```bash
python -m app.users list
python -m app.users create priya --role trainee --name "Priya Sharma"
python -m app.users create arun --role lead --name "Arun Kumar"
python -m app.users set-password priya
python -m app.users set-role priya lead     # takes effect at their next sign-in
python -m app.users disable priya           # or: enable
```

Passwords are stored as salted PBKDF2-SHA256 hashes. A login lasts `AUTH_TOKEN_HOURS` (12 by default). Tokens are signed with `AUTH_SECRET_KEY`; if that is empty, a random key is generated once and kept in `data/.auth_secret`. Deleting that file or changing the key signs everybody out.

**Errors & solutions.** The sidebar item sits below Knowledge base. It lists the PDFs as cards; clicking one opens it inside the app in the browser's own PDF viewer (zoom, search and print work), with **New tab** and **Download** buttons. There are two ways to add the PDFs:

1. **In the app:** sign in as a lead → Errors & solutions → **Upload PDF**. Give it a title and optional description. **Edit** on a card lets a lead rename it, replace the PDF or delete it.
2. **From a folder:** copy the PDFs into `data/seed/documents/` and run `python -m app.seed`. The title comes from the file name (`author_name_errors.pdf` → "Author name errors"). Running it again does not add the same file twice.

Uploaded files are stored in `data/documents/` (or `DOCUMENTS_DIR`). Back this folder up together with the database.

## 8. Current limitations

- **Accounts are managed from the command line.** There is no user admin page yet, no self-service password reset and no sign-in rate limiting. Serve the app over HTTPS before using it outside a trusted network, because passwords and tokens are sent with every request.
- The login token is kept in the browser's localStorage. Anyone with access to the signed-in browser can use the app until they sign out or the token expires.
- **Keyword matching, not understanding.** Questions worded very differently from the keyword list return "no matching rule" (for example "the author only gave a surname"). That is the intended safe behaviour, and the fix is to add keywords.
- **A match is not a guarantee the rule answers the question.** For "How many email addresses can the corresponding author have?" the closest rule is AUTHOR-005, which does not state a limit.
- **19 of 20 rules are incomplete** (no action), so most trainee answers currently say the rule is incomplete. That is expected until the team fills in the actions.
- **Confirming is not verified.** The system checks completeness, not whether the text really matches the style manual. Confirmed means a lead said so.
- AUTHOR-018 (more than two family names) still needs clarification from the team.
- The reason text is a template ("matches rule X on the words..."); real explanations come with the LLM stage.
- No pagination, no change history for rules (only `version` and `updated_at`), no migrations tool beyond the small upgrade step in `migrations.py`.
- SQLite drops time zone information, so timestamps are returned without one; they are stored in UTC.

## 9. Planned next stages

1. Have the team complete the 19 missing actions (and exceptions/examples) through the review page.
2. Use saved questions with no matched rule, and lead corrections, to grow the keyword list.
3. LLM integration for clear explanations of an already-matched, complete rule (`LLM_API_KEY` is reserved in `backend/.env.example`). The rule engine stays the source of truth.
4. Import of the official style manual as the primary source of truth.
5. Change history for rules (who changed what), a user-management page for leads, and moving the Raised Queries page from browser storage to the backend.
