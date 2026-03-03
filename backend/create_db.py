from app.core.database import engine
from app.models.base import Base

from app.api.v1.routes import auth, chat, contratos, dashboard, historico, metas, perfil, transacoes

def init_db():
    print("👷 Construindo as tabelas do banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas com sucesso!")

if __name__ == "__main__":
    init_db()