import sqlite3
from datetime import datetime

DB_NAME = "agenda.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            phone TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT DEFAULT 'confirmed',
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def is_slot_available(date: str, time: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM appointments
        WHERE date = ? AND time = ? AND status = 'confirmed'
    """, (date, time))

    result = cursor.fetchone()
    conn.close()

    return result is None


def create_appointment(client_name: str, phone: str, date: str, time: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO appointments (client_name, phone, date, time, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        client_name,
        phone,
        date,
        time,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def list_appointments_by_phone(phone: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, time, status
        FROM appointments
        WHERE phone = ?
        ORDER BY date, time
    """, (phone,))

    rows = cursor.fetchall()
    conn.close()

    return rows

def init_memory_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            title TEXT NOT NULL,
            service TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            google_event_id TEXT,
            status TEXT DEFAULT 'confirmed',
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_memory (
            phone TEXT PRIMARY KEY,
            last_intent TEXT,
            date_text TEXT,
            time_text TEXT,
            service TEXT,
            updated_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_bot_event(phone, title, service, date, time, google_event_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO bot_events (
            phone, title, service, date, time, google_event_id, status, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, 'confirmed', ?)
    """, (
        phone,
        title,
        service,
        date,
        time,
        google_event_id,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def get_last_bot_event(phone):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, service, date, time, google_event_id
        FROM bot_events
        WHERE phone = ? AND status = 'confirmed'
        ORDER BY id DESC
        LIMIT 1
    """, (phone,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "title": row[1],
        "service": row[2],
        "date": row[3],
        "time": row[4],
        "google_event_id": row[5]
    }


def find_bot_events_by_service(phone, service_text):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, service, date, time, google_event_id
        FROM bot_events
        WHERE phone = ?
          AND status = 'confirmed'
          AND (
            LOWER(title) LIKE LOWER(?)
            OR LOWER(service) LIKE LOWER(?)
          )
        ORDER BY date, time
    """, (
        phone,
        f"%{service_text}%",
        f"%{service_text}%"
    ))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "service": row[2],
            "date": row[3],
            "time": row[4],
            "google_event_id": row[5]
        }
        for row in rows
    ]


def mark_bot_event_cancelled(event_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE bot_events
        SET status = 'cancelled'
        WHERE id = ?
    """, (event_id,))

    conn.commit()
    conn.close()


def list_confirmed_bot_events(phone):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, service, date, time
        FROM bot_events
        WHERE phone = ? AND status = 'confirmed'
        ORDER BY date, time
    """, (phone,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "service": row[2],
            "date": row[3],
            "time": row[4]
        }
        for row in rows
    ]


def save_conversation_memory(phone, last_intent=None, date_text=None, time_text=None, service=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO conversation_memory (
            phone, last_intent, date_text, time_text, service, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(phone) DO UPDATE SET
            last_intent = excluded.last_intent,
            date_text = excluded.date_text,
            time_text = excluded.time_text,
            service = excluded.service,
            updated_at = excluded.updated_at
    """, (
        phone,
        last_intent,
        date_text,
        time_text,
        service,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def get_conversation_memory(phone):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT last_intent, date_text, time_text, service
        FROM conversation_memory
        WHERE phone = ?
    """, (phone,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return {}

    return {
        "last_intent": row[0],
        "date_text": row[1],
        "time_text": row[2],
        "service": row[3]
    }


def clear_conversation_memory(phone):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM conversation_memory
        WHERE phone = ?
    """, (phone,))

    conn.commit()
    conn.close()