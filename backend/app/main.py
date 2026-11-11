from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import SessionLocal, init_db
from app.routes import auth, documents, feedback, health, questions, rules
from app.services.auth_service import ensure_default_users


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()  # make sure tables exist even if the seed script was not run
    with SessionLocal() as db:
        created = ensure_default_users(db)  # only when there are no users at all
    if created:
        print(
            f"Created default accounts: {', '.join(created)}. "
            "Change their passwords: python -m app.users set-password <username>"
        )
    yield


app = FastAPI(title="Copy Editing Assistant API", version="0.4.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(rules.router)
app.include_router(questions.router)
app.include_router(feedback.router)
app.include_router(documents.router)
