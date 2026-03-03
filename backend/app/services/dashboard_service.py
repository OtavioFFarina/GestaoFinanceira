"""
DashboardService — Business logic for the dashboard endpoint.
Uses ORM aggregate sums from Transaction and Category instead of static old tables.
"""
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.monthly_record import MonthlyRecord
from app.models.transaction import Transaction, TransactionTypeEnum
from app.models.category import Category
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
        Calculates aggregates dynamically from the Transaction table.
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

        total_gasto = 0.0
        alocacoes: list[CategoriaAlocacao] = []

        if record:
            # 2. Dynamically calculate category expenses via GROUP BY
            stmt = (
                select(
                    Category.id,
                    Category.name,
                    Category.slug,
                    Category.hex_color,
                    func.sum(Transaction.amount).label("actual")
                )
                .select_from(Transaction)
                .join(Category, Transaction.category_id == Category.id)
                .where(
                    Transaction.record_id == record.id,
                    Transaction.type == TransactionTypeEnum.SAIDA
                )
                .group_by(Category.id)
            )
            
            results = db.execute(stmt).all()

            for r in results:
                cat_id, name, slug, color, actual = r
                actual = float(actual)
                pct_actual = round(actual / renda_total * 100, 2) if renda_total > 0 else 0.0

                alocacoes.append(
                    CategoriaAlocacao(
                        categoria_id=cat_id,
                        categoria=name,
                        slug=slug,
                        cor_hex=color,
                        valor_planejado=0.0,
                        percentual_planejado=0.0,
                        valor_realizado=actual,
                        percentual_realizado=pct_actual,
                    )
                )

            # 3. Handle standalone exact total dynamically from DB
            total_gasto_row = db.execute(
                select(func.sum(Transaction.amount))
                .select_from(Transaction)
                .where(
                    Transaction.record_id == record.id,
                    Transaction.type == TransactionTypeEnum.SAIDA
                )
            ).scalar_one_or_none()
            total_gasto = float(total_gasto_row) if total_gasto_row else 0.0

        # Sort allocations by actual amount descending
        alocacoes.sort(key=lambda a: a.valor_realizado, reverse=True)

        saldo_livre: float = renda_total - total_gasto
        taxa_poupanca: float = (
            round((saldo_livre / renda_total) * 100, 2)
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
