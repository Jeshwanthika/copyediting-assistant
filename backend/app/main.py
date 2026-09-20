from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routes import feedback, health, questions, rules


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()  # make sure tables exist even if the seed script was not run
    yield


app = FastAPI(title="Copy Editing Assistant API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(rules.router)
app.include_router(questions.router)
app.include_router(feedback.router)
