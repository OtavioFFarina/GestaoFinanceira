"""
FastAPI application entry point — all routes registered here.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.v1.routes import auth, chat, contratos, dashboard, historico, metas, perfil, transacoes
from app.core.config import settings
from app.core.database import SessionLocal, check_connection, engine

# Import all models so Base.metadata.create_all() picks them up
import app.models  # noqa: F401
from app.models.base import Base
from app.models.category import Category, CategoryTypeEnum
from app.models.market_indicator import MarketIndicator


# ── Default Categories Seed ──────────────────────────────────────────────────
DEFAULT_CATEGORIES = [
    # Saída (expenses)
    {"name": "Moradia",        "slug": "moradia",        "icon": "🏠", "hex_color": "#58A6FF", "type": CategoryTypeEnum.SAIDA},
    {"name": "Alimentação",    "slug": "alimentacao",    "icon": "🍔", "hex_color": "#F0883E", "type": CategoryTypeEnum.SAIDA},
    {"name": "Transporte",     "slug": "transporte",     "icon": "🚗", "hex_color": "#A371F7", "type": CategoryTypeEnum.SAIDA},
    {"name": "Saúde",          "slug": "saude",          "icon": "💊", "hex_color": "#F85149", "type": CategoryTypeEnum.SAIDA},
    {"name": "Educação",       "slug": "educacao",       "icon": "📚", "hex_color": "#79C0FF", "type": CategoryTypeEnum.SAIDA},
    {"name": "Lazer",          "slug": "lazer",          "icon": "🎮", "hex_color": "#D2A8FF", "type": CategoryTypeEnum.SAIDA},
    {"name": "Gastos Fixos",   "slug": "gastos-fixos",   "icon": "📋", "hex_color": "#7EE787", "type": CategoryTypeEnum.SAIDA},
    {"name": "Vestuário",      "slug": "vestuario",      "icon": "👕", "hex_color": "#FFA657", "type": CategoryTypeEnum.SAIDA},
    {"name": "Assinaturas",    "slug": "assinaturas",    "icon": "📺", "hex_color": "#BC8CFF", "type": CategoryTypeEnum.SAIDA},
    {"name": "Investimentos",  "slug": "investimentos",  "icon": "📈", "hex_color": "#3FB950", "type": CategoryTypeEnum.SAIDA},
    {"name": "Reserva",        "slug": "reserva",        "icon": "🛡️", "hex_color": "#388BFD", "type": CategoryTypeEnum.SAIDA},
    {"name": "Dívidas",        "slug": "dividas",        "icon": "💸", "hex_color": "#F85149", "type": CategoryTypeEnum.SAIDA},
    {"name": "Outros",         "slug": "outros",         "icon": "📦", "hex_color": "#8B949E", "type": CategoryTypeEnum.SAIDA},
    # Entrada (income)
    {"name": "Salário",        "slug": "salario",        "icon": "💰", "hex_color": "#3FB950", "type": CategoryTypeEnum.ENTRADA},
    {"name": "Freelance",      "slug": "freelance",      "icon": "💻", "hex_color": "#58A6FF", "type": CategoryTypeEnum.ENTRADA},
    {"name": "A Receber",      "slug": "receber",        "icon": "📥", "hex_color": "#7EE787", "type": CategoryTypeEnum.ENTRADA},
    {"name": "Outros Entrada", "slug": "outros-entrada", "icon": "📦", "hex_color": "#8B949E", "type": CategoryTypeEnum.ENTRADA},
]

DEFAULT_INDICATORS = [
    {"key": "selic",  "value": 10.75, "description": "Taxa Selic (a.a.)"},
    {"key": "cdi",    "value": 10.65, "description": "CDI (a.a.)"},
    {"key": "ipca",   "value": 4.50,  "description": "IPCA acumulado 12 meses"},
    {"key": "dolar",  "value": 5.85,  "description": "Dólar comercial (R$)"},
]


def seed_defaults():
    """Insert default categories and market indicators if the tables are empty."""
    db = SessionLocal()
    try:
        # Seed categories (only if table is empty or missing slugs)
        existing_slugs = set(
            row[0] for row in db.execute(select(Category.slug)).all()
        )
        for cat in DEFAULT_CATEGORIES:
            if cat["slug"] not in existing_slugs:
                db.add(Category(**cat))

        # Seed market indicators
        existing_keys = set(
            row[0] for row in db.execute(select(MarketIndicator.key)).all()
        )
        for ind in DEFAULT_INDICATORS:
            if ind["key"] not in existing_keys:
                db.add(MarketIndicator(**ind))

        db.commit()
        inserted_cats = len(DEFAULT_CATEGORIES) - len(existing_slugs & {c["slug"] for c in DEFAULT_CATEGORIES})
        if inserted_cats > 0:
            print(f"🌱 Seed: {inserted_cats} categorias inseridas.")
        else:
            print("🌱 Seed: categorias já existentes, nenhuma inserida.")
    except Exception as e:
        db.rollback()
        print(f"⚠️ Seed falhou (não crítico): {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if not check_connection():
        raise RuntimeError("❌ Falha na conexão com o banco de dados. Verifique o .env e se o banco está rodando.")

    # Create all tables that don't exist yet
    Base.metadata.create_all(bind=engine)

    # Seed default data
    seed_defaults()

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
