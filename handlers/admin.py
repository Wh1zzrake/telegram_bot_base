import logging
from datetime import date, timedelta, datetime
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from config import ADMIN_TELEGRAM_ID
from keyboards.inline import admin_menu_keyboard, main_menu_keyboard
from services import google_sheets

logger = logging.getLogger(__name__)
MONTHS = ["января","февраля","марта","апреля","мая","июня",
          "июля","августа","сентября","октября","ноября","декабря"]


def _is_admin(uid): return uid == ADMIN_TELEGRAM_ID


def _fmt_date(s):
    try:
        d = datetime.strptime(s, "%Y-%m-%d")
        return f"{d.day} {MONTHS[d.month-1]} {d.year}"
    except ValueError:
        return s


def _line(b):
    return (
        f"🕐 {b.get('Время','?')} — *{b.get('Услуга','?')}*\n"
        f"   👤 {b.get('Имя клиента','?')} | 📞 {b.get('Телефон','?')}\n"
        f"   💳 {b.get('Оплата','?')} | 💰 {b.get('Цена (₽)','?')} ₽  ID: `{b.get('ID','?')}`"
    )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("Нет доступа.")
        return
    await update.message.reply_text("🔐 *Панель администратора*", parse_mode=ParseMode.MARKDOWN, reply_markup=admin_menu_keyboard())


async def admin_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not _is_admin(update.effective_user.id): return
    today    = date.today().isoformat()
    bookings = sorted(google_sheets.get_bookings_for_date(today), key=lambda b: b.get("Время",""))
    text = (
        f"📅 *Сегодня ({_fmt_date(today)})* — {len(bookings)} запись(-ей):\n\n" + "\n\n".join(_line(b) for b in bookings)
        if bookings else f"📅 *Сегодня ({_fmt_date(today)})* — записей нет."
    )
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=admin_menu_keyboard())


async def admin_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not _is_admin(update.effective_user.id): return
    today    = date.today()
    bookings = sorted(
        google_sheets.get_bookings_for_period(today.isoformat(), (today + timedelta(days=7)).isoformat()),
        key=lambda b: (b.get("Дата",""), b.get("Время",""))
    )
    if not bookings:
        text = "📆 На следующие 7 дней записей нет."
    else:
        lines, cur = ["📆 *Записи на 7 дней:*\n"], ""
        for b in bookings:
            if b.get("Дата") != cur:
                cur = b.get("Дата","")
                lines.append(f"\n📅 *{_fmt_date(cur)}*")
            lines.append(_line(b))
        text = "\n".join(lines)
    await query.edit_message_text(text[:4000], parse_mode=ParseMode.MARKDOWN, reply_markup=admin_menu_keyboard())


async def admin_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not _is_admin(update.effective_user.id): return
    today    = date.today()
    bookings = sorted(
        google_sheets.get_bookings_for_period(today.isoformat(), today.replace(year=today.year+1).isoformat()),
        key=lambda b: (b.get("Дата",""), b.get("Время",""))
    )
    if not bookings:
        text = "📊 Активных записей нет."
    else:
        lines, cur = [f"📊 *Все записи* ({len(bookings)} шт.):\n"], ""
        for b in bookings:
            if b.get("Дата") != cur:
                cur = b.get("Дата","")
                lines.append(f"\n📅 *{_fmt_date(cur)}*")
            lines.append(_line(b))
        text = "\n".join(lines)
    await query.edit_message_text(text[:4000], parse_mode=ParseMode.MARKDOWN, reply_markup=admin_menu_keyboard())


async def admin_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not _is_admin(update.effective_user.id): return
    booking_id = query.data.split(":", 2)[2]
    ok = google_sheets.cancel_booking(booking_id)
    text = f"✅ Запись `{booking_id}` отменена." if ok else f"❌ Не удалось отменить `{booking_id}`."
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=admin_menu_keyboard())
