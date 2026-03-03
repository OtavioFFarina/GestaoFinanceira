"""
TransacaoService — handles transaction CRUD + monthly record upsert + categories.
Fully ORM-based, no raw SQL.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.monthly_record import MonthlyRecord
from app.models.transaction import Transaction, TransactionTypeEnum
from app.models.category import Category
from app.models.goal import Goal
from app.models.financial_contract import FinancialContract
from app.models.installment import Installment, InstallmentStatusEnum
from app.schemas.transacao import (
    CategoriaPublica,
    CicloCreate,
    CicloResponse,
    ReservaResponse,
    TransacaoCreate,
    TransacaoDetalhe,
    TransacaoResponse,
    TransacaoUpdate,
)


class TransacaoService:

    # ── Create transaction ────────────────────────────────────────────────────
    def create_transacao(self, db: Session, payload: TransacaoCreate) -> TransacaoResponse:
        tx = Transaction(
            record_id=payload.ciclo_id,
            category_id=payload.categoria_id,
            goal_id=payload.meta_id,
            description=payload.descricao,
            amount=float(payload.valor),
            type=TransactionTypeEnum(payload.tipo),
            transaction_date=payload.data_transacao,
            recurring=payload.recorrente,
            notes=payload.observacoes,
        )
        db.add(tx)

        # If linked to a goal, update current_amount
        if payload.meta_id:
            goal = db.get(Goal, payload.meta_id)
            if goal:
                goal.current_amount = float(goal.current_amount) + float(payload.valor)

        db.commit()
        db.refresh(tx)

        return TransacaoResponse(
            id=tx.id,
            ciclo_id=tx.record_id,
            categoria_id=tx.category_id,
            descricao=tx.description,
            valor=Decimal(str(tx.amount)),
            tipo=tx.type.value,
            data_transacao=tx.transaction_date,
            recorrente=tx.recurring,
        )

    # ── List transactions for a record (detailed) ─────────────────────────────
    def list_transacoes(self, db: Session, ciclo_id: str) -> list[TransacaoDetalhe]:
        txs = db.execute(
            select(Transaction)
            .where(Transaction.record_id == ciclo_id)
            .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        ).scalars().all()

        result = []
        for t in txs:
            # Category is eager-loaded
            cat = t.category
            goal = t.goal

            result.append(
                TransacaoDetalhe(
                    id=t.id,
                    ciclo_id=t.record_id,
                    categoria_id=t.category_id,
                    categoria_nome=cat.name if cat else "",
                    categoria_cor=cat.hex_color if cat else None,
                    meta_id=t.goal_id,
                    meta_titulo=goal.title if goal else None,
                    descricao=t.description,
                    valor=float(t.amount),
                    tipo=t.type.value,
                    data_transacao=t.transaction_date,
                    recorrente=t.recurring,
                    observacoes=t.notes,
                    created_at=t.created_at,
                )
            )
        return result

    # ── Update transaction ────────────────────────────────────────────────────
    def update_transacao(self, db: Session, transacao_id: str, payload: TransacaoUpdate) -> TransacaoDetalhe:
        tx = db.get(Transaction, transacao_id)
        if not tx:
            raise ValueError("Transação não encontrada.")

        if payload.descricao is not None:
            tx.description = payload.descricao
        if payload.valor is not None:
            tx.amount = float(payload.valor)
        if payload.data_transacao is not None:
            tx.transaction_date = payload.data_transacao
        if payload.observacoes is not None:
            tx.notes = payload.observacoes
        if payload.meta_id is not None:
            tx.goal_id = payload.meta_id

        db.commit()
        db.refresh(tx)

        txs = self.list_transacoes(db, tx.record_id)
        return next(t for t in txs if t.id == transacao_id)

    # ── Delete transaction ────────────────────────────────────────────────────
    def delete_transacao(self, db: Session, transacao_id: str) -> None:
        tx = db.get(Transaction, transacao_id)
        if not tx:
            return

        # Revert goal amount if linked
        if tx.goal_id:
            goal = db.get(Goal, tx.goal_id)
            if goal:
                goal.current_amount = max(0, float(goal.current_amount) - float(tx.amount))

        db.delete(tx)
        db.commit()

    # ── Upsert monthly record ─────────────────────────────────────────────────
    def upsert_ciclo(self, db: Session, payload: CicloCreate) -> CicloResponse:
        ref_month = date(payload.ano, payload.mes, 1)

        record = db.execute(
            select(MonthlyRecord).where(
                MonthlyRecord.user_id == payload.usuario_id,
                MonthlyRecord.reference_month == ref_month,
            )
        ).scalar_one_or_none()

        if record:
            record.total_received = float(payload.renda_total)
        else:
            record = MonthlyRecord(
                user_id=payload.usuario_id,
                reference_month=ref_month,
                total_received=float(payload.renda_total),
            )
            db.add(record)

        db.commit()
        db.refresh(record)

        # ── Auto-import 'receber' installments as income transactions ──
        cat_receber = db.execute(
            select(Category).where(Category.slug == "receber")
        ).scalar_one_or_none()

        if cat_receber:
            # Find pending 'receber' installments due this month
            installments = db.execute(
                select(Installment)
                .join(FinancialContract)
                .where(
                    FinancialContract.user_id == payload.usuario_id,
                    FinancialContract.type == "receber",
                    FinancialContract.status == "ativo",
                    Installment.status.in_(["pendente", "atrasada"]),
                    func.extract("year", Installment.due_date) == payload.ano,
                    func.extract("month", Installment.due_date) == payload.mes,
                )
            ).scalars().all()

            for inst in installments:
                contract = inst.contract
                desc = f"[Auto] {contract.description}"

                # Avoid duplicates
                exists = db.execute(
                    select(Transaction).where(
                        Transaction.record_id == record.id,
                        Transaction.category_id == cat_receber.id,
                        Transaction.description == desc,
                        Transaction.amount == float(inst.amount),
                        Transaction.type == TransactionTypeEnum.ENTRADA,
                    )
                ).scalar_one_or_none()

                if not exists:
                    tx = Transaction(
                        record_id=record.id,
                        category_id=cat_receber.id,
                        description=desc,
                        amount=float(inst.amount),
                        type=TransactionTypeEnum.ENTRADA,
                        transaction_date=inst.due_date,
                        recurring=False,
                    )
                    db.add(tx)

            db.commit()

        return CicloResponse(
            id=record.id,
            usuario_id=str(record.user_id),
            ano=record.reference_month.year,
            mes=record.reference_month.month,
            renda_total=Decimal(str(record.total_received)),
            fechado=False,
        )

    # ── List categories ───────────────────────────────────────────────────────
    def list_categorias(self, db: Session, tipo: str | None) -> list[CategoriaPublica]:
        stmt = select(Category)
        if tipo:
            stmt = stmt.where(Category.type == tipo)
        stmt = stmt.order_by(Category.name)

        cats = db.execute(stmt).scalars().all()
        return [
            CategoriaPublica(
                id=c.id,
                nome=c.name,
                slug=c.slug,
                cor_hex=c.hex_color,
                icone=c.icon,
                tipo=c.type.value,
            )
            for c in cats
        ]

    # ── Reserva (emergency fund) ──────────────────────────────────────────────
    def get_reserva(self, db: Session, usuario_id: str) -> ReservaResponse:
        # Find 'reserva' category
        cat_reserva = db.execute(
            select(Category).where(Category.slug == "reserva")
        ).scalar_one_or_none()

        if not cat_reserva:
            return ReservaResponse(saldo_total=0, total_aportes=0, ultimo_aporte=None, historico=[])

        # Get all reserve transactions (saida type for contributions)
        reserve_txs = db.execute(
            select(Transaction)
            .join(MonthlyRecord)
            .where(
                MonthlyRecord.user_id == usuario_id,
                Transaction.category_id == cat_reserva.id,
                Transaction.type == TransactionTypeEnum.SAIDA,
            )
            .order_by(Transaction.transaction_date.desc())
        ).scalars().all()

        saldo = sum(float(t.amount) for t in reserve_txs)
        total_aportes = len(reserve_txs)
        ultimo_aporte = reserve_txs[0].transaction_date if reserve_txs else None

        # Group by month for history
        monthly: dict[tuple[int, int], float] = {}
        for t in reserve_txs:
            key = (t.transaction_date.year, t.transaction_date.month)
            monthly[key] = monthly.get(key, 0) + float(t.amount)

        historico = [
            {"ano": k[0], "mes": k[1], "valor": v}
            for k, v in sorted(monthly.items(), reverse=True)[:24]
        ]

        return ReservaResponse(
            saldo_total=saldo,
            total_aportes=total_aportes,
            ultimo_aporte=ultimo_aporte,
            historico=historico,
        )
