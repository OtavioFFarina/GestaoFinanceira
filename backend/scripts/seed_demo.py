"""
Seed script — creates the demo user with a real bcrypt hash.
Run: python scripts/seed_demo.py

Also recreates the perfil_usuario, sessoes and metas tables.
"""
import sys
import os

# Resolve backend root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

# ── Generate real bcrypt hash ────────────────────────────────────────────────
SENHA = "otavio1305"
senha_hash = bcrypt.hashpw(SENHA.encode(), bcrypt.gensalt(rounds=12)).decode()
DEMO_ID = "00000000-0000-0000-0000-000000000001"

print(f"🔐 Hash gerado para '{SENHA}': {senha_hash}")

with engine.begin() as conn:
    # ── Create tables if not exist ────────────────────────────────────────────
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS perfil_usuario (
            usuario_id      CHAR(36)  NOT NULL,
            nome_exibicao   VARCHAR(60) NOT NULL DEFAULT 'Usuário',
            foto_url        VARCHAR(500) NULL,
            tema            ENUM('dark','light') NOT NULL DEFAULT 'dark',
            meses_historico TINYINT NOT NULL DEFAULT 12,
            updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT pk_perfil         PRIMARY KEY (usuario_id),
            CONSTRAINT fk_perfil_usuario FOREIGN KEY (usuario_id)
                REFERENCES usuarios (id) ON DELETE CASCADE ON UPDATE RESTRICT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sessoes (
            id          CHAR(36)  NOT NULL DEFAULT (UUID()),
            usuario_id  CHAR(36)  NOT NULL,
            token       CHAR(64)  NOT NULL,
            expires_at  DATETIME  NOT NULL,
            created_at  DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT pk_sessoes         PRIMARY KEY (id),
            CONSTRAINT uq_sessao_token    UNIQUE (token),
            CONSTRAINT fk_sessao_usuario  FOREIGN KEY (usuario_id)
                REFERENCES usuarios (id) ON DELETE CASCADE ON UPDATE RESTRICT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS metas (
            id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            usuario_id      CHAR(36) NOT NULL,
            titulo          VARCHAR(120) NOT NULL,
            descricao       TEXT NULL,
            valor_alvo      DECIMAL(12,2) NOT NULL,
            valor_atual     DECIMAL(12,2) NOT NULL DEFAULT 0.00,
            prazo           DATE NOT NULL,
            categoria_id    SMALLINT UNSIGNED NULL,
            status          ENUM('ativa','concluida','cancelada') NOT NULL DEFAULT 'ativa',
            ia_dicas        TEXT NULL,
            created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT pk_metas         PRIMARY KEY (id),
            CONSTRAINT fk_meta_usuario  FOREIGN KEY (usuario_id)
                REFERENCES usuarios (id) ON DELETE CASCADE ON UPDATE RESTRICT,
            CONSTRAINT fk_meta_cat      FOREIGN KEY (categoria_id)
                REFERENCES categorias (id) ON DELETE SET NULL ON UPDATE CASCADE,
            CONSTRAINT chk_meta_alvo    CHECK (valor_alvo > 0),
            CONSTRAINT chk_meta_atual   CHECK (valor_atual >= 0)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """))

    print("✅ Tabelas criadas (se não existiam).")

    # ── Upsert demo user ─────────────────────────────────────────────────────
    conn.execute(text("""
        INSERT INTO usuarios (id, nome, email, senha_hash, ativo)
        VALUES (:id, 'Otávio', 'otaviofranciscofarina13@gmail.com', :hash, 1)
        ON DUPLICATE KEY UPDATE senha_hash = VALUES(senha_hash), ativo = 1, email = VALUES(email), nome = VALUES(nome)
    """), {"id": DEMO_ID, "hash": senha_hash})

    conn.execute(text("""
        INSERT INTO perfil_usuario (usuario_id, nome_exibicao, tema)
        VALUES (:id, 'Otávio', 'dark')
        ON DUPLICATE KEY UPDATE nome_exibicao = 'Otávio'
    """), {"id": DEMO_ID})

    print(f"✅ Usuário demo criado/atualizado.")
    print(f"   📧 Email: otaviofranciscofarina13@gmail.com")
    print(f"   🔑 Senha: {SENHA}")
    print(f"   🆔 ID: {DEMO_ID}")
    print()
    print("🚀 Agora você pode fazer login normalmente!")
