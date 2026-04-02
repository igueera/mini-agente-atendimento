from sentence_transformers import SentenceTransformer, util

modelo = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

print("Modelo carregado")

def buscar_semantico(pergunta, conhecimento):
    embedding_pergunta = modelo.encode(pergunta, convert_to_tensor=True)

    melhor_score = -1
    melhor_resposta = None

    for item in conhecimento:
        texto_comparacao = item["categoria"] + " " + " ".join(item["keywords"])
        embedding_categoria = modelo.encode(texto_comparacao, convert_to_tensor=True)
        score = util.cos_sim(embedding_pergunta, embedding_categoria).item()

        if score > melhor_score:
            melhor_score = score
            melhor_resposta = item["resposta"]

    if melhor_score > 0.3:
        return melhor_resposta

    return "Desculpe, não entendi sua pergunta."

