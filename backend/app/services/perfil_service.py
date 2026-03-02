"""
PerfilService — get and update user profile.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.auth import PerfilResponse, PerfilUpdate


class PerfilService:

    def get_perfil(self, db: Session, usuario_id: str) -> PerfilResponse:
        row = db.execute(
            text("""
                SELECT u.id AS usuario_id, u.nome, u.email,
                       p.nome_exibicao, p.foto_url, p.tema, p.meses_historico
                FROM usuarios u
                LEFT JOIN perfil_usuario p ON p.usuario_id = u.id
                WHERE u.id = :uid
            """),
            {"uid": usuario_id},
        ).mappings().first()

        if not row:
            raise ValueError("Usuário não encontrado.")

        return PerfilResponse(
            usuario_id=str(row["usuario_id"]),
            nome=row["nome"],
            nome_exibicao=row["nome_exibicao"] or row["nome"],
            email=row["email"],
            foto_url=row["foto_url"],
            tema=row["tema"] or "dark",
            meses_historico=row["meses_historico"] or 12,
        )

    def update_perfil(self, db: Session, usuario_id: str, payload: PerfilUpdate) -> PerfilResponse:
        updates: dict = {}
        if payload.nome_exibicao is not None:
            updates["nome_exibicao"] = payload.nome_exibicao
        if payload.foto_url is not None:
            updates["foto_url"] = payload.foto_url
        if payload.tema is not None:
            updates["tema"] = payload.tema
        if payload.meses_historico is not None:
            updates["meses_historico"] = payload.meses_historico

        if updates:
            set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
            updates["uid"] = usuario_id
            db.execute(
                text(f"""
                    INSERT INTO perfil_usuario (usuario_id, {', '.join(k for k in updates if k != 'uid')})
                    VALUES (:uid, {', '.join(f':{k}' for k in updates if k != 'uid')})
                    ON DUPLICATE KEY UPDATE {set_clause}
                """),
                updates,
            )
            db.commit()

        return self.get_perfil(db, usuario_id)

    def delete_dados(self, db: Session, usuario_id: str):
        # 1. Deletar transacoes associadas aos ciclos_mensais deste usuario
        db.execute(text("""
            DELETE t FROM transacoes t
            INNER JOIN ciclos_mensais c ON t.ciclo_id = c.id
            WHERE c.usuario_id = :uid
        """), {"uid": usuario_id})

        # 2. Deletar os ciclos_mensais (metas_alocacao eh excluido via CASCADE)
        db.execute(text("DELETE FROM ciclos_mensais WHERE usuario_id = :uid"), {"uid": usuario_id})

        # 3. Deletar as metas independentes
        db.execute(text("DELETE FROM metas WHERE usuario_id = :uid"), {"uid": usuario_id})

        # 4. Deletar parcelas (FK filho de contratos_financeiros)
        db.execute(text("""
            DELETE p FROM parcelas p
            INNER JOIN contratos_financeiros c ON p.contrato_id = c.id
            WHERE c.usuario_id = :uid
        """), {"uid": usuario_id})

        # 5. Deletar contratos financeiros (dividas e recebíveis)
        db.execute(text("DELETE FROM contratos_financeiros WHERE usuario_id = :uid"), {"uid": usuario_id})

        db.commit()

