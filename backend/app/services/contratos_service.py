"""
ContratosService — handles creation, listing, installment payment (baixa) and summary.
Fully ORM-based, no raw SQL.
"""
import calendar
from datetime import date
from decimal import Decimal, ROUND_DOWN
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.models.financial_contract import FinancialContract, ContractStatusEnum, ContractTypeEnum
from app.models.installment import Installment, InstallmentStatusEnum
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
        Lógica anti-centavo-fantasma.
        """
        contract = FinancialContract(
            user_id=payload.usuario_id,
            type=ContractTypeEnum(payload.tipo),
            description=payload.descricao,
            total_amount=float(payload.valor_total),
            num_installments=payload.num_parcelas,
            first_due_date=payload.data_primeiro_vencimento,
            notes=payload.observacoes,
        )
        db.add(contract)
        db.flush()  # Get the ID without committing

        # Calculate installments without ghost pennies
        n = payload.num_parcelas
        total = payload.valor_total
        base = (total / n).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        ultima = total - base * (n - 1)

        for i in range(1, n + 1):
            valor = ultima if i == n else base
            vcto = _add_months(payload.data_primeiro_vencimento, i - 1)
            inst = Installment(
                contract_id=contract.id,
                number=i,
                amount=float(valor),
                due_date=vcto,
                status=InstallmentStatusEnum.PENDENTE,
            )
            db.add(inst)

        db.commit()
        db.refresh(contract)
        return self._contract_to_response(contract)

    # ── Detalhe de um contrato ────────────────────────────────────────────────
    def get_contrato(self, db: Session, contrato_id: str) -> ContratoResponse:
        contract = db.get(FinancialContract, contrato_id)
        if not contract:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado.")
        return self._contract_to_response(contract)

    # ── Listar contratos de um usuário ────────────────────────────────────────
    def list_contratos(
        self, db: Session, usuario_id: str, tipo: Optional[str] = None
    ) -> list[ContratoListItem]:
        stmt = select(FinancialContract).where(
            FinancialContract.user_id == usuario_id
        )
        if tipo:
            stmt = stmt.where(FinancialContract.type == tipo)
        stmt = stmt.order_by(FinancialContract.created_at.desc())

        contracts = db.execute(stmt).scalars().all()
        result = []

        for c in contracts:
            installments = c.installments
            pagas = sum(1 for i in installments if i.status == InstallmentStatusEnum.PAGA)
            pendentes = sum(1 for i in installments if i.status == InstallmentStatusEnum.PENDENTE)
            atrasadas = sum(1 for i in installments if i.status == InstallmentStatusEnum.ATRASADA)

            pending_installments = [
                i for i in installments
                if i.status in (InstallmentStatusEnum.PENDENTE, InstallmentStatusEnum.ATRASADA)
            ]
            pending_installments.sort(key=lambda i: i.due_date)

            proximo_vcto = pending_installments[0].due_date if pending_installments else None
            proximo_valor = float(pending_installments[0].amount) if pending_installments else None

            result.append(
                ContratoListItem(
                    id=c.id,
                    tipo=c.type.value,
                    descricao=c.description,
                    valor_total=float(c.total_amount),
                    num_parcelas=c.num_installments,
                    status=c.status.value,
                    data_primeiro_vencimento=c.first_due_date,
                    parcelas_pagas=pagas,
                    parcelas_pendentes=pendentes,
                    parcelas_atrasadas=atrasadas,
                    proximo_vencimento=proximo_vcto,
                    proximo_valor=proximo_valor,
                )
            )

        return result

    # ── Dar baixa em uma parcela ──────────────────────────────────────────────
    def baixar_parcela(self, db: Session, parcela_id: str) -> BaixaResponse:
        inst = db.get(Installment, parcela_id)
        if not inst:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela não encontrada.")

        inst.status = InstallmentStatusEnum.PAGA
        inst.payment_date = date.today()

        # Check if all installments are paid
        contract = inst.contract
        all_paid = all(
            i.status == InstallmentStatusEnum.PAGA
            for i in contract.installments
        )
        if all_paid:
            contract.status = ContractStatusEnum.QUITADO

        db.commit()
        return BaixaResponse(
            parcela_id=parcela_id,
            status="paga",
            data_pagamento=date.today(),
            contrato_quitado=all_paid,
        )

    # ── Excluir contrato (cascade deleta parcelas) ────────────────────────────
    def delete_contrato(self, db: Session, contrato_id: str) -> None:
        contract = db.get(FinancialContract, contrato_id)
        if contract:
            db.delete(contract)
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
            # Get active contracts of this type
            contracts = db.execute(
                select(FinancialContract).where(
                    FinancialContract.user_id == usuario_id,
                    FinancialContract.type == tipo,
                    FinancialContract.status == ContractStatusEnum.ATIVO,
                )
            ).scalars().all()

            total_mes = 0.0
            contratos_ativos = len(contracts)
            proximo_vcto = None

            for c in contracts:
                for inst in c.installments:
                    if inst.status in (InstallmentStatusEnum.PENDENTE, InstallmentStatusEnum.ATRASADA):
                        # Sum for this month
                        if mes_ini <= inst.due_date < mes_fim:
                            total_mes += float(inst.amount)
                        # Find next due date from today
                        if inst.due_date >= today:
                            if proximo_vcto is None or inst.due_date < proximo_vcto:
                                proximo_vcto = inst.due_date

            return {
                "total_mes": total_mes,
                "contratos_ativos": contratos_ativos,
                "proximo_vcto": proximo_vcto,
            }

        pagar = _totais("pagar")
        receber = _totais("receber")

        return ResumoContratos(
            total_pagar_mes=pagar["total_mes"],
            contratos_pagar_ativos=pagar["contratos_ativos"],
            proximo_vencimento_pagar=pagar["proximo_vcto"],
            total_receber_mes=receber["total_mes"],
            contratos_receber_ativos=receber["contratos_ativos"],
            proximo_vencimento_receber=receber["proximo_vcto"],
        )

    # ── Parcelas pendentes de pagar (modal do dashboard) ──────────────────────
    def list_parcelas_pendentes_pagar(self, db: Session, usuario_id: str) -> list[dict]:
        contracts = db.execute(
            select(FinancialContract).where(
                FinancialContract.user_id == usuario_id,
                FinancialContract.type == ContractTypeEnum.PAGAR,
                FinancialContract.status == ContractStatusEnum.ATIVO,
            )
        ).scalars().all()

        result = []
        for c in contracts:
            for inst in c.installments:
                if inst.status in (InstallmentStatusEnum.PENDENTE, InstallmentStatusEnum.ATRASADA):
                    result.append({
                        "id": inst.id,
                        "label": (
                            f"{c.description} — Parcela {inst.number}/{c.num_installments} "
                            f"(R$ {float(inst.amount):.2f}) vence {inst.due_date}"
                        ),
                        "valor": float(inst.amount),
                        "data_vencimento": str(inst.due_date),
                        "status": inst.status.value,
                    })

        result.sort(key=lambda x: x["data_vencimento"])
        return result

    # ── Sync atrasadas ────────────────────────────────────────────────────────
    def _sync_atrasadas(self, db: Session, usuario_id: str) -> None:
        """Marks overdue pending installments as 'atrasada'."""
        contracts = db.execute(
            select(FinancialContract).where(
                FinancialContract.user_id == usuario_id,
            )
        ).scalars().all()

        today = date.today()
        changed = False
        for c in contracts:
            for inst in c.installments:
                if inst.status == InstallmentStatusEnum.PENDENTE and inst.due_date < today:
                    inst.status = InstallmentStatusEnum.ATRASADA
                    changed = True

        if changed:
            db.commit()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _contract_to_response(self, contract: FinancialContract) -> ContratoResponse:
        parcelas = [
            ParcelaResponse(
                id=i.id,
                contrato_id=i.contract_id,
                numero_parcela=i.number,
                valor_parcela=float(i.amount),
                data_vencimento=i.due_date,
                data_pagamento=i.payment_date,
                status=i.status.value,
            )
            for i in contract.installments
        ]
        return ContratoResponse(
            id=contract.id,
            usuario_id=str(contract.user_id),
            tipo=contract.type.value,
            descricao=contract.description,
            valor_total=float(contract.total_amount),
            num_parcelas=contract.num_installments,
            data_primeiro_vencimento=contract.first_due_date,
            status=contract.status.value,
            observacoes=contract.notes,
            created_at=contract.created_at,
            parcelas=parcelas,
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _add_months(d: date, months: int) -> date:
    """Adds `months` months to a date, clamping to the last day of the month."""
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(d.day, last_day)
    return d.replace(year=year, month=month, day=day)
