# Mini Agente de Atendimento IA 🤖

Agente de atendimento inteligente integrado ao WhatsApp, construído do zero com Python. Utiliza RAG (Retrieval-Augmented Generation) para buscar informações em documentos e um LLM para gerar respostas naturais em português.

## Demonstração

**Usuário:** "Quero me matricular no plano anual, mas posso precisar viajar a trabalho por um mês. Perco esse tempo?"

**Agente:** "Não se preocupe! Nossa academia oferece pausa de até 60 dias por ano sem custo adicional. Basta nos avisar com antecedência e o período é preservado para quando você retornar."

---

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Linguagem | Python 3.13 |
| Framework web | Flask |
| Busca semântica | sentence-transformers (multilingual) |
| IA Generativa | Groq API — Llama 3.3 70B |
| Leitura de documentos | python-docx |
| WhatsApp | Evolution API v2.3.7 |
| Infraestrutura | Docker + Docker Compose |
| Banco de dados | SQLite (histórico e memória) + PostgreSQL (Evolution API) |
| Cache | Redis |

---

## Arquitetura

Mensagem no WhatsApp
↓
Evolution API (Docker) → webhook → Flask
↓
rag.py → busca chunks relevantes no documento Word
↓
llm.py → Groq API gera resposta natural com histórico
↓
Resposta enviada de volta ao WhatsApp

---

## Funcionalidades

- **Atendimento automático 24/7** no WhatsApp
- **Busca semântica** — entende variações e sinônimos, não apenas palavras exatas
- **RAG pipeline** — extrai parágrafos e tabelas de documentos Word como base de conhecimento
- **Memória de conversa** — cada cliente tem seu histórico salvo por número de telefone
- **Respostas geradas por LLM** — naturais e contextualizadas, não textos fixos
- **API REST** para testes sem WhatsApp

---

## Estrutura do projeto

├── main.py          # Rotas HTTP e webhook do WhatsApp
├── rag.py           # Pipeline RAG: leitura, chunks, embeddings e busca
├── llm.py           # Integração com Groq API e montagem do histórico
├── database.py      # SQLite: histórico, conhecimento e memória por número
├── agente.py        # Módulo legado de busca por similaridade
├── utils.py         # Normalização de texto
├── requirements.txt
└── .env.example     # Variáveis de ambiente necessárias

---

## Como rodar localmente

### Pré-requisitos
- Python 3.10+
- Docker Desktop

### 1. Clone o repositório
```bash
git clone https://github.com/igueera/mini-agente-atendimento.git
cd mini-agente-atendimento
```

### 2. Configure as variáveis de ambiente
```bash
cp .env.example .env
# Edite o .env com suas credenciais
```

### 3. Instale as dependências Python
```bash
pip install -r requirements.txt
```

### 4. Suba a infraestrutura Docker
```bash
cd docker
docker-compose up -d
```

### 5. Inicie o agente
```bash
python main.py
```

### 6. Teste via API
```bash
POST http://localhost:5000/pergunta
Content-Type: application/json

{
  "mensagem": "Quais são os planos disponíveis?"
}
```

---

## Variáveis de ambiente

```env
EVOLUTION_URL=http://localhost:8080
EVOLUTION_KEY=sua-chave-aqui
INSTANCE_NAME=nome-da-instancia
GROQ_API_KEY=sua-chave-groq
```

---

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Status da aplicação |
| POST | `/pergunta` | Testa o agente via HTTP |
| GET | `/historico` | Retorna conversas salvas |
| POST | `/conhecimento` | Adiciona novo conhecimento ao banco |
| POST | `/webhook` | Recebe mensagens do WhatsApp (Evolution API) |

---

## Desenvolvido por

**Igor Gabriel** — [LinkedIn](https://linkedin.com/in/igor-gabriel-924812220/) · [GitHub](https://github.com/igueera)