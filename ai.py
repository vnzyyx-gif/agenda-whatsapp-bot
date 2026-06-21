import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


def interpretar_mensagem(message: str):
    system_prompt = """
Você é um assistente de agendamento por WhatsApp.

Extraia a intenção do usuário e responda SOMENTE em JSON válido.

Intenções possíveis:
- agendar
- consultar
- cancelar
- saudacao
- desconhecido

Formato obrigatório:
{
  "intent": "agendar",
  "client_name": null,
  "date_text": "amanhã",
  "time_text": "15h",
  "service": "Jogo do Brasil"
}

Regras:
- Se não houver data, use null.
- Se não houver horário, use null.
- Se o usuário escrever algo depois de dois pontos, como "19h: Jogo do Brasil", use isso como service.
- Se não houver nome do cliente, use null.
- Se o usuário pedir para cancelar, a intent deve ser "cancelar".
- Não invente informações.
- Não escreva explicações fora do JSON.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "intent": "desconhecido",
            "client_name": None,
            "date_text": None,
            "time_text": None,
            "service": None
        }