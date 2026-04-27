import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

cliente = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODELO = "llama-3.3-70b-versatile"
MAX_HISTORICO = 10


def gerar_resposta(pergunta: str, contexto: str, historico: list = []) -> str:
    system_prompt = """Você é um assistente de atendimento de uma academia.
Responda de forma simpática, clara e objetiva.
Use apenas as informações fornecidas no contexto para responder.
Se a informação não estiver no contexto, diga educadamente que não tem essa informação no momento.
Responda sempre em português."""

    user_prompt_atual = f"""Contexto com informações da academia:
{contexto}

Pergunta do cliente: {pergunta}"""
    historico_recente = historico[-MAX_HISTORICO:]
    mensagens = (
        [{"role": "system", "content": system_prompt}]
        + historico_recente
        + [{"role": "user", "content": user_prompt_atual}]
    )

    resposta = cliente.chat.completions.create(
        model=MODELO,
        messages=mensagens,
        max_tokens=300,
        temperature=0.7
    )

    return resposta.choices[0].message.content.strip()