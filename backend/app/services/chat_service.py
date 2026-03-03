"""
ChatService — Avocado AI financial assistant.

RAG Flow:
  1. Collect real financial context from DB for the user
  2. Build a dynamic system prompt with that context + market indicators
  3. Call the LLM (OpenAI-compatible API) and return the response

Fully ORM-based, no raw SQL.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.monthly_record import MonthlyRecord
from app.models.transaction import Transaction, TransactionTypeEnum
from app.models.financial_contract import FinancialContract
from app.models.goal import Goal, GoalStatusEnum
from app.models.market_indicator import MarketIndicator

logger = logging.getLogger(__name__)


# ── Context Collector ────────────────────────────────────────────────────────

def _get_current_cycle(db: Session, usuario_id: str) -> dict:
    """Returns the most recent monthly record for the user."""
    record = db.execute(
        select(MonthlyRecord)
        .where(MonthlyRecord.user_id == usuario_id)
        .order_by(MonthlyRecord.reference_month.desc())
    ).scalars().first()

    if not record:
        return {}

    renda = float(record.total_received or 0)

    # Sum of 'saida' transactions
    total_saidas = db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.record_id == record.id,
            Transaction.type == TransactionTypeEnum.SAIDA,
        )
    ).scalar()
    saidas = float(total_saidas or 0)

    saldo = renda - saidas
    pct = round((saidas / renda * 100), 1) if renda > 0 else 0.0

    return {
        "renda_mensal": renda,
        "total_gastos_mes": saidas,
        "saldo_disponivel": saldo,
        "percentual_comprometido": pct,
    }


def _get_dividas(db: Session, usuario_id: str) -> dict:
    """Returns a summary of the user's active financial contracts."""
    contracts = db.execute(
        select(FinancialContract).where(
            FinancialContract.user_id == usuario_id,
            FinancialContract.status == "ativo",
        )
    ).scalars().all()

    total_dividas = sum(float(c.total_amount) for c in contracts if c.type.value == "pagar")
    total_receber = sum(float(c.total_amount) for c in contracts if c.type.value == "receber")
    num_dividas = sum(1 for c in contracts if c.type.value == "pagar")
    num_receber = sum(1 for c in contracts if c.type.value == "receber")

    return {
        "total_dividas_ativas": total_dividas,
        "total_a_receber_ativo": total_receber,
        "quantidade_dividas": num_dividas,
        "quantidade_receber": num_receber,
    }


def _get_metas(db: Session, usuario_id: str) -> list[dict]:
    """Returns active financial goals."""
    goals = db.execute(
        select(Goal)
        .where(Goal.user_id == usuario_id, Goal.status == GoalStatusEnum.ATIVA)
        .order_by(Goal.deadline.asc())
        .limit(5)
    ).scalars().all()

    return [
        {
            "titulo": g.title,
            "valor_alvo": float(g.target_amount),
            "valor_atual": float(g.current_amount),
            "progresso_pct": g.progress_pct,
            "prazo": str(g.deadline),
        }
        for g in goals
    ]


def _get_indicadores(db: Session) -> dict:
    """Returns all market indicators."""
    indicators = db.execute(
        select(MarketIndicator).order_by(MarketIndicator.key)
    ).scalars().all()

    return {
        i.key: {"valor": float(i.value), "descricao": i.description}
        for i in indicators
    }


def get_contexto_financeiro(db: Session, usuario_id: str) -> dict:
    """Collects all relevant financial context for the given user."""
    try:
        indicadores = _get_indicadores(db)
    except Exception:
        indicadores = {}

    try:
        ciclo = _get_current_cycle(db, usuario_id)
    except Exception:
        ciclo = {}

    try:
        dividas = _get_dividas(db, usuario_id)
    except Exception:
        dividas = {}

    try:
        metas = _get_metas(db, usuario_id)
    except Exception:
        metas = []

    return {
        "ciclo_atual": ciclo,
        "contratos": dividas,
        "metas_ativas": metas,
        "indicadores_mercado": indicadores,
    }


# ── System Prompt Builder ────────────────────────────────────────────────────

def _build_system_prompt(contexto: dict) -> str:
    ctx_json = json.dumps(contexto, ensure_ascii=False, indent=2)
    now = datetime.now().strftime("%B de %Y")

    return f"""Você é o Avocado 🥑, um consultor financeiro pessoal sagaz, direto e focado em fazer o patrimônio do usuário crescer.

PERSONALIDADE:
- Seja direto, amigável e use emojis com moderação.
- Quando o usuário quiser gastar algo inviável, seja firme mas educado.
- Quando sobrar dinheiro, SEMPRE sugira onde investir baseado na Selic/CDI atual.
- Use linguagem simples; evite jargões desnecessários.
- Limpe suas respostas a no máximo 3–4 parágrafos curtos, exceto quando o usuário pedir análise detalhada.

DADOS FINANCEIROS DO USUÁRIO (referência: {now}):
```json
{ctx_json}
```

INSTRUÇÕES:
1. Use os dados acima para fundamentar TODAS as respostas sobre a situação financeira do usuário.
2. Se o usuário perguntar algo que os dados não cobrem, responda com base no seu conhecimento geral, mas deixe claro que não tem o dado específico.
3. Para sugestões de investimento, sempre mencione a Selic ({contexto.get('indicadores_mercado', {}).get('selic', {}).get('valor', '?')}% a.a.) e CDI como referência.
4. Não invente dados financeiros; se o campo estiver vazio (ciclo não registrado ainda), informe o usuário de forma amigável.
5. Responda SEMPRE em português brasileiro.
"""


# ── LLM Caller ───────────────────────────────────────────────────────────────

async def call_llm(system_prompt: str, history: list[dict]) -> str:
    """Calls the configured LLM via the OpenAI-compatible SDK."""
    if not settings.OPENAI_API_KEY:
        return (
            "⚠️ O Avocado AI não está configurado ainda. "
            "Adicione `OPENAI_API_KEY` ao arquivo `.env` do backend para ativar o assistente."
        )

    try:
        from openai import AsyncOpenAI

        client_kwargs: dict = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL:
            client_kwargs["base_url"] = settings.OPENAI_BASE_URL

        client = AsyncOpenAI(**client_kwargs)

        messages = [{"role": "system", "content": system_prompt}] + history

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,  # type: ignore[arg-type]
            temperature=0.65,
            max_tokens=700,
        )
        return response.choices[0].message.content or "Não consegui gerar uma resposta."

    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        return (
            "😔 Tive um problema ao processar sua pergunta. "
            "Verifique se a chave de API está correta e tente novamente."
        )


# ── Service Façade ───────────────────────────────────────────────────────────

class ChatService:

    async def responder(
        self,
        db: Session,
        usuario_id: str,
        mensagem: str,
        historico: list[dict] | None = None,
    ) -> str:
        """Main entry point: collect context → build prompt → call LLM → return reply."""
        contexto = get_contexto_financeiro(db, usuario_id)
        system_prompt = _build_system_prompt(contexto)

        # Build conversation history: previous turns + new user message
        history: list[dict] = historico or []
        history = history + [{"role": "user", "content": mensagem}]

        return await call_llm(system_prompt, history)
