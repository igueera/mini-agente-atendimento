from database import buscar_conhecimento
from utils import limpar_texto
from semantic import buscar_semantico

def buscar_resposta(pergunta):
    pergunta = limpar_texto(pergunta)
    conhecimento = buscar_conhecimento()

    return buscar_semantico(pergunta, conhecimento)

print("Arquivo agente carregado")