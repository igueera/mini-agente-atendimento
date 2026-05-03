# tests/test_integracao.py
# Testes de integração — testam os endpoints HTTP completos
# simulando requisições reais ao Flask

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("EVOLUTION_URL", "http://localhost:8080")
os.environ.setdefault("EVOLUTION_KEY", "chave-teste")
os.environ.setdefault("INSTANCE_NAME", "teste")
os.environ.setdefault("GROQ_API_KEY", "chave-teste")
os.environ.setdefault("DOCUMENTO_PATH", "academia_forcamax.docx")

from main import app
from database import criar_tabela, criar_tabela_conhecimento, criar_tabela_memoria, popular_conhecimento


@pytest.fixture
def client():
    app.config["TESTING"] = True
    criar_tabela()
    criar_tabela_conhecimento()
    criar_tabela_memoria()
    popular_conhecimento()
    with app.test_client() as client:
        yield client


class TestHome:
    def test_home_retorna_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_home_retorna_mensagem(self, client):
        response = client.get("/")
        assert b"funcionando" in response.data


class TestPergunta:
    def test_sem_corpo_retorna_400(self, client):
        response = client.post("/pergunta", json={})
        assert response.status_code == 400

    def test_sem_campo_mensagem_retorna_400(self, client):
        response = client.post("/pergunta", json={"outro": "campo"})
        assert response.status_code == 400

    def test_mensagem_vazia_retorna_400(self, client):
        response = client.post("/pergunta", json={"mensagem": "   "})
        assert response.status_code == 400

    @patch("main.gerar_resposta")
    @patch("main.buscar_contexto")
    def test_pergunta_valida_retorna_200(self, mock_contexto, mock_llm, client):
        mock_contexto.return_value = "contexto fictício"
        mock_llm.return_value = "Resposta fictícia do agente."

        response = client.post("/pergunta", json={"mensagem": "Qual o horário?"})
        assert response.status_code == 200
        assert "resposta" in response.get_json()

    @patch("main.gerar_resposta")
    @patch("main.buscar_contexto")
    def test_pergunta_retorna_resposta_do_llm(self, mock_contexto, mock_llm, client):
        # a resposta deve ser exatamente o que o LLM retornou
        mock_contexto.return_value = "contexto"
        mock_llm.return_value = "Funcionamos das 6h às 22h."

        response = client.post("/pergunta", json={"mensagem": "Qual o horário?"})
        dados = response.get_json()
        assert dados["resposta"] == "Funcionamos das 6h às 22h."


class TestHistorico:

    def test_historico_retorna_200(self, client):
        response = client.get("/historico")
        assert response.status_code == 200

    def test_historico_retorna_lista(self, client):
        response = client.get("/historico")
        assert isinstance(response.get_json(), list)



class TestConhecimento:

    def test_sem_campos_retorna_400(self, client):
        response = client.post("/conhecimento", json={})
        assert response.status_code == 400

    def test_campos_incompletos_retorna_400(self, client):
        response = client.post("/conhecimento", json={"categoria": "teste"})
        assert response.status_code == 400

    def test_adicionar_conhecimento_retorna_200(self, client):
        response = client.post("/conhecimento", json={
            "categoria": "teste",
            "keywords": "teste, exemplo",
            "resposta": "Resposta de teste."
        })
        assert response.status_code == 200


class TestWebhook:

    def test_evento_ignorado(self, client):
        # eventos que não são messages.upsert devem ser ignorados
        response = client.post("/webhook", json={"event": "outro.evento"})
        assert response.status_code == 200
        assert response.get_json()["status"] == "ignorado"

    def test_mensagem_propria_ignorada(self, client):
        # mensagens fromMe=True devem ser ignoradas (evita loop)
        response = client.post("/webhook", json={
            "event": "messages.upsert",
            "data": {
                "key": {"remoteJid": "5511@s.whatsapp.net", "fromMe": True, "id": "123"},
                "message": {"conversation": "teste"}
            }
        })
        assert response.get_json()["status"] == "ignorado"

    @patch("main.gerar_resposta")
    @patch("main.buscar_contexto")
    @patch("main.requests.post")
    def test_webhook_processa_mensagem_valida(self, mock_post, mock_contexto, mock_llm, client):
        mock_contexto.return_value = "contexto"
        mock_llm.return_value = "Resposta de teste."
        mock_post.return_value = MagicMock(status_code=201)

        response = client.post("/webhook", json={
            "event": "messages.upsert",
            "data": {
                "key": {"remoteJid": "5511999999999@s.whatsapp.net", "fromMe": False, "id": "msg-unica-456"},
                "message": {"conversation": "Qual o horário?"}
            },
            "sender": "5511999999999@s.whatsapp.net"
        })
        assert response.status_code == 200
        assert response.get_json()["status"] == "ok"