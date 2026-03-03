"""
FastAPI application entry point — all routes registered here.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import auth, chat, contratos, dashboard, historico, metas, perfil, transacoes
from app.core.config import settings
from app.core.database import check_connection, engine

# Import all models so Base.metadata.create_all() picks them up
import app.models  # noqa: F401
from app.models.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if not check_connection():
        raise RuntimeError("❌ Falha na conexão com o banco de dados. Verifique o .env e se o banco está rodando.")

    # Create all tables that don't exist yet
    Base.metadata.create_all(bind=engine)

    print("✅ Conexão com PostgreSQL estabelecida. Tabelas sincronizadas.")
    yield
    print("🛑 Servidor encerrado.")


app = FastAPI(
    title="GestãoFinanceira API",
    description="Backend do sistema de gestão financeira pessoal com IA integrada.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # allow_origins=settings.CORS_ORIGINS,
    allow_origins=["https://agilizagestaofinanceira.up.railway.app", "http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(auth.router,        prefix=settings.API_PREFIX)
app.include_router(dashboard.router,   prefix=settings.API_PREFIX)
app.include_router(transacoes.router,  prefix=settings.API_PREFIX)
app.include_router(perfil.router,      prefix=settings.API_PREFIX)
app.include_router(historico.router,   prefix=settings.API_PREFIX)
app.include_router(metas.router,       prefix=settings.API_PREFIX)
app.include_router(contratos.router,   prefix=settings.API_PREFIX)
app.include_router(chat.router,        prefix=settings.API_PREFIX)


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    return {"status": "ok", "db": check_connection()}
