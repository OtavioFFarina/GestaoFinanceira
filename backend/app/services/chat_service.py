"""
ChatService — Avocado AI financial assistant.

RAG Flow:
  1. Collect real financial context from DB for the user
  2. Build a dynamic system prompt with that context + market indicators
  3. Call the LLM (OpenAI-compatible API) and return the response
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)


# ── Context Collector ────────────────────────────────────────────────────────

def _get_current_cycle(db: Session, usuario_id: str) -> dict:
    """Returns the open 'ativo' monthly cycle, if any."""
    row = db.execute(
        text("""
            SELECT c.id, c.ano, c.mes, c.renda_total, c.saldo_atual,
                   COALESCE(SUM(t.valor), 0) AS total_saidas
            FROM ciclos_mensais c
            LEFT JOIN transacoes t ON t.ciclo_id = c.id AND t.tipo = 'saida'
            WHERE c.usuario_id = :uid
              AND c.status = 'ativo'
            GROUP BY c.id, c.ano, c.mes, c.renda_total, c.saldo_atual
            ORDER BY c.ano DESC, c.mes DESC
            LIMIT 1
        """),
        {"uid": usuario_id},
    ).mappings().first()

    if not row:
        return {}

    renda = float(row["renda_total"] or 0)
    saidas = float(row["total_saidas"] or 0)
    saldo = float(row["saldo_atual"] or 0)
    pct = round((saidas / renda * 100), 1) if renda > 0 else 0.0

    return {
        "renda_mensal": renda,
        "total_gastos_mes": saidas,
        "saldo_disponivel": saldo,
        "percentual_comprometido": pct,
    }


def _get_dividas(db: Session, usuario_id: str) -> dict:
    """Returns a summary of the user's active financial contracts."""
    row = db.execute(
        text("""
            SELECT
                SUM(CASE WHEN tipo='pagar' AND status='ativo' THEN valor_total ELSE 0 END) AS total_dividas,
                SUM(CASE WHEN tipo='receber' AND status='ativo' THEN valor_total ELSE 0 END) AS total_receber,
                COUNT(CASE WHEN tipo='pagar' AND status='ativo' THEN 1 END) AS num_dividas,
                COUNT(CASE WHEN tipo='receber' AND status='ativo' THEN 1 END) AS num_receber
            FROM contratos_financeiros
            WHERE usuario_id = :uid
        """),
        {"uid": usuario_id},
    ).mappings().first()

    if not row:
        return {}

    return {
        "total_dividas_ativas": float(row["total_dividas"] or 0),
        "total_a_receber_ativo": float(row["total_receber"] or 0),
        "quantidade_dividas": int(row["num_dividas"] or 0),
        "quantidade_receber": int(row["num_receber"] or 0),
    }


def _get_metas(db: Session, usuario_id: str) -> list[dict]:
    """Returns active financial goals."""
    rows = db.execute(
        text("""
            SELECT titulo, valor_alvo, valor_atual, percentual, prazo
            FROM metas
            WHERE usuario_id = :uid AND status = 'ativa'
            ORDER BY percentual DESC
            LIMIT 5
        """),
        {"uid": usuario_id},
    ).mappings().all()

    return [
        {
            "titulo": r["titulo"],
            "valor_alvo": float(r["valor_alvo"]),
            "valor_atual": float(r["valor_atual"]),
            "progresso_pct": float(r["percentual"]),
            "prazo": str(r["prazo"]),
        }
        for r in rows
    ]


def _get_indicadores(db: Session) -> dict:
    """Returns all market indicators."""
    rows = db.execute(
        text("SELECT chave, valor, descricao FROM indicadores_mercado ORDER BY chave")
    ).mappings().all()

    # Return empty dict (graceful) if table doesn't exist yet
    return {r["chave"]: {"valor": float(r["valor"]), "descricao": r["descricao"]} for r in rows}


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
