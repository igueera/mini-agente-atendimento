from flask import Flask, request, jsonify
from agente import buscar_resposta
from database import criar_tabela, criar_tabela_conhecimento, adicionar_conhecimento, salvar_conversa, buscar_historico, popular_conhecimento
from database import salvar_conversa, buscar_historico

app = Flask(__name__)

@app.route("/")
def home():
    return "Mini agente funcionando!"

@app.route("/pergunta", methods=["POST"])
def pergunta():

    dados = request.get_json()
    if not dados or "mensagem" not in dados:
        return jsonify({"erro": "Campo 'mensagem' é obrigatório."}), 400
    
    mensagem = dados.get("mensagem")
    if not mensagem.strip():
        return jsonify({"erro": "Mensagem não pode estar vazia"}), 400

    resposta = buscar_resposta(mensagem)
    salvar_conversa(mensagem, resposta)

    return jsonify({
        "resposta": resposta
    })

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

if __name__ == "__main__":
    criar_tabela()
    criar_tabela_conhecimento()
    popular_conhecimento()
    app.run(debug=True)