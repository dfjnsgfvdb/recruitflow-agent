from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import agent, candidates, confirmations, dashboard, data_quality, events, interviews, resumes, sync_logs, tasks
from app.core.config import settings
from app.db import models  # noqa: F401  # 确保 ORM 模型注册到 Base.metadata
from app.db.database import Base, engine
from app.db.schema_migrations import ensure_resume_schema

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent.router)
app.include_router(candidates.router)
app.include_router(interviews.router)
app.include_router(events.router)
app.include_router(dashboard.router)
app.include_router(confirmations.router, prefix="/api/confirmations", tags=["confirmations"])
app.include_router(tasks.router)
app.include_router(sync_logs.router)
app.include_router(data_quality.router)
app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])


@app.on_event("startup")
def on_startup() -> None:
    # Demo 阶段启动即自动建表，生产环境建议改为 Alembic 管理迁移。
    Base.metadata.create_all(bind=engine)
    ensure_resume_schema(engine)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "app": settings.app_name}
