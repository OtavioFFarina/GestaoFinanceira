# 💰 Gestão Financeira — Controle Orçamentário com Agente de IA

> **Plataforma completa de gestão financeira pessoal e empresarial potencializada por um Agente Autônomo de IA.**  
> Arquitetura moderna com **Next.js**, **Node.js / TypeScript**, **PostgreSQL** e orquestração automatizada via **Docker**.

---

## 🎯 Sobre o Projeto

O **GestaoFinanceira** foi desenvolvido para centralizar entradas, saídas, ciclos recorrentes e projeções de fluxo de caixa, integrando um assistente de Inteligência Artificial capaz de categorizar despesas e sugerir otimizações de economia.

### 🌟 Destaques da Arquitetura

- 🐳 **Orquestração Completa com Docker:** Banco de dados PostgreSQL configurado e gerenciado via `docker-compose.postgres.yml`.
- 🔄 **Alocação Dinâmica de Portas:** O backend seleciona automaticamente portas livres no range 8001–8015 para evitar conflitos com outros serviços locais.
- 🤖 **Agente de IA Integrado:** Módulo de análise inteligente de despesas e sugestões financeiras personalizadas.
- ⚡ **Scripts One-Click:** Scripts de shell dedicados para iniciar (`start_all.sh`) e encerrar (`stop_all.sh`) todo o ambiente sem processos órfãos.

---

## 🚀 Como Executar o Projeto

```bash
# 1. Clone o repositório
git clone https://github.com/OtavioFFarina/GestaoFinanceira.git
cd GestaoFinanceira

# 2. Garanta permissão de execução nos scripts
chmod +x start_all.sh stop_all.sh

# 3. Suba todo o ambiente com um único comando
./start_all.sh
```

Após a inicialização:
- **Frontend:** [http://127.0.0.1:3001](http://127.0.0.1:3001)
- **Backend:** Conforme exibido no terminal e registrado em `.run/backend.port`

### Para parar todos os serviços:
```bash
./stop_all.sh
```

---

## 👨‍💻 Autor
Desenvolvido por **[Otávio Farina](https://github.com/OtavioFFarina)**.
