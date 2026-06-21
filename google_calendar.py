from datetime import datetime, timedelta
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_calendar_service():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def criar_evento_google_agenda(titulo, data, horario, duracao_minutos=60):
    service = get_calendar_service()

    inicio = datetime.fromisoformat(f"{data}T{horario}:00")
    fim = inicio + timedelta(minutes=duracao_minutos)

    evento = {
        "summary": titulo,
        "description": "Agendamento criado automaticamente pelo bot do WhatsApp.",
        "start": {
            "dateTime": inicio.isoformat(),
            "timeZone": "America/Sao_Paulo",
        },
        "end": {
            "dateTime": fim.isoformat(),
            "timeZone": "America/Sao_Paulo",
        },
    }

    evento_criado = service.events().insert(
        calendarId="primary",
        body=evento
    ).execute()

    return evento_criado


def verificar_horario_livre(data, horario, duracao_minutos=60):
    service = get_calendar_service()

    inicio = datetime.fromisoformat(f"{data}T{horario}:00")
    fim = inicio + timedelta(minutes=duracao_minutos)

    eventos_resultado = service.events().list(
        calendarId="primary",
        timeMin=inicio.isoformat() + "-03:00",
        timeMax=fim.isoformat() + "-03:00",
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    eventos = eventos_resultado.get("items", [])

    return len(eventos) == 0

def cancelar_eventos_no_horario(data, horario, duracao_minutos=60):
    service = get_calendar_service()

    inicio = datetime.fromisoformat(f"{data}T{horario}:00")
    fim = inicio + timedelta(minutes=duracao_minutos)

    eventos_resultado = service.events().list(
        calendarId="primary",
        timeMin=inicio.isoformat() + "-03:00",
        timeMax=fim.isoformat() + "-03:00",
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    eventos = eventos_resultado.get("items", [])

    if not eventos:
        return 0

    cancelados = 0

    for evento in eventos:
        service.events().delete(
            calendarId="primary",
            eventId=evento["id"]
        ).execute()

        cancelados += 1

    return cancelados