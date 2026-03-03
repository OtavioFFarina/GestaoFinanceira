"""
PerfilService — get and update user profile using ORM.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.monthly_record import MonthlyRecord
from app.models.transaction import Transaction
from app.models.goal import Goal
from app.models.financial_contract import FinancialContract
from app.models.installment import Installment
from app.schemas.auth import PerfilResponse, PerfilUpdate


class PerfilService:

    def get_perfil(self, db: Session, usuario_id: str) -> PerfilResponse:
        user = db.execute(
            select(User).where(User.id == usuario_id)
        ).scalar_one_or_none()

        if not user:
            raise ValueError("Usuário não encontrado.")

        profile = db.execute(
            select(UserProfile).where(UserProfile.user_id == usuario_id)
        ).scalar_one_or_none()

        return PerfilResponse(
            usuario_id=str(user.id),
            nome=user.name,
            nome_exibicao=profile.display_name if profile and profile.display_name else user.name,
            email=user.email,
            foto_url=profile.photo_url if profile else None,
            tema=profile.theme if profile else "dark",
            meses_historico=profile.history_months if profile else 12,
        )

    def update_perfil(self, db: Session, usuario_id: str, payload: PerfilUpdate) -> PerfilResponse:
        profile = db.execute(
            select(UserProfile).where(UserProfile.user_id == usuario_id)
        ).scalar_one_or_none()

        if not profile:
            # Create profile if it doesn't exist
            profile = UserProfile(user_id=usuario_id)
            db.add(profile)

        if payload.nome_exibicao is not None:
            profile.display_name = payload.nome_exibicao
        if payload.foto_url is not None:
            profile.photo_url = payload.foto_url
        if payload.tema is not None:
            profile.theme = payload.tema
        if payload.meses_historico is not None:
            profile.history_months = payload.meses_historico

        db.commit()
        return self.get_perfil(db, usuario_id)

    def delete_dados(self, db: Session, usuario_id: str):
        # 1. Delete transactions linked to monthly records
        records = db.execute(
            select(MonthlyRecord).where(MonthlyRecord.user_id == usuario_id)
        ).scalars().all()

        for record in records:
            txs = db.execute(
                select(Transaction).where(Transaction.record_id == record.id)
            ).scalars().all()
            for tx in txs:
                db.delete(tx)

        # 2. Delete monthly records (record_categories cascade)
        for record in records:
            db.delete(record)

        # 3. Delete goals
        goals = db.execute(
            select(Goal).where(Goal.user_id == usuario_id)
        ).scalars().all()
        for goal in goals:
            db.delete(goal)

        # 4. Delete financial contracts (installments cascade)
        contracts = db.execute(
            select(FinancialContract).where(FinancialContract.user_id == usuario_id)
        ).scalars().all()
        for contract in contracts:
            db.delete(contract)

        db.commit()
