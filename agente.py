from database import buscar_conhecimento
from utils import limpar_texto

def buscar_resposta(pergunta):
    pergunta = limpar_texto(pergunta)
    palavras = pergunta.split()
    categorias_detectadas = []

    conhecimento = buscar_conhecimento()

    for categoria in conhecimento:
        pontuacao = 0

        for keyword in categoria["keywords"]:
            if keyword in palavras:
                pontuacao += 1

        if pontuacao > 0:
            categorias_detectadas.append((pontuacao, categoria["resposta"]))

    if categorias_detectadas:
        categorias_detectadas.sort(key=lambda x: x[0], reverse=True)
        respostas_ordenadas = [resposta for pontuacao, resposta in categorias_detectadas]
        return "\n\n".join(respostas_ordenadas)

    return "Desculpe, não entendi sua pergunta."

print("Arquivo agente carregado")