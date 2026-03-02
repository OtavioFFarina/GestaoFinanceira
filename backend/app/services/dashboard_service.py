"""
DashboardService — Business logic for the dashboard endpoint.
Queries vw_planejado_vs_realizado and aggregates data for the frontend.
SOLID: Single Responsibility — only handles dashboard aggregation.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.dashboard import CategoriaAlocacao, DashboardResponse


class DashboardService:

    def get_dashboard(
        self,
        db: Session,
        usuario_id: str,
        ano: int,
        mes: int,
    ) -> DashboardResponse:
        """
        Returns the full dashboard payload for a given user/month.
        Reads from the vw_planejado_vs_realizado VIEW for chart data.
        """
        # 1. Fetch the cycle header (renda_total + ciclo_id)
        ciclo_row = db.execute(
            text("""
                SELECT id, renda_total
                FROM ciclos_mensais
                WHERE usuario_id = :uid AND ano = :ano AND mes = :mes
            """),
            {"uid": usuario_id, "ano": ano, "mes": mes},
        ).mappings().first()

        renda_total: float = float(ciclo_row["renda_total"]) if ciclo_row else 0.0
        ciclo_id: int | None = ciclo_row["id"] if ciclo_row else None

        # 2. Fetch per-category breakdown from the VIEW
        view_rows = db.execute(
            text("""
                SELECT
                    categoria_id,
                    categoria,
                    slug,
                    cor_hex,
                    valor_planejado,
                    percentual_planejado,
                    valor_realizado,
                    percentual_realizado
                FROM vw_planejado_vs_realizado
                WHERE usuario_id = :uid AND ano = :ano AND mes = :mes
                ORDER BY valor_realizado DESC
            """),
            {"uid": usuario_id, "ano": ano, "mes": mes},
        ).mappings().all()

        alocacoes = [
            CategoriaAlocacao(
                categoria_id=row["categoria_id"],
                categoria=row["categoria"],
                slug=row["slug"],
                cor_hex=row["cor_hex"],
                valor_planejado=float(row["valor_planejado"]),
                percentual_planejado=float(row["percentual_planejado"]),
                valor_realizado=float(row["valor_realizado"]),
                percentual_realizado=float(row["percentual_realizado"]),
            )
            for row in view_rows
        ]

        # 3. Compute aggregates — all float, no Decimal mixing
        total_gasto: float = sum(a.valor_realizado for a in alocacoes)
        saldo_livre: float = renda_total - total_gasto
        taxa_poupanca: float = (
            round(saldo_livre / renda_total * 100, 2)
            if renda_total > 0
            else 0.0
        )

        return DashboardResponse(
            ciclo_id=ciclo_id,
            usuario_id=usuario_id,
            ano=ano,
            mes=mes,
            renda_total=renda_total,
            total_gasto=total_gasto,
            saldo_livre=saldo_livre,
            taxa_poupanca=taxa_poupanca,
            alocacoes=alocacoes,
        )
