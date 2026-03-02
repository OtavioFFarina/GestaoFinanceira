"""
ContratosService — handles creation, listing, installment payment (baixa) and summary.
"""
from datetime import date
from decimal import Decimal, ROUND_DOWN
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.contratos import (
    BaixaResponse,
    ContratoCreate,
    ContratoListItem,
    ContratoResponse,
    ParcelaResponse,
    ResumoContratos,
)


class ContratosService:

    # ── Criar contrato + gerar parcelas ──────────────────────────────────────
    def create_contrato(self, db: Session, payload: ContratoCreate) -> ContratoResponse:
        """
        Cria o contrato e gera automaticamente N parcelas.
        Lógica anti-centavo-fantasma:
          base   = TRUNCATE(valor_total / n, 2)  — trunca, não arredonda
          última = valor_total - base * (n - 1)  — absorve o centavo restante
        """
        # 1. Inserir contrato
        result = db.execute(
            text("""
                INSERT INTO contratos_financeiros
                    (usuario_id, tipo, descricao, valor_total, num_parcelas,
                     data_primeiro_vencimento, observacoes)
                VALUES
                    (:uid, :tipo, :descricao, :valor_total, :n_parc,
                     :primeiro_vcto, :obs)
            """),
            {
                "uid":          payload.usuario_id,
                "tipo":         payload.tipo,
                "descricao":    payload.descricao,
                "valor_total":  float(payload.valor_total),
                "n_parc":       payload.num_parcelas,
                "primeiro_vcto": payload.data_primeiro_vencimento.isoformat(),
                "obs":          payload.observacoes,
            },
        )
        contrato_id = result.lastrowid

        # 2. Calcular parcelas sem centavo fantasma
        n = payload.num_parcelas
        total = payload.valor_total
        base = (total / n).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        ultima = total - base * (n - 1)

        # 3. Inserir parcelas
        for i in range(1, n + 1):
            valor = ultima if i == n else base
            vcto = _add_months(payload.data_primeiro_vencimento, i - 1)
            db.execute(
                text("""
                    INSERT INTO parcelas
                        (contrato_id, numero_parcela, valor_parcela, data_vencimento, status)
                    VALUES
                        (:cid, :num, :valor, :vcto, 'pendente')
                """),
                {
                    "cid":   contrato_id,
                    "num":   i,
                    "valor": float(valor),
                    "vcto":  vcto.isoformat(),
                },
            )

        db.commit()
        return self.get_contrato(db, contrato_id)

    # ── Detalhe de um contrato ────────────────────────────────────────────────
    def get_contrato(self, db: Session, contrato_id: int) -> ContratoResponse:
        row = db.execute(
            text("SELECT * FROM contratos_financeiros WHERE id = :id"),
            {"id": contrato_id},
        ).mappings().first()

        if not row:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado.")

        parcelas = self._get_parcelas(db, contrato_id)
        return ContratoResponse(
            id=row["id"],
            usuario_id=str(row["usuario_id"]),
            tipo=row["tipo"],
            descricao=row["descricao"],
            valor_total=float(row["valor_total"]),
            num_parcelas=row["num_parcelas"],
            data_primeiro_vencimento=row["data_primeiro_vencimento"],
            status=row["status"],
            observacoes=row["observacoes"],
            created_at=row["created_at"],
            parcelas=parcelas,
        )

    # ── Listar contratos de um usuário ────────────────────────────────────────
    def list_contratos(
        self, db: Session, usuario_id: str, tipo: Optional[str] = None
    ) -> list[ContratoListItem]:
        query = """
            SELECT
                c.id, c.tipo, c.descricao, c.valor_total, c.num_parcelas,
                c.status, c.data_primeiro_vencimento,
                SUM(p.status = 'paga')    AS parcelas_pagas,
                SUM(p.status = 'pendente') AS parcelas_pendentes,
                SUM(p.status = 'atrasada') AS parcelas_atrasadas,
                MIN(CASE WHEN p.status IN ('pendente','atrasada') THEN p.data_vencimento END) AS proximo_vencimento,
                MIN(CASE WHEN p.status IN ('pendente','atrasada') THEN p.valor_parcela END)   AS proximo_valor
            FROM contratos_financeiros c
            LEFT JOIN parcelas p ON p.contrato_id = c.id
            WHERE c.usuario_id = :uid
        """
        params: dict = {"uid": usuario_id}
        if tipo:
            query += " AND c.tipo = :tipo"
            params["tipo"] = tipo
        query += " GROUP BY c.id ORDER BY proximo_vencimento ASC, c.created_at DESC"

        rows = db.execute(text(query), params).mappings().all()

        return [
            ContratoListItem(
                id=r["id"],
                tipo=r["tipo"],
                descricao=r["descricao"],
                valor_total=float(r["valor_total"]),
                num_parcelas=r["num_parcelas"],
                status=r["status"],
                data_primeiro_vencimento=r["data_primeiro_vencimento"],
                parcelas_pagas=int(r["parcelas_pagas"] or 0),
                parcelas_pendentes=int(r["parcelas_pendentes"] or 0),
                parcelas_atrasadas=int(r["parcelas_atrasadas"] or 0),
                proximo_vencimento=r["proximo_vencimento"],
                proximo_valor=float(r["proximo_valor"]) if r["proximo_valor"] else None,
            )
            for r in rows
        ]

    # ── Dar baixa em uma parcela ──────────────────────────────────────────────
    def baixar_parcela(self, db: Session, parcela_id: int) -> BaixaResponse:
        # 1. Marcar parcela como paga
        db.execute(
            text("""
                UPDATE parcelas
                SET status = 'paga', data_pagamento = CURDATE()
                WHERE id = :id
            """),
            {"id": parcela_id},
        )

        # 2. Obter contrato_id
        row = db.execute(
            text("SELECT contrato_id, data_pagamento FROM parcelas WHERE id = :id"),
            {"id": parcela_id},
        ).mappings().first()
        contrato_id = row["contrato_id"]
        data_pagamento = row["data_pagamento"]

        # 3. Verificar se todas as parcelas estão pagas
        pendente_count = db.execute(
            text("SELECT COUNT(*) FROM parcelas WHERE contrato_id = :cid AND status != 'paga'"),
            {"cid": contrato_id},
        ).scalar()

        contrato_quitado = int(pendente_count) == 0
        if contrato_quitado:
            db.execute(
                text("UPDATE contratos_financeiros SET status = 'quitado' WHERE id = :id"),
                {"id": contrato_id},
            )

        db.commit()
        return BaixaResponse(
            parcela_id=parcela_id,
            status="paga",
            data_pagamento=date.today(),
            contrato_quitado=contrato_quitado,
        )

    # ── Excluir contrato (cascade deleta parcelas) ────────────────────────────
    def delete_contrato(self, db: Session, contrato_id: int) -> None:
        db.execute(
            text("DELETE FROM contratos_financeiros WHERE id = :id"),
            {"id": contrato_id},
        )
        db.commit()

    # ── Resumo para cards do dashboard ────────────────────────────────────────
    def get_resumo(self, db: Session, usuario_id: str) -> ResumoContratos:
        today = date.today()
        mes_ini = today.replace(day=1)
        if today.month == 12:
            mes_fim = today.replace(year=today.year + 1, month=1, day=1)
        else:
            mes_fim = today.replace(month=today.month + 1, day=1)

        def _totais(tipo: str) -> dict:
            # Total do mês corrente (SUM filtrado por data)
            row = db.execute(
                text("""
                    SELECT
                        COALESCE(SUM(CASE
                            WHEN p.data_vencimento >= :ini AND p.data_vencimento < :fim
                            THEN p.valor_parcela ELSE 0 END), 0)  AS total_mes,
                        COUNT(DISTINCT c.id)                        AS contratos_ativos
                    FROM parcelas p
                    JOIN contratos_financeiros c ON c.id = p.contrato_id
                    WHERE c.usuario_id = :uid
                      AND c.tipo       = :tipo
                      AND c.status     = 'ativo'
                      AND p.status    IN ('pendente', 'atrasada')
                """),
                {"uid": usuario_id, "tipo": tipo,
                 "ini": mes_ini.isoformat(), "fim": mes_fim.isoformat()},
            ).mappings().first()

            # Próximo vencimento: qualquer parcela pendente a partir de HOJE (sem limite de mês)
            proximo = db.execute(
                text("""
                    SELECT MIN(p.data_vencimento) AS proximo_vcto
                    FROM parcelas p
                    JOIN contratos_financeiros c ON c.id = p.contrato_id
                    WHERE c.usuario_id     = :uid
                      AND c.tipo           = :tipo
                      AND c.status         = 'ativo'
                      AND p.status        IN ('pendente', 'atrasada')
                      AND p.data_vencimento >= :hoje
                """),
                {"uid": usuario_id, "tipo": tipo, "hoje": today.isoformat()},
            ).mappings().first()

            return {
                "total_mes":        float(row["total_mes"]) if row["total_mes"] else 0.0,
                "contratos_ativos": int(row["contratos_ativos"]) if row["contratos_ativos"] else 0,
                "proximo_vcto":     proximo["proximo_vcto"] if proximo else None,
            }

        pagar   = _totais("pagar")
        receber = _totais("receber")

        return ResumoContratos(
            total_pagar_mes=pagar["total_mes"],
            contratos_pagar_ativos=pagar["contratos_ativos"],
            proximo_vencimento_pagar=pagar["proximo_vcto"],
            total_receber_mes=receber["total_mes"],
            contratos_receber_ativos=receber["contratos_ativos"],
            proximo_vencimento_receber=receber["proximo_vcto"],
        )

    # ── Parcelas pendentes de pagar de um usuário (para modal do dashboard) ───
    def list_parcelas_pendentes_pagar(self, db: Session, usuario_id: str) -> list[dict]:
        """Retorna parcelas pendentes/atrasadas de contratos tipo 'pagar' para o modal."""
        rows = db.execute(
            text("""
                SELECT
                    p.id, p.numero_parcela, p.valor_parcela,
                    p.data_vencimento, p.status,
                    c.descricao AS contrato_descricao,
                    c.num_parcelas
                FROM parcelas p
                JOIN contratos_financeiros c ON c.id = p.contrato_id
                WHERE c.usuario_id = :uid
                  AND c.tipo       = 'pagar'
                  AND c.status     = 'ativo'
                  AND p.status    IN ('pendente', 'atrasada')
                ORDER BY p.data_vencimento ASC
            """),
            {"uid": usuario_id},
        ).mappings().all()
        return [
            {
                "id": r["id"],
                "label": f"{r['contrato_descricao']} — Parcela {r['numero_parcela']}/{r['num_parcelas']} "
                         f"(R$ {float(r['valor_parcela']):.2f}) vence {r['data_vencimento']}",
                "valor": float(r["valor_parcela"]),
                "data_vencimento": str(r["data_vencimento"]),
                "status": r["status"],
            }
            for r in rows
        ]

    # ── Atualizar status de parcelas atrasadas (helper) ──────────────────────
    def _sync_atrasadas(self, db: Session, usuario_id: str) -> None:
        """Marca como 'atrasada' toda parcela pendente cujo vencimento já passou."""
        db.execute(
            text("""
                UPDATE parcelas p
                JOIN contratos_financeiros c ON c.id = p.contrato_id
                SET p.status = 'atrasada'
                WHERE c.usuario_id    = :uid
                  AND p.status        = 'pendente'
                  AND p.data_vencimento < CURDATE()
            """),
            {"uid": usuario_id},
        )
        db.commit()

    # ── Parcelas de um contrato ───────────────────────────────────────────────
    def _get_parcelas(self, db: Session, contrato_id: int) -> list[ParcelaResponse]:
        rows = db.execute(
            text("""
                SELECT id, contrato_id, numero_parcela, valor_parcela,
                       data_vencimento, data_pagamento, status
                FROM parcelas
                WHERE contrato_id = :cid
                ORDER BY numero_parcela ASC
            """),
            {"cid": contrato_id},
        ).mappings().all()
        return [
            ParcelaResponse(
                id=r["id"],
                contrato_id=r["contrato_id"],
                numero_parcela=r["numero_parcela"],
                valor_parcela=float(r["valor_parcela"]),
                data_vencimento=r["data_vencimento"],
                data_pagamento=r["data_pagamento"],
                status=r["status"],
            )
            for r in rows
        ]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _add_months(d: date, months: int) -> date:
    """Adds `months` months to a date, clamping to the last day of the month."""
    month = d.month - 1 + months
    year  = d.year + month // 12
    month = month % 12 + 1
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    day = min(d.day, last_day)
    return d.replace(year=year, month=month, day=day)
