from flask import Flask, request, jsonify
from agente import buscar_resposta 
from database import (
    criar_tabela, criar_tabela_conhecimento,
    adicionar_conhecimento, salvar_conversa,
    buscar_historico, popular_conhecimento
)
import requests  # Para fazer requisições HTTP para a Evolution API
import os
from dotenv import load_dotenv


app = Flask(__name__)


load_dotenv()

EVOLUTION_URL = os.getenv("EVOLUTION_URL", "http://localhost:8080")
EVOLUTION_KEY = os.getenv("EVOLUTION_KEY")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "final1")

# Conjunto para evitar processar a mesma mensagem duas vezes
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

    # Valida se o campo 'mensagem' foi enviado
    if not dados or "mensagem" not in dados:
        return jsonify({"erro": "Campo 'mensagem' é obrigatório."}), 400
    
    mensagem = dados.get("mensagem")

    # Valida se a mensagem não está vazia
    if not mensagem.strip():
        return jsonify({"erro": "Mensagem não pode estar vazia"}), 400
    
    resposta = buscar_resposta(mensagem)
    salvar_conversa(mensagem, resposta)
    return jsonify({"resposta": resposta})


# - Retorna conversas salvas
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


# Adiciona nova resposta ao banco
# Permite adicionar categorias sem mexer no código
@app.route("/conhecimento", methods=["POST"])
def adicionar():
    dados = request.get_json()

    # Valida se todos os campos obrigatórios foram enviados
    if not dados or "categoria" not in dados or "keywords" not in dados or "resposta" not in dados:
        return jsonify({"erro": "Campos 'categoria', 'keywords', e 'resposta' são obrigatórios."}), 400
    
    categoria = dados.get("categoria")
    keywords = dados.get("keywords")
    resposta = dados.get("resposta")
    adicionar_conhecimento(categoria, keywords, resposta)
    return jsonify({"mensagem": "Conhecimento adicionado com sucesso!"})


# Recebe mensagens do WhatsApp
# A Evolution API chama esta rota automaticamente quando alguém manda mensagem para o número conectado
@app.route("/webhook", methods=["POST"])
def webhook():
    dados = request.get_json()

    # Ignora eventos que não são mensagens novas
    if not dados or dados.get("event") != "messages.upsert":
        return jsonify({"status": "ignorado"}), 200

    mensagem_obj = dados.get("data", {})

    # Ignora mensagens enviadas pelo próprio bot
    if mensagem_obj.get("key", {}).get("fromMe"):
        return jsonify({"status": "ignorado"}), 200

    # Verifica se essa mensagem já foi processada
    msg_id = mensagem_obj.get("key", {}).get("id")
    if msg_id in mensagens_processadas:
        return jsonify({"status": "duplicado"}), 200
    mensagens_processadas.add(msg_id)

    # Pega o ID do remetente e o texto da mensagem
    remoteJid = mensagem_obj.get("key", {}).get("remoteJid")
    texto = (
        mensagem_obj.get("message", {}).get("conversation") or
        mensagem_obj.get("message", {}).get("extendedTextMessage", {}).get("text")
    )

    # Ignora se não tiver texto ou número
    if not texto or not remoteJid:
        return jsonify({"status": "ignorado"}), 200

    # Resolução do @lid 
    # O WhatsApp passou a usar IDs anônimos (@lid) em vez do número real para contatos novos.
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
                # Se não resolver, usa o @lid mesmo (pode falhar no envio)
                numero = remoteJid
        except Exception as e:
            print("Erro ao resolver @lid:", e)
            numero = remoteJid
    else:
        # Número normal no formato 5511999999999@s.whatsapp.net
        numero = remoteJid

    print("Número:", numero)
    print("Texto:", texto)

    # Busca a resposta usando busca semântica (sentence-transformers)
    resposta = buscar_resposta(texto)
    salvar_conversa(texto, resposta)
    print("Resposta:", resposta)

    # Envia a resposta de volta para o WhatsApp via Evolution API
    resultado = requests.post(
        f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}",
        headers={"apikey": EVOLUTION_KEY, "Content-Type": "application/json"},
        json={"number": numero, "text": resposta}
    )
    print("Status envio:", resultado.status_code)

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    criar_tabela()           
    criar_tabela_conhecimento() 
    popular_conhecimento()      
    app.run(debug=True, port=5000, host="0.0.0.0")