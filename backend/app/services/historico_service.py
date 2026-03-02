"""
HistoricoService — lists all monthly cycles for a user with aggregated data.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.auth import CicloResumo


class HistoricoService:

    def get_historico(self, db: Session, usuario_id: str) -> list[CicloResumo]:
        rows = db.execute(
            text("""
                SELECT
                    cm.id          AS ciclo_id,
                    cm.ano,
                    cm.mes,
                    cm.renda_total,
                    COALESCE(SUM(t.valor), 0)  AS total_gasto,
                    cm.renda_total - COALESCE(SUM(t.valor), 0) AS saldo_livre,
                    ROUND(
                        (cm.renda_total - COALESCE(SUM(t.valor), 0))
                        / NULLIF(cm.renda_total, 0) * 100, 2
                    ) AS taxa_poupanca
                FROM ciclos_mensais cm
                LEFT JOIN transacoes t
                    ON t.ciclo_id = cm.id AND t.tipo = 'saida'
                WHERE cm.usuario_id = :uid
                GROUP BY cm.id, cm.ano, cm.mes, cm.renda_total
                ORDER BY cm.ano DESC, cm.mes DESC
            """),
            {"uid": usuario_id},
        ).mappings().all()

        return [
            CicloResumo(
                ciclo_id=r["ciclo_id"],
                ano=r["ano"],
                mes=r["mes"],
                renda_total=float(r["renda_total"]),
                total_gasto=float(r["total_gasto"]),
                saldo_livre=float(r["saldo_livre"]),
                taxa_poupanca=float(r["taxa_poupanca"] or 0),
            )
            for r in rows
        ]
