"""
AgentService — Orchestrates the financial AI agent.

Architecture:
  1. Load user financial context from DB (ContextService)
  2. Build message history with a strict system prompt
  3. Decide if external tools are needed (ReAct pattern via LangChain)
  4. Execute tools: news search, BCB API, bank yield comparison
  5. Synthesize a verified response with cited sources
  6. Persist conversation and return structured response

SOLID Principles applied:
  - Single Responsibility: each sub-service has one job
  - Open/Closed: new tools can be added without modifying AgentService
  - Dependency Inversion: services injected via constructor
"""
from __future__ import annotations

from typing import List

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.schemas.chat import AgentResponse, ChatMessage
from app.services.context_service import ContextService
from app.tools.bcb_selic_tool import get_selic_rate
from app.tools.bank_yield_tool import compare_bank_yields
from app.tools.financial_news_tool import search_financial_news

# ---------------------------------------------------------------------------
# System Prompt — Anti-hallucination, source-checked financial assistant
# ---------------------------------------------------------------------------
FINANCIAL_SYSTEM_PROMPT = """Você é um assistente financeiro pessoal chamado **Avocado**,
especializado no mercado financeiro brasileiro. Você é rigoroso, honesto e transparente.

## REGRAS OBRIGATÓRIAS — NUNCA VIOLE ESTAS REGRAS:

1. **NUNCA afirme rendimentos ou taxas sem citar a fonte e a data da consulta.**
   Formato obrigatório: "(Fonte: {nome}, consultado em {data})"

2. **Classifique SEMPRE o risco** de qualquer investimento mencionado:
   🟢 Baixo Risco | 🟡 Médio Risco | 🔴 Alto Risco

3. **Se não encontrar dados atualizados (com menos de 30 dias)**, comunique
   explicitamente: "Não possuo dados recentes sobre isso. Recomendo verificar
   diretamente em [fonte oficial]."

4. **Cruze no mínimo 2 fontes** antes de recomendar qualquer produto financeiro.
   Se não tiver 2 fontes, informe que é baseado em apenas 1 fonte.

5. **NUNCA recomende alocar mais de 20% em ativos de alto risco** sem emitir
   um alerta explícito ao usuário sobre a possibilidade de perda de capital.

6. **Diferencie SEMPRE** rentabilidade bruta de rentabilidade líquida (pós-IR e IOF).
   Use a tabela regressiva do IR sobre renda fixa quando aplicável.

7. **PROIBIDO criar dados fictícios.** Se não souber ou não tiver acesso à informação,
   responda exatamente: "Não tenho essa informação disponível no momento."

8. Ao sugerir viagens ou compras de alto valor, apresente sempre:
   - Estimativa de custo total
   - Estratégia de economia recomendada
   - Tempo estimado para juntar o valor com base nos dados financeiros do usuário

## CONTEXTO DO USUÁRIO:
{user_financial_context}

## COMPORTAMENTO:
- Seja conciso, direto e amigável.
- Use emojis com moderação para melhor legibilidade.
- Formate valores em Reais: R$ X.XXX,XX
- Responda SEMPRE em Português do Brasil.
"""


class AgentService:
    """
    Orchestrates the LangChain ReAct agent with financial tools.
    Injected dependencies follow Dependency Inversion Principle.
    """

    def __init__(self, context_service: ContextService) -> None:
        self._context_service = context_service
        self._llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.2,  # Low temperature = more deterministic, less hallucination
            streaming=True,
        )
        self._tools = [
            search_financial_news,
            compare_bank_yields,
            get_selic_rate,
        ]

    async def chat(
        self,
        user_id: str,
        conversation_history: List[ChatMessage],
        new_message: str,
    ) -> AgentResponse:
        """
        Main entry point. Returns a verified agent response with cited sources.
        """
        # 1. Load user financial context
        user_context = await self._context_service.get_user_financial_summary(user_id)

        # 2. Build the prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", FINANCIAL_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # 3. Build agent (ReAct via OpenAI function calling)
        agent = create_openai_tools_agent(self._llm, self._tools, prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=self._tools,
            verbose=settings.DEBUG,
            max_iterations=5,           # Prevent infinite tool loops
            return_intermediate_steps=True,
        )

        # 4. Format conversation history for LangChain
        lc_history = self._format_history(conversation_history)

        # 5. Execute agent
        result = await executor.ainvoke({
            "input": new_message,
            "chat_history": lc_history,
            "user_financial_context": user_context,
        })

        # 6. Extract sources from intermediate tool steps
        sources = self._extract_sources(result.get("intermediate_steps", []))

        return AgentResponse(
            content=result["output"],
            sources=sources,
        )

    def _format_history(self, history: List[ChatMessage]):
        """Converts stored messages to LangChain message format."""
        messages = []
        for msg in history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
        return messages

    def _extract_sources(self, intermediate_steps: list) -> list:
        """Extracts source citations from tool outputs for transparency."""
        sources = []
        for action, observation in intermediate_steps:
            if isinstance(observation, dict) and "sources" in observation:
                sources.extend(observation["sources"])
        return sources
