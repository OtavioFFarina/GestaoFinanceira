"""
DashboardService — Business logic for the dashboard endpoint.
Uses ORM models (MonthlyRecord, RecordCategory) instead of raw SQL views.
"""
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.monthly_record import MonthlyRecord
from app.models.record_category import RecordCategory
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
        Uses ORM models instead of database views.
        """
        # 1. Fetch the monthly record
        ref_month = date(ano, mes, 1)
        record = db.execute(
            select(MonthlyRecord).where(
                MonthlyRecord.user_id == usuario_id,
                MonthlyRecord.reference_month == ref_month,
            )
        ).scalar_one_or_none()

        renda_total: float = float(record.total_received) if record else 0.0
        ciclo_id: str | None = record.id if record else None

        # 2. Fetch per-category breakdown from RecordCategory
        alocacoes: list[CategoriaAlocacao] = []
        if record:
            categories = db.execute(
                select(RecordCategory).where(
                    RecordCategory.record_id == record.id
                )
            ).scalars().all()

            for cat in categories:
                planned = float(cat.planned_amount)
                actual = float(cat.actual_amount)
                pct_planned = round(planned / renda_total * 100, 2) if renda_total > 0 else 0.0
                pct_actual = round(actual / renda_total * 100, 2) if renda_total > 0 else 0.0

                alocacoes.append(
                    CategoriaAlocacao(
                        categoria_id=cat.id,
                        categoria=cat.category.value,
                        slug=cat.category.value,
                        cor_hex=None,
                        valor_planejado=planned,
                        percentual_planejado=pct_planned,
                        valor_realizado=actual,
                        percentual_realizado=pct_actual,
                    )
                )

        # Sort by actual amount descending
        alocacoes.sort(key=lambda a: a.valor_realizado, reverse=True)

        # 3. Compute aggregates
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
