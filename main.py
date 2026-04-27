# main.py
# Arquivo principal da aplicação - define as rotas HTTP e integração com WhatsApp

from flask import Flask, request, jsonify
from rag import buscar_contexto
from llm import gerar_resposta
from database import (
    criar_tabela, criar_tabela_conhecimento, criar_tabela_memoria,
    adicionar_conhecimento, salvar_conversa,
    buscar_historico, popular_conhecimento,
    buscar_memoria, salvar_memoria
)
# ── Por que importar buscar_memoria e salvar_memoria? ────
# São as duas novas funções do database.py que criamos.
# buscar_memoria traz o histórico do cliente antes de responder.
# salvar_memoria atualiza o histórico após cada resposta.
# ─────────────────────────────────────────────────────────
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

    # ── Por que usar "teste" como número fixo aqui? ──────
    # A rota /pergunta é para testes via Postman/HTTP,
    # sem um número de WhatsApp real. Usamos "teste" como
    # identificador fixo para que o histórico de teste
    # fique separado dos históricos reais de clientes.
    # ─────────────────────────────────────────────────────
    numero_teste = "teste"
    historico = buscar_memoria(numero_teste)

    contexto = buscar_contexto(mensagem)
    resposta = gerar_resposta(mensagem, contexto, historico)

    # ── Por que atualizar o histórico após responder? ────
    # O histórico é uma lista crescente de mensagens.
    # Após cada troca, adicionamos a pergunta do usuário
    # e a resposta do assistente — mantendo o formato
    # que o LLM espera: role "user" e role "assistant".
    # ─────────────────────────────────────────────────────
    historico.append({"role": "user", "content": mensagem})
    historico.append({"role": "assistant", "content": resposta})
    salvar_memoria(numero_teste, historico)

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
# ─────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    dados = request.get_json()

    if not dados or dados.get("event") != "messages.upsert":
        return jsonify({"status": "ignorado"}), 200

    mensagem_obj = dados.get("data", {})

    if mensagem_obj.get("key", {}).get("fromMe"):
        return jsonify({"status": "ignorado"}), 200

    msg_id = mensagem_obj.get("key", {}).get("id")
    if msg_id in mensagens_processadas:
        return jsonify({"status": "duplicado"}), 200
    mensagens_processadas.add(msg_id)

    remoteJid = mensagem_obj.get("key", {}).get("remoteJid")
    texto = (
        mensagem_obj.get("message", {}).get("conversation") or
        mensagem_obj.get("message", {}).get("extendedTextMessage", {}).get("text")
    )

    if not texto or not remoteJid:
        return jsonify({"status": "ignorado"}), 200

    # Resolução de @lid
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

    # ── Por que buscar a memória pelo número? ────────────
    # Cada cliente tem seu próprio histórico identificado
    # pelo número de telefone. Assim o agente lembra o
    # contexto de cada pessoa separadamente — o histórico
    # do cliente A não se mistura com o do cliente B.
    # ─────────────────────────────────────────────────────
    historico = buscar_memoria(numero)

    contexto = buscar_contexto(texto)
    resposta = gerar_resposta(texto, contexto, historico)

    # ── Por que salvar antes de enviar? ──────────────────
    # Salvamos o histórico atualizado antes de enviar a
    # resposta ao WhatsApp. Se o envio falhar por algum
    # motivo, o histórico já está salvo e a próxima mensagem
    # do cliente ainda terá contexto correto.
    # ─────────────────────────────────────────────────────
    historico.append({"role": "user", "content": texto})
    historico.append({"role": "assistant", "content": resposta})
    salvar_memoria(numero, historico)

    salvar_conversa(texto, resposta)
    print("Resposta:", resposta)

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
    criar_tabela()
    criar_tabela_conhecimento()
    criar_tabela_memoria()      # Cria a nova tabela de memória por número
    popular_conhecimento()
    app.run(debug=True, port=5000, host="0.0.0.0")