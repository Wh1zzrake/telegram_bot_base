import logging
from datetime import datetime, timedelta
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from config import ADMIN_TELEGRAM_ID, REMINDER_HOURS_BEFORE, TIMEZONE
from services import google_sheets

logger = logging.getLogger(__name__)


async def send_reminders(bot: Bot) -> None:
    tz       = pytz.timezone(TIMEZONE)
    target   = (datetime.now(tz) + timedelta(hours=REMINDER_HOURS_BEFORE)).strftime("%Y-%m-%d %H:%M")
    MONTHS   = ["янв","фев","мар","апр","май","июн","июл","авг","сен","окт","ноя","дек"]

    for b in google_sheets.get_upcoming_reminders(target):
        name, svc = b.get("Имя клиента",""), b.get("Услуга","")
        d_str = b.get("Дата","")
        try:
            from datetime import datetime as dt
            d = dt.strptime(d_str, "%Y-%m-%d")
            d_fmt = f"{d.day} {MONTHS[d.month-1]}"
        except Exception:
            d_fmt = d_str

        client_msg = (
            f"⏰ *Напоминание о записи*\n\n"
            f"Привет, {name}!\n"
            f"Через {REMINDER_HOURS_BEFORE} ч у вас запись:\n\n"
            f"📅 {d_fmt}, {b.get('Время','')}\n💅 {svc}\n\nЖдём вас!"
        )
        if b.get("Telegram ID"):
            try: await bot.send_message(int(b["Telegram ID"]), client_msg, parse_mode="Markdown")
            except Exception as e: logger.warning("reminder client: %s", e)

        try:
            await bot.send_message(
                ADMIN_TELEGRAM_ID,
                f"📋 *Напоминание (через {REMINDER_HOURS_BEFORE} ч)*\n\nКлиент: {name}\nУслуга: {svc}\n📅 {d_fmt}, {b.get('Время','')}\n📞 {b.get('Телефон','')}",
                parse_mode="Markdown",
            )
        except Exception as e: logger.warning("reminder admin: %s", e)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    s = AsyncIOScheduler(timezone=TIMEZONE)
    s.add_job(send_reminders, "cron", minute="0,30", kwargs={"bot": bot}, id="reminders", replace_existing=True)
    return s
