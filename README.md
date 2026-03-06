# Mini Agente de Atendimento (Python)

Projeto de um mini agente de atendimento para negócios locais.

## Tecnologias

- Python
- Flask
- Processamento de texto
- API REST

## Funcionalidades

- Responde perguntas sobre:
  - horário
  - planos
  - localização
- Detecta múltiplas intenções
- Ordena respostas por relevância

## Exemplo de uso

POST /pergunta

{
 "mensagem": "Qual o horário e onde fica?"
}

Resposta:

{
 "resposta": "Funcionamos das 6h às 22h...\n\nEstamos localizados..."
}

## Objetivo

Projeto criado para estudo de:

- Python
- APIs
- Lógica de agentes