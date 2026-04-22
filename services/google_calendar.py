import logging
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import GOOGLE_CREDENTIALS_PATH, GOOGLE_CALENDAR_ID, TIMEZONE, MASTER_NAME

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _svc():
    creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH, scopes=SCOPES)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def create_event(booking_date, booking_time, duration_minutes, client_name,
                 client_phone, service_name, payment, booking_id) -> str:
    try:
        start = datetime.fromisoformat(f"{booking_date}T{booking_time}:00")
        end   = start + timedelta(minutes=duration_minutes)
        event = {
            "summary": f"💅 {service_name} — {client_name}",
            "description": f"Клиент: {client_name}\nТелефон: {client_phone}\nУслуга: {service_name}\nОплата: {payment}\nID: {booking_id}\nМастер: {MASTER_NAME}",
            "start": {"dateTime": start.isoformat(), "timeZone": TIMEZONE},
            "end":   {"dateTime": end.isoformat(),   "timeZone": TIMEZONE},
            "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 30}]},
        }
        created = _svc().events().insert(calendarId=GOOGLE_CALENDAR_ID, body=event).execute()
        return created.get("id", "")
    except Exception as e:
        logger.error("Calendar create_event: %s", e); return ""


def delete_event(event_id: str) -> bool:
    if not event_id: return False
    try:
        _svc().events().delete(calendarId=GOOGLE_CALENDAR_ID, eventId=event_id).execute()
        return True
    except Exception as e:
        logger.error("Calendar delete_event: %s", e); return False
