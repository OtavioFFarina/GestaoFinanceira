"""
TransacaoService — handles transaction CRUD + cycle upsert + categories + reserve.
"""
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

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
        result = db.execute(
            text("""
                INSERT INTO transacoes
                    (ciclo_id, categoria_id, meta_id, descricao, valor,
                     tipo, data_transacao, recorrente, observacoes)
                VALUES
                    (:ciclo_id, :cat_id, :meta_id, :descricao, :valor,
                     :tipo, :data, :recorrente, :obs)
            """),
            {
                "ciclo_id":   payload.ciclo_id,
                "cat_id":     payload.categoria_id,
                "meta_id":    payload.meta_id,
                "descricao":  payload.descricao,
                "valor":      float(payload.valor),
                "tipo":       payload.tipo,
                "data":       payload.data_transacao.isoformat(),
                "recorrente": int(payload.recorrente),
                "obs":        payload.observacoes,
            },
        )

        # If linked to a goal, update meta.valor_atual
        if payload.meta_id:
            db.execute(
                text("""
                    UPDATE metas
                    SET valor_atual = valor_atual + :valor
                    WHERE id = :meta_id
                """),
                {"valor": float(payload.valor), "meta_id": payload.meta_id},
            )

        db.commit()
        row = db.execute(
            text("SELECT * FROM transacoes WHERE id = :id"),
            {"id": result.lastrowid},
        ).mappings().first()
        return TransacaoResponse(
            id=row["id"], ciclo_id=row["ciclo_id"], categoria_id=row["categoria_id"],
            descricao=row["descricao"], valor=row["valor"],
            tipo=row["tipo"], data_transacao=row["data_transacao"], recorrente=bool(row["recorrente"]),
        )

    # ── List transactions for a cycle (detailed) ──────────────────────────────
    def list_transacoes(self, db: Session, ciclo_id: int) -> list[TransacaoDetalhe]:
        rows = db.execute(
            text("""
                SELECT
                    t.id, t.ciclo_id, t.categoria_id, t.meta_id,
                    t.descricao, t.valor, t.tipo, t.data_transacao,
                    t.recorrente, t.observacoes, t.created_at,
                    c.nome AS categoria_nome, c.cor_hex AS categoria_cor,
                    m.titulo AS meta_titulo
                FROM transacoes t
                JOIN categorias c ON c.id = t.categoria_id
                LEFT JOIN metas m ON m.id = t.meta_id
                WHERE t.ciclo_id = :ciclo_id
                ORDER BY t.data_transacao DESC, t.created_at DESC
            """),
            {"ciclo_id": ciclo_id},
        ).mappings().all()

        return [
            TransacaoDetalhe(
                id=r["id"], ciclo_id=r["ciclo_id"], categoria_id=r["categoria_id"],
                categoria_nome=r["categoria_nome"], categoria_cor=r["categoria_cor"],
                meta_id=r["meta_id"], meta_titulo=r["meta_titulo"],
                descricao=r["descricao"], valor=float(r["valor"]),
                tipo=r["tipo"], data_transacao=r["data_transacao"],
                recorrente=bool(r["recorrente"]), observacoes=r["observacoes"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    # ── Update transaction ────────────────────────────────────────────────────
    def update_transacao(self, db: Session, transacao_id: int, payload: TransacaoUpdate) -> TransacaoDetalhe:
        fields: dict = {}
        if payload.descricao is not None: fields["descricao"] = payload.descricao
        if payload.valor is not None: fields["valor"] = float(payload.valor)
        if payload.data_transacao is not None: fields["data_transacao"] = payload.data_transacao.isoformat()
        if payload.observacoes is not None: fields["observacoes"] = payload.observacoes
        if payload.meta_id is not None: fields["meta_id"] = payload.meta_id

        if fields:
            set_clause = ", ".join(f"{k} = :{k}" for k in fields)
            fields["id"] = transacao_id
            db.execute(text(f"UPDATE transacoes SET {set_clause} WHERE id = :id"), fields)
            db.commit()

        ciclo_id = db.execute(
            text("SELECT ciclo_id FROM transacoes WHERE id = :id"), {"id": transacao_id}
        ).scalar()
        txs = self.list_transacoes(db, ciclo_id)
        return next(t for t in txs if t.id == transacao_id)

    # ── Delete transaction ────────────────────────────────────────────────────
    def delete_transacao(self, db: Session, transacao_id: int) -> None:
        # Get info before delete to revert meta value if needed
        row = db.execute(
            text("SELECT meta_id, valor FROM transacoes WHERE id = :id"),
            {"id": transacao_id},
        ).mappings().first()

        if row and row["meta_id"]:
            db.execute(
                text("UPDATE metas SET valor_atual = GREATEST(0, valor_atual - :v) WHERE id = :id"),
                {"v": float(row["valor"]), "id": row["meta_id"]},
            )

        db.execute(text("DELETE FROM transacoes WHERE id = :id"), {"id": transacao_id})
        db.commit()

    # ── Upsert monthly cycle ──────────────────────────────────────────────────
    def upsert_ciclo(self, db: Session, payload: CicloCreate) -> CicloResponse:
        db.execute(
            text("""
                INSERT INTO ciclos_mensais
                    (usuario_id, ano, mes, renda_total, observacoes)
                VALUES
                    (:uid, :ano, :mes, :renda, :obs)
                ON DUPLICATE KEY UPDATE
                    renda_total  = VALUES(renda_total),
                    observacoes  = VALUES(observacoes),
                    updated_at   = CURRENT_TIMESTAMP
            """),
            {
                "uid":   payload.usuario_id,
                "ano":   payload.ano,
                "mes":   payload.mes,
                "renda": float(payload.renda_total),
                "obs":   payload.observacoes,
            },
        )
        db.commit()

        row = db.execute(
            text("""
                SELECT id, usuario_id, ano, mes, renda_total, fechado
                FROM ciclos_mensais
                WHERE usuario_id = :uid AND ano = :ano AND mes = :mes
            """),
            {"uid": payload.usuario_id, "ano": payload.ano, "mes": payload.mes},
        ).mappings().first()

        ciclo_id = row["id"]

        # ── Auto-importar parcelas 'receber' vencidas neste mês como entradas ──
        # Busca a categoria 'receber' (criamos via migration); fallback para NULL
        cat_row = db.execute(
            text("SELECT id FROM categorias WHERE slug = 'receber' LIMIT 1"),
        ).mappings().first()
        cat_id = cat_row["id"] if cat_row else None

        if cat_id:
            # Parcelas 'receber' com vencimento no mês registrado, ainda pendentes
            parcelas_receber = db.execute(
                text("""
                    SELECT p.id, p.valor_parcela, p.data_vencimento,
                           c.descricao AS contrato_descricao
                    FROM parcelas p
                    JOIN contratos_financeiros c ON c.id = p.contrato_id
                    WHERE c.usuario_id = :uid
                      AND c.tipo       = 'receber'
                      AND c.status     = 'ativo'
                      AND p.status    IN ('pendente', 'atrasada')
                      AND YEAR(p.data_vencimento)  = :ano
                      AND MONTH(p.data_vencimento) = :mes
                """),
                {"uid": payload.usuario_id, "ano": payload.ano, "mes": payload.mes},
            ).mappings().all()

            for p in parcelas_receber:
                # Evitar duplicatas: verifica se já existe transação vinculada
                exists = db.execute(
                    text("""
                        SELECT 1 FROM transacoes
                        WHERE ciclo_id = :ciclo_id
                          AND categoria_id = :cat_id
                          AND descricao = :descricao
                          AND valor = :valor
                          AND tipo = 'entrada'
                        LIMIT 1
                    """),
                    {
                        "ciclo_id": ciclo_id,
                        "cat_id":   cat_id,
                        "descricao": f"[Auto] {p['contrato_descricao']}",
                        "valor":    float(p["valor_parcela"]),
                    },
                ).scalar()

                if not exists:
                    db.execute(
                        text("""
                            INSERT INTO transacoes
                                (ciclo_id, categoria_id, descricao, valor,
                                 tipo, data_transacao, recorrente)
                            VALUES
                                (:ciclo_id, :cat_id, :descricao, :valor,
                                 'entrada', :data, 0)
                        """),
                        {
                            "ciclo_id": ciclo_id,
                            "cat_id":   cat_id,
                            "descricao": f"[Auto] {p['contrato_descricao']}",
                            "valor":    float(p["valor_parcela"]),
                            "data":     str(p["data_vencimento"]),
                        },
                    )

            db.commit()

        return CicloResponse(
            id=row["id"], usuario_id=str(row["usuario_id"]),
            ano=row["ano"], mes=row["mes"],
            renda_total=row["renda_total"], fechado=bool(row["fechado"]),
        )

    # ── List categories ───────────────────────────────────────────────────────
    def list_categorias(self, db: Session, tipo: str | None) -> list[CategoriaPublica]:
        query = "SELECT id, nome, slug, cor_hex, icone, tipo FROM categorias"
        params: dict = {}
        if tipo:
            query += " WHERE tipo = :tipo"
            params["tipo"] = tipo
        query += " ORDER BY nome"
        rows = db.execute(text(query), params).mappings().all()
        return [CategoriaPublica(**dict(r)) for r in rows]

    # ── Reserva (emergency fund) ──────────────────────────────────────────────
    def get_reserva(self, db: Session, usuario_id: str) -> ReservaResponse:
        # Total accumulated reserve
        total_row = db.execute(
            text("SELECT saldo_total, total_aportes, ultimo_aporte FROM vw_reserva_saldo WHERE usuario_id = :uid"),
            {"uid": usuario_id},
        ).mappings().first()

        saldo = float(total_row["saldo_total"]) if total_row else 0.0
        aportes = int(total_row["total_aportes"]) if total_row else 0
        ultimo = total_row["ultimo_aporte"] if total_row else None

        # Monthly breakdown
        hist_rows = db.execute(
            text("""
                SELECT cm.ano, cm.mes, SUM(t.valor) AS valor
                FROM transacoes t
                JOIN ciclos_mensais cm ON cm.id = t.ciclo_id
                JOIN categorias c ON c.id = t.categoria_id
                WHERE cm.usuario_id = :uid AND c.slug = 'reserva' AND t.tipo = 'saida'
                GROUP BY cm.ano, cm.mes
                ORDER BY cm.ano DESC, cm.mes DESC
                LIMIT 24
            """),
            {"uid": usuario_id},
        ).mappings().all()

        historico = [{"ano": r["ano"], "mes": r["mes"], "valor": float(r["valor"])} for r in hist_rows]

        return ReservaResponse(
            saldo_total=saldo, total_aportes=aportes,
            ultimo_aporte=ultimo, historico=historico,
        )
