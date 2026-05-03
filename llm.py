# Responsável por se comunicar com a API da Groq
# e gerar respostas naturais baseadas no contexto do banco de conhecimento

import os
from groq import Groq
from dotenv import load_dotenv
from logger import get_logger

load_dotenv()

logger = get_logger(__name__)
cliente = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODELO = "llama-3.3-70b-versatile"
MAX_HISTORICO = 10
FALLBACK = "Desculpe, estou com dificuldades técnicas no momento. Por favor, tente novamente em alguns instantes."


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

    try:
        resposta = cliente.chat.completions.create(
            model=MODELO,
            messages=mensagens,
            max_tokens=300,
            temperature=0.7
        )
        return resposta.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Erro ao chamar Groq API: {e}")
        return FALLBACK