"""
HistoricoService — lists all monthly records for a user with aggregated data.
Uses ORM models instead of raw SQL.
"""
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.monthly_record import MonthlyRecord
from app.models.transaction import Transaction, TransactionTypeEnum
from app.schemas.auth import CicloResumo


class HistoricoService:

    def get_historico(self, db: Session, usuario_id: str) -> list[CicloResumo]:
        records = db.execute(
            select(MonthlyRecord)
            .where(MonthlyRecord.user_id == usuario_id)
            .order_by(MonthlyRecord.reference_month.desc())
        ).scalars().all()

        result = []
        for record in records:
            renda = float(record.total_received)

            # Sum of 'saida' transactions for this record
            total_gasto_row = db.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0))
                .where(
                    Transaction.record_id == record.id,
                    Transaction.type == TransactionTypeEnum.SAIDA,
                )
            ).scalar()
            total_gasto = float(total_gasto_row or 0)

            saldo_livre = renda - total_gasto
            taxa_poupanca = round(saldo_livre / renda * 100, 2) if renda > 0 else 0.0

            # Extract year and month from reference_month (date)
            ano = record.reference_month.year
            mes = record.reference_month.month

            result.append(
                CicloResumo(
                    ciclo_id=record.id,
                    ano=ano,
                    mes=mes,
                    renda_total=renda,
                    total_gasto=total_gasto,
                    saldo_livre=saldo_livre,
                    taxa_poupanca=taxa_poupanca,
                )
            )

        return result
