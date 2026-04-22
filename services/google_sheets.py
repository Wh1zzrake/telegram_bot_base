"""
Google Sheets — структура листа "Записи":
  A=ID  B=Дата  C=Время  D=Имя клиента  E=Телефон
  F=Услуга  G=Длительность(мин)  H=Цена(₽)  I=Оплата
  J=Мастер  K=Статус  L=Telegram ID  M=Google Event ID
"""
import logging, uuid
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from config import GOOGLE_CREDENTIALS_PATH, GOOGLE_SHEET_ID, MASTER_NAME

logger = logging.getLogger(__name__)

SCOPES     = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.readonly"]
SHEET_NAME = "Записи"
HEADERS    = ["ID","Дата","Время","Имя клиента","Телефон","Услуга",
               "Длительность (мин)","Цена (₽)","Оплата","Мастер","Статус","Telegram ID","Google Event ID"]


def _sheet() -> gspread.Worksheet:
    creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH, scopes=SCOPES)
    client = gspread.authorize(creds)
    sp = client.open_by_key(GOOGLE_SHEET_ID)
    try:
        return sp.worksheet(SHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = sp.add_worksheet(title=SHEET_NAME, rows=1000, cols=len(HEADERS))
        ws.append_row(HEADERS, value_input_option="USER_ENTERED")
        return ws


def add_booking(booking_date, booking_time, client_name, client_phone,
                service_name, duration_minutes, price, payment, telegram_id, google_event_id="") -> str:
    bid = str(uuid.uuid4())[:8].upper()
    row = [bid, booking_date, booking_time, client_name, client_phone,
           service_name, duration_minutes, price, payment, MASTER_NAME,
           "active", str(telegram_id), google_event_id]
    try:
        _sheet().append_row(row, value_input_option="USER_ENTERED")
    except Exception as e:
        logger.error("Sheets add_booking: %s", e)
    return bid


def get_bookings_for_date(booking_date: str) -> list[dict]:
    try:
        return [r for r in _sheet().get_all_records() if r.get("Дата") == booking_date and r.get("Статус") == "active"]
    except Exception as e:
        logger.error("Sheets get_date: %s", e); return []


def get_bookings_for_period(date_from: str, date_to: str) -> list[dict]:
    try:
        return [r for r in _sheet().get_all_records()
                if r.get("Статус") == "active" and date_from <= r.get("Дата","") <= date_to]
    except Exception as e:
        logger.error("Sheets get_period: %s", e); return []


def get_bookings_for_client(telegram_id: int) -> list[dict]:
    try:
        today = date.today().isoformat()
        return [r for r in _sheet().get_all_records()
                if str(r.get("Telegram ID")) == str(telegram_id)
                and r.get("Статус") == "active" and r.get("Дата","") >= today]
    except Exception as e:
        logger.error("Sheets get_client: %s", e); return []


def cancel_booking(booking_id: str) -> bool:
    try:
        ws = _sheet()
        for i, row in enumerate(_sheet().get_all_records(), start=2):
            if str(row.get("ID")) == str(booking_id):
                ws.update_cell(i, HEADERS.index("Статус") + 1, "cancelled")
                return True
        return False
    except Exception as e:
        logger.error("Sheets cancel: %s", e); return False


def update_event_id(booking_id: str, event_id: str) -> None:
    try:
        ws = _sheet()
        for i, row in enumerate(_sheet().get_all_records(), start=2):
            if str(row.get("ID")) == str(booking_id):
                ws.update_cell(i, HEADERS.index("Google Event ID") + 1, event_id)
                return
    except Exception as e:
        logger.error("Sheets update_event_id: %s", e)


def get_upcoming_reminders(target: str) -> list[dict]:
    try:
        target_date, target_time = target.split(" ")
        return [r for r in _sheet().get_all_records()
                if r.get("Статус") == "active" and r.get("Дата") == target_date and r.get("Время") == target_time]
    except Exception as e:
        logger.error("Sheets reminders: %s", e); return []
