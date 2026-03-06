from flask import Flask, request, jsonify
from agente import buscar_resposta

app = Flask(__name__)

@app.route("/")
def home():
    return "Mini agente funcionando!"

@app.route("/pergunta", methods=["POST"])
def pergunta():

    dados = request.get_json()
    mensagem = dados.get("mensagem")

    resposta = buscar_resposta(mensagem)

    return jsonify({
        "resposta": resposta
    })


if __name__ == "__main__":
    app.run(debug=True)