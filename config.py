import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "---")
ADMIN_TELEGRAM_ID: int = int(os.getenv("ADMIN_TELEGRAM_ID", "1002785084"))

GOOGLE_CREDENTIALS_PATH: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials/service_account.json")
GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "1LysG-xy86xTFFIid8M5RTOyzRPhjVgd1OmETsatb3EE")
GOOGLE_CALENDAR_ID: str = os.getenv("GOOGLE_CALENDAR_ID", "7cc3f5c1fa06faadd98c3b951602e9da0ae487cf188db697a8bbacac4dc06c07@group.calendar.google.com")

TIMEZONE: str = os.getenv("TIMEZONE", "Europe/Moscow")
WORK_SESSIONS = [
    ("09:00", "12:00"),
    ("13:00", "19:00"),
]
SLOT_STEP_MINUTES: int = 30

N8N_WEBHOOK_SECRET: str = os.getenv("N8N_WEBHOOK_SECRET", "")
API_PORT: int = int(os.getenv("API_PORT", "8080"))

BOT_NAME = "NailsBot"
MASTER_NAME = "Анастасия"
SALON_NAME = "Студия маникюра"
REMINDER_HOURS_BEFORE: int = 1
BOOKING_DAYS_AHEAD: int = 14
