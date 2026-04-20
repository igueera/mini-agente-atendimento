# llm.py
# Responsável por se comunicar com a API da Groq
# e gerar respostas naturais baseadas no contexto do banco de conhecimento

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Inicializa o cliente da Groq com a chave do .env
cliente = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Modelo utilizado — llama3 é rápido e muito capaz
MODELO = "llama-3.3-70b-versatile"

def gerar_resposta(pergunta: str, contexto: str) -> str:
    """
    Recebe a pergunta do usuário e o contexto encontrado no banco
    e pede para o LLM gerar uma resposta natural.
    """

    # O system prompt define o comportamento do agente
    system_prompt = """Você é um assistente de atendimento de uma academia.
Responda de forma simpática, clara e objetiva.
Use apenas as informações fornecidas no contexto para responder.
Se a informação não estiver no contexto, diga educadamente que não tem essa informação no momento.
Responda sempre em português."""

    # O user prompt junta o contexto do banco com a pergunta do usuário
    user_prompt = f"""Contexto com informações da academia:
{contexto}

Pergunta do cliente: {pergunta}"""

    # Chama a API da Groq
    resposta = cliente.chat.completions.create(
        model=MODELO,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=300,
        temperature=0.7  # 0 = mais preciso, 1 = mais criativo
    )

    return resposta.choices[0].message.content.strip()