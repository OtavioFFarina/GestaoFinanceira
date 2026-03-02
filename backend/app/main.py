"""
FastAPI application entry point — all routes registered here.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import auth, chat, contratos, dashboard, historico, metas, perfil, transacoes
from app.core.config import settings
from app.core.database import check_connection


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if not check_connection():
        raise RuntimeError("❌ Falha na conexão com MySQL. Verifique o .env e se o banco está rodando.")
    print("✅ Conexão com MySQL estabelecida com sucesso.")
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
    allow_origins=settings.CORS_ORIGINS,
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
