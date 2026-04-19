# main.py
# Arquivo principal da aplicação - define as rotas HTTP e integração com WhatsApp

from flask import Flask, request, jsonify
from agente import buscar_resposta
from llm import gerar_resposta  # Geração de resposta natural via Groq
from database import (
    criar_tabela, criar_tabela_conhecimento,
    adicionar_conhecimento, salvar_conversa,
    buscar_historico, popular_conhecimento
)
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ─────────────────────────────────────────────
# CONFIGURAÇÕES — lidas do arquivo .env
# ─────────────────────────────────────────────
EVOLUTION_URL = os.getenv("EVOLUTION_URL", "http://localhost:8080")
EVOLUTION_KEY = os.getenv("EVOLUTION_KEY")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "final1")

# Evita processar a mesma mensagem duas vezes
# (o webhook pode disparar duplicado em algumas situações)
mensagens_processadas = set()


# ─────────────────────────────────────────────
# ROTA PRINCIPAL - Teste de funcionamento
# ─────────────────────────────────────────────
@app.route("/")
def home():
    return "Mini agente funcionando!"


# ─────────────────────────────────────────────
# ROTA /pergunta - Testa o agente via HTTP
# Útil para testar sem precisar do WhatsApp
# ─────────────────────────────────────────────
@app.route("/pergunta", methods=["POST"])
def pergunta():
    dados = request.get_json()

    if not dados or "mensagem" not in dados:
        return jsonify({"erro": "Campo 'mensagem' é obrigatório."}), 400

    mensagem = dados.get("mensagem")

    if not mensagem.strip():
        return jsonify({"erro": "Mensagem não pode estar vazia"}), 400

    # Passo 1: busca semântica encontra o contexto relevante no banco
    contexto = buscar_resposta(mensagem)

    # Passo 2: LLM gera uma resposta natural baseada no contexto
    resposta = gerar_resposta(mensagem, contexto)

    salvar_conversa(mensagem, resposta)
    return jsonify({"resposta": resposta})


# ─────────────────────────────────────────────
# ROTA /historico - Retorna conversas salvas
# ─────────────────────────────────────────────
@app.route("/historico", methods=["GET"])
def historico():
    dados = buscar_historico()
    resultado = []
    for pergunta, resposta, data in dados:
        resultado.append({
            "pergunta": pergunta,
            "resposta": resposta,
            "data": data
        })
    return jsonify(resultado)


# ─────────────────────────────────────────────
# ROTA /conhecimento - Adiciona nova resposta ao banco
# Permite adicionar categorias sem mexer no código
# ─────────────────────────────────────────────
@app.route("/conhecimento", methods=["POST"])
def adicionar():
    dados = request.get_json()

    if not dados or "categoria" not in dados or "keywords" not in dados or "resposta" not in dados:
        return jsonify({"erro": "Campos 'categoria', 'keywords', e 'resposta' são obrigatórios."}), 400

    categoria = dados.get("categoria")
    keywords = dados.get("keywords")
    resposta = dados.get("resposta")
    adicionar_conhecimento(categoria, keywords, resposta)
    return jsonify({"mensagem": "Conhecimento adicionado com sucesso!"})


# ─────────────────────────────────────────────
# ROTA /webhook - Recebe mensagens do WhatsApp
# A Evolution API chama esta rota automaticamente
# quando alguém manda mensagem para o número conectado
# ─────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    dados = request.get_json()

    # Ignora eventos que não são mensagens novas
    if not dados or dados.get("event") != "messages.upsert":
        return jsonify({"status": "ignorado"}), 200

    mensagem_obj = dados.get("data", {})

    # Ignora mensagens enviadas pelo próprio bot (evita loop infinito)
    if mensagem_obj.get("key", {}).get("fromMe"):
        return jsonify({"status": "ignorado"}), 200

    # Evita processar a mesma mensagem duas vezes
    msg_id = mensagem_obj.get("key", {}).get("id")
    if msg_id in mensagens_processadas:
        return jsonify({"status": "duplicado"}), 200
    mensagens_processadas.add(msg_id)

    # Extrai número e texto da mensagem
    remoteJid = mensagem_obj.get("key", {}).get("remoteJid")
    texto = (
        mensagem_obj.get("message", {}).get("conversation") or
        mensagem_obj.get("message", {}).get("extendedTextMessage", {}).get("text")
    )

    if not texto or not remoteJid:
        return jsonify({"status": "ignorado"}), 200

    # ── Resolução de @lid ──────────────────────────────────
    # O WhatsApp usa IDs anônimos (@lid) para contatos novos.
    # Tentamos resolver para o número real via Evolution API.
    if "@lid" in remoteJid:
        try:
            res = requests.post(
                f"{EVOLUTION_URL}/chat/whatsappNumbers/{INSTANCE_NAME}",
                headers={"apikey": EVOLUTION_KEY, "Content-Type": "application/json"},
                json={"numbers": [remoteJid]}
            )
            dados_res = res.json()
            if dados_res and len(dados_res) > 0 and dados_res[0].get("jid"):
                numero = dados_res[0].get("jid")
            else:
                numero = remoteJid
        except Exception as e:
            print("Erro ao resolver @lid:", e)
            numero = remoteJid
    else:
        numero = remoteJid

    print("Número:", numero)
    print("Texto:", texto)

    # Passo 1: busca semântica encontra o contexto relevante no banco
    contexto = buscar_resposta(texto)

    # Passo 2: LLM gera uma resposta natural baseada no contexto
    resposta = gerar_resposta(texto, contexto)

    salvar_conversa(texto, resposta)
    print("Resposta:", resposta)

    # Envia resposta de volta ao WhatsApp via Evolution API
    resultado = requests.post(
        f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}",
        headers={"apikey": EVOLUTION_KEY, "Content-Type": "application/json"},
        json={"number": numero, "text": resposta}
    )
    print("Status envio:", resultado.status_code)

    return jsonify({"status": "ok"}), 200


# ─────────────────────────────────────────────
# INICIALIZAÇÃO DA APLICAÇÃO
# ─────────────────────────────────────────────
if __name__ == "__main__":
    criar_tabela()              # Cria tabela de histórico de conversas
    criar_tabela_conhecimento() # Cria tabela de base de conhecimento
    popular_conhecimento()      # Popula com respostas iniciais se estiver vazia
    app.run(debug=True, port=5000, host="0.0.0.0")
    # host="0.0.0.0" permite que o Docker acesse o Flask