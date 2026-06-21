from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime
import dateparser
import re
import traceback

from google_calendar import (
    criar_evento_google_agenda,
    verificar_horario_livre,
    cancelar_eventos_no_horario
)

from database import (
    init_db,
    init_memory_db,
    save_bot_event,
    get_last_bot_event,
    find_bot_events_by_service,
    mark_bot_event_cancelled,
    list_confirmed_bot_events,
    save_conversation_memory,
    get_conversation_memory,
    clear_conversation_memory
)

from ai import interpretar_mensagem


app = Flask(__name__)

init_db()
init_memory_db()


def responder_twilio(response):
    return Response(str(response), mimetype="application/xml")


def normalizar_data(date_text: str):
    if not date_text:
        return None

    parsed = dateparser.parse(
        date_text,
        languages=["pt"],
        settings={
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": datetime.now()
        }
    )

    if not parsed:
        return None

    return parsed.strftime("%Y-%m-%d")


def normalizar_horario(time_text: str):
    if not time_text:
        return None

    texto = time_text.lower().strip()

    match = re.search(r'\b(\d{1,2})\s*(?:h|:)?\s*(\d{2})?\b', texto)

    if not match:
        return None

    hora = int(match.group(1))
    minuto = int(match.group(2)) if match.group(2) else 0

    if hora < 0 or hora > 23:
        return None

    if minuto < 0 or minuto > 59:
        return None

    return f"{hora:02d}:{minuto:02d}"


def mensagem_tem_cancelamento(texto: str):
    palavras_cancelamento = [
        "cancelar",
        "cancela",
        "cancele",
        "deletar",
        "deleta",
        "apagar",
        "apaga",
        "desistir",
        "desisti",
        "deixa pra lá",
        "deixa para lá",
        "não quero mais"
    ]

    return any(palavra in texto for palavra in palavras_cancelamento)


def mensagem_tem_agendamento(texto: str):
    palavras_agendamento = [
        "marcar",
        "marca",
        "agendar",
        "agende",
        "criar compromisso",
        "cria compromisso"
    ]

    return any(palavra in texto for palavra in palavras_agendamento)


def mensagem_tem_consulta(texto: str):
    palavras_consulta = [
        "quais",
        "consultar",
        "consulta",
        "ver meus",
        "meus compromissos",
        "compromissos",
        "horários",
        "horarios",
        "o que tenho",
        "tenho algo"
    ]

    return any(palavra in texto for palavra in palavras_consulta)


@app.route("/", methods=["GET"])
def home():
    return "Servidor Flask funcionando!"


@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    incoming_msg = request.values.get("Body", "").strip()
    phone = request.values.get("From", "").replace("whatsapp:", "")
    profile_name = request.values.get("ProfileName", "Cliente WhatsApp")

    response = MessagingResponse()
    msg = response.message()

    try:
        if not incoming_msg:
            msg.body("Não consegui ler sua mensagem. Pode tentar novamente?")
            return responder_twilio(response)

        data = interpretar_mensagem(incoming_msg)

        intent = data.get("intent")
        client_name = data.get("client_name")
        date_text = data.get("date_text")
        time_text = data.get("time_text")
        service = data.get("service")

        texto_usuario = incoming_msg.lower()

        if mensagem_tem_cancelamento(texto_usuario):
            intent = "cancelar"

        elif mensagem_tem_agendamento(texto_usuario):
            intent = "agendar"

        elif mensagem_tem_consulta(texto_usuario):
            intent = "consultar"

        state = get_conversation_memory(phone)

        if intent in ["desconhecido", "saudacao", "consultar"]:
            if state.get("last_intent") in ["agendar", "cancelar"]:
                intent = state.get("last_intent")

        if not date_text and state.get("date_text"):
            date_text = state.get("date_text")

        if not time_text and state.get("time_text"):
            time_text = state.get("time_text")

        if not service and state.get("service"):
            service = state.get("service")

        if intent == "saudacao":
            msg.body(
                "Olá! Sou seu assistente de agendamentos. 📖"
                "Você pode dizer algo como: 'Quero marcar amanhã às 15h'."
            )
            return responder_twilio(response)

        if intent == "consultar":
            eventos = list_confirmed_bot_events(phone)

            if not eventos:
                msg.body("Você não tem compromissos criados no momento.")
                return responder_twilio(response)

            date = normalizar_data(date_text)

            if date:
                eventos = [evento for evento in eventos if evento["date"] == date]

                if not eventos:
                    msg.body(f"Você não tem compromissos criados em {date}.")
                    return responder_twilio(response)

                texto = f"Seus compromissos em {date}:\n\n"
            else:
                texto = "Seus compromissos criados:\n\n"

            for evento in eventos:
                texto += f"- {evento['title']} às {evento['time']}\n"

            msg.body(texto)
            return responder_twilio(response)

        if intent == "agendar":
            date = normalizar_data(date_text)
            time = normalizar_horario(time_text)

            if not date:
                save_conversation_memory(
                    phone=phone,
                    last_intent="agendar",
                    date_text=date_text,
                    time_text=time_text,
                    service=service
                )

                msg.body("Claro! Para qual dia você quer agendar?")
                return responder_twilio(response)

            if not time:
                save_conversation_memory(
                    phone=phone,
                    last_intent="agendar",
                    date_text=date_text,
                    time_text=time_text,
                    service=service
                )

                msg.body("Perfeito. Qual horário você prefere?")
                return responder_twilio(response)

            if not verificar_horario_livre(date, time):
                save_conversation_memory(
                    phone=phone,
                    last_intent="agendar",
                    date_text=date_text,
                    time_text=time_text,
                    service=service
                )

                msg.body(
                    f"Esse horário já está ocupado no Google Agenda: {date} às {time}. "
                    "Você pode me enviar outro horário ou dizer: 'cancelar esse horário'."
                )
                return responder_twilio(response)

            titulo = f"{service or 'Agendamento'} - {client_name or profile_name or phone}"

            evento_criado = criar_evento_google_agenda(
                titulo=titulo,
                data=date,
                horario=time,
                duracao_minutos=60
            )

            save_bot_event(
                phone=phone,
                title=titulo,
                service=service,
                date=date,
                time=time,
                google_event_id=evento_criado.get("id")
            )

            clear_conversation_memory(phone)

            msg.body(
                f"Agendamento confirmado no Google Agenda para {date} às {time}. "
                "Obrigado!"
            )
            return responder_twilio(response)

        if intent == "cancelar":
            date = normalizar_data(date_text)
            time = normalizar_horario(time_text)

            last_event = get_last_bot_event(phone)

            if not date and not time and last_event:
                cancelados = cancelar_eventos_no_horario(
                    last_event["date"],
                    last_event["time"]
                )

                if cancelados == 0:
                    msg.body(
                        f"Eu encontrei na memória, mas não achei no Google Agenda: "
                        f"{last_event['title']} em {last_event['date']} às {last_event['time']}."
                    )
                    return responder_twilio(response)

                mark_bot_event_cancelled(last_event["id"])
                clear_conversation_memory(phone)

                msg.body(
                    f"Pronto, cancelei: {last_event['title']} "
                    f"em {last_event['date']} às {last_event['time']}."
                )
                return responder_twilio(response)

            if service and not date and not time:
                eventos = find_bot_events_by_service(phone, service)

                if len(eventos) == 1:
                    evento = eventos[0]

                    cancelados = cancelar_eventos_no_horario(
                        evento["date"],
                        evento["time"]
                    )

                    if cancelados == 0:
                        msg.body(
                            f"Encontrei na memória, mas não achei no Google Agenda: "
                            f"{evento['title']} em {evento['date']} às {evento['time']}."
                        )
                        return responder_twilio(response)

                    mark_bot_event_cancelled(evento["id"])
                    clear_conversation_memory(phone)

                    msg.body(
                        f"Pronto, cancelei: {evento['title']} "
                        f"em {evento['date']} às {evento['time']}."
                    )
                    return responder_twilio(response)

                if len(eventos) > 1:
                    texto = "Encontrei mais de um compromisso parecido. Qual deles você quer cancelar?\n\n"

                    for evento in eventos:
                        texto += f"- {evento['title']} em {evento['date']} às {evento['time']}\n"

                    save_conversation_memory(
                        phone=phone,
                        last_intent="cancelar",
                        date_text=date_text,
                        time_text=time_text,
                        service=service
                    )

                    msg.body(texto)
                    return responder_twilio(response)

            if not date:
                save_conversation_memory(
                    phone=phone,
                    last_intent="cancelar",
                    date_text=date_text,
                    time_text=time_text,
                    service=service
                )

                msg.body("Claro. Qual dia você quer cancelar?")
                return responder_twilio(response)

            if not time:
                if last_event and last_event.get("date") == date:
                    time = last_event.get("time")
                else:
                    save_conversation_memory(
                        phone=phone,
                        last_intent="cancelar",
                        date_text=date_text,
                        time_text=time_text,
                        service=service
                    )

                    msg.body("Qual horário você quer cancelar?")
                    return responder_twilio(response)

            cancelados = cancelar_eventos_no_horario(date, time)

            if cancelados == 0:
                msg.body(f"Não encontrei nenhum evento em {date} às {time}.")
                return responder_twilio(response)

            if last_event and last_event.get("date") == date and last_event.get("time") == time:
                mark_bot_event_cancelled(last_event["id"])

            clear_conversation_memory(phone)

            msg.body(f"Evento cancelado no Google Agenda: {date} às {time}.")
            return responder_twilio(response)

        msg.body(
            "Não entendi muito bem. Você pode escrever, por exemplo: "
            "'Quero marcar amanhã às 15h', 'Quais são meus compromissos?' "
            "ou 'Cancelar amanhã às 15h'."
        )

        return responder_twilio(response)

    except Exception as e:
        print("ERRO NO WEBHOOK:")
        print(e)
        traceback.print_exc()

        msg.body(
            "Tive um erro interno ao processar sua mensagem. "
            "Olhe o terminal onde está rodando o python app.py."
        )
        return responder_twilio(response)


if __name__ == "__main__":
    app.run(debug=True, port=5000)