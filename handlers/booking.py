import logging
import re
from datetime import date, datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters,
)

from config import ADMIN_TELEGRAM_ID, WORK_SESSIONS, SLOT_STEP_MINUTES
from data.services import SERVICES_BY_ID, PAYMENT_LABELS
from keyboards.inline import (
    back_to_menu_keyboard, confirm_keyboard, dates_keyboard,
    main_menu_keyboard, payment_keyboard, services_keyboard,
    times_keyboard, cancel_booking_keyboard,
)
from services import google_sheets, google_calendar

logger = logging.getLogger(__name__)

(SELECT_SERVICE, SELECT_DATE, SELECT_TIME, ENTER_NAME, ENTER_PHONE, SELECT_PAYMENT, CONFIRM) = range(7)


def _t2m(t: str) -> int:
    h, m = map(int, t.split(":"))
    return h * 60 + m


def _m2t(m: int) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


def _get_available_slots(duration: int, existing: list[dict]) -> list[str]:
    booked = [
        (_t2m(str(b["Время"])), _t2m(str(b["Время"])) + int(b["Длительность (мин)"]))
        for b in existing
    ]
    available = []
    for sess_start_str, sess_end_str in WORK_SESSIONS:
        sess_start = _t2m(sess_start_str)
        sess_end   = _t2m(sess_end_str)
        t = sess_start
        while t < sess_end:
            slot_end = t + duration
            if slot_end <= sess_end:
                if not any(t < b_end and slot_end > b_start for b_start, b_end in booked):
                    available.append(_m2t(t))
            t += SLOT_STEP_MINUTES
    return available


def _format_date(date_str: str) -> str:
    MONTHS = ["января","февраля","марта","апреля","мая","июня",
              "июля","августа","сентября","октября","ноября","декабря"]
    DAYS   = ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"]
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return f"{DAYS[d.weekday()]}, {d.day} {MONTHS[d.month - 1]}"
    except ValueError:
        return date_str


def _build_summary(ctx_data: dict) -> str:
    service = SERVICES_BY_ID.get(ctx_data.get("service_id", ""))
    pay     = PAYMENT_LABELS.get(ctx_data.get("payment", ""), ctx_data.get("payment", ""))
    return (
        f"📋 *Детали записи*\n\n"
        f"💅 Услуга: {service.name if service else '—'}\n"
        f"📅 Дата: {_format_date(ctx_data.get('date', ''))}\n"
        f"⏰ Время: {ctx_data.get('time', '—')}\n"
        f"👤 Имя: {ctx_data.get('name', '—')}\n"
        f"📞 Телефон: {ctx_data.get('phone', '—')}\n"
        f"💰 Оплата: {pay}\n"
        f"💵 Стоимость: {service.price if service else '—'} ₽"
    )


async def booking_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("💅 *Выберите услугу:*", parse_mode=ParseMode.MARKDOWN, reply_markup=services_keyboard())
    return SELECT_SERVICE


async def select_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    service_id = query.data.split(":", 2)[2]
    service = SERVICES_BY_ID.get(service_id)
    if not service:
        await query.answer("Услуга не найдена", show_alert=True)
        return SELECT_SERVICE
    context.user_data["service_id"] = service_id
    await query.edit_message_text(
        f"✅ Услуга: *{service.name}*\n\n📅 Выберите дату:",
        parse_mode=ParseMode.MARKDOWN, reply_markup=dates_keyboard(),
    )
    return SELECT_DATE


async def back_to_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💅 *Выберите услугу:*", parse_mode=ParseMode.MARKDOWN, reply_markup=services_keyboard())
    return SELECT_SERVICE


async def select_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chosen_date = query.data.split(":", 2)[2]
    if chosen_date < date.today().isoformat():
        await query.answer("Нельзя записаться в прошлом", show_alert=True)
        return SELECT_DATE
    context.user_data["date"] = chosen_date
    service = SERVICES_BY_ID.get(context.user_data.get("service_id", ""))
    if not service:
        return SELECT_SERVICE
    existing  = google_sheets.get_bookings_for_date(chosen_date)
    available = _get_available_slots(service.duration_minutes, existing)
    context.user_data["available_slots"] = available
    text = f"📅 *{_format_date(chosen_date)}*\n\n💅 {service.name}\n\n⏰ Выберите время:"
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=times_keyboard(available, chosen_date))
    return SELECT_TIME


async def back_to_dates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    service = SERVICES_BY_ID.get(context.user_data.get("service_id", ""))
    prefix  = f"✅ Услуга: *{service.name}*\n\n" if service else ""
    await query.edit_message_text(f"{prefix}📅 Выберите дату:", parse_mode=ParseMode.MARKDOWN, reply_markup=dates_keyboard())
    return SELECT_DATE


async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chosen_time = query.data.split(":", 2)[2]
    if chosen_time not in context.user_data.get("available_slots", []):
        await query.answer("Это время уже занято.", show_alert=True)
        return SELECT_TIME
    context.user_data["time"] = chosen_time
    await query.edit_message_text("👤 Введите ваше *имя*:", parse_mode=ParseMode.MARKDOWN)
    return ENTER_NAME


async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if not 2 <= len(name) <= 50:
        await update.message.reply_text("Пожалуйста, введите корректное имя (2–50 символов).")
        return ENTER_NAME
    context.user_data["name"] = name
    await update.message.reply_text(
        f"✅ Имя: *{name}*\n\n📞 Введите ваш *номер телефона*:",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ENTER_PHONE


_PHONE_RE = re.compile(r"^[\+\d][\d\s\-\(\)]{6,18}$")


async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone = update.message.text.strip()
    if not _PHONE_RE.match(phone):
        await update.message.reply_text("Введите корректный номер (например: +7 900 123-45-67).")
        return ENTER_PHONE
    context.user_data["phone"] = phone
    await update.message.reply_text("💳 Выберите *способ оплаты*:", parse_mode=ParseMode.MARKDOWN, reply_markup=payment_keyboard())
    return SELECT_PAYMENT


async def select_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["payment"] = query.data.split(":", 2)[2]
    await query.edit_message_text(
        f"{_build_summary(context.user_data)}\n\n❓ Всё верно?",
        parse_mode=ParseMode.MARKDOWN, reply_markup=confirm_keyboard(),
    )
    return CONFIRM


async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⏳ Создаю запись...")
    data    = context.user_data
    service = SERVICES_BY_ID.get(data.get("service_id", ""))
    pay_lbl = PAYMENT_LABELS.get(data.get("payment", ""), data.get("payment", ""))
    if not service:
        await query.edit_message_text("Ошибка. Попробуйте снова /start")
        return ConversationHandler.END

    # Финальная проверка свободности слота
    existing  = google_sheets.get_bookings_for_date(data["date"])
    available = _get_available_slots(service.duration_minutes, existing)
    if data["time"] not in available:
        await query.edit_message_text("😔 Это время только что заняли. Запишитесь снова /start", reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    booking_id = google_sheets.add_booking(
        booking_date=data["date"], booking_time=data["time"],
        client_name=data["name"], client_phone=data["phone"],
        service_name=service.name, duration_minutes=service.duration_minutes,
        price=service.price, payment=pay_lbl, telegram_id=update.effective_user.id,
    )
    event_id = google_calendar.create_event(
        booking_date=data["date"], booking_time=data["time"],
        duration_minutes=service.duration_minutes, client_name=data["name"],
        client_phone=data["phone"], service_name=service.name,
        payment=pay_lbl, booking_id=booking_id,
    )
    if event_id:
        google_sheets.update_event_id(booking_id, event_id)

    await query.edit_message_text(
        f"✅ *Запись оформлена!*\n\n"
        f"📋 ID: `{booking_id}`\n"
        f"💅 {service.name}\n"
        f"📅 {_format_date(data['date'])}, {data['time']}\n"
        f"👤 {data['name']}\n"
        f"💳 {pay_lbl}\n\n"
        f"Если нужно отменить — нажмите кнопку ниже.",
        parse_mode=ParseMode.MARKDOWN, reply_markup=cancel_booking_keyboard(booking_id),
    )
    try:
        await context.bot.send_message(
            chat_id=ADMIN_TELEGRAM_ID,
            text=(
                f"🆕 *Новая запись!*\n\n"
                f"📋 ID: `{booking_id}`\n💅 {service.name}\n"
                f"📅 {_format_date(data['date'])}, {data['time']}\n"
                f"👤 {data['name']}\n📞 {data['phone']}\n"
                f"💳 {pay_lbl} | 💰 {service.price} ₽"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception:
        pass
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_booking_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("❌ Запись отменена.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END


async def client_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    booking_id = query.data.split(":", 1)[1]
    if google_sheets.cancel_booking(booking_id):
        await query.edit_message_text(
            f"✅ Запись `{booking_id}` отменена.", parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard()
        )
        try:
            await context.bot.send_message(ADMIN_TELEGRAM_ID, f"❌ Клиент отменил запись ID: `{booking_id}`", parse_mode=ParseMode.MARKDOWN)
        except Exception:
            pass
    else:
        await query.edit_message_text("Запись не найдена или уже отменена.", reply_markup=main_menu_keyboard())


async def my_bookings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    bookings = google_sheets.get_bookings_for_client(update.effective_user.id)
    if not bookings:
        await query.edit_message_text("📋 У вас нет предстоящих записей.", reply_markup=main_menu_keyboard())
        return
    lines = ["📋 *Ваши предстоящие записи:*\n"]
    for b in bookings:
        lines.append(f"• {_format_date(str(b['Дата']))}, {b['Время']}\n  {b['Услуга']}\n  ID: `{b['ID']}`")
    await query.edit_message_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN, reply_markup=back_to_menu_keyboard())


def get_booking_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(booking_start, pattern="^book:start$")],
        states={
            SELECT_SERVICE: [
                CallbackQueryHandler(select_service,  pattern=r"^book:service:(?!back$).+$"),
                CallbackQueryHandler(booking_start,   pattern="^main_menu$"),
            ],
            SELECT_DATE: [
                CallbackQueryHandler(select_date,     pattern=r"^book:date:"),
                CallbackQueryHandler(back_to_services,pattern=r"^book:service:back$"),
            ],
            SELECT_TIME: [
                CallbackQueryHandler(select_time,     pattern=r"^book:time:(?!back$).+$"),
                CallbackQueryHandler(back_to_dates,   pattern=r"^book:service:back$"),
            ],
            ENTER_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
            ENTER_PHONE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone)],
            SELECT_PAYMENT:[
                CallbackQueryHandler(select_payment,  pattern=r"^book:pay:"),
                CallbackQueryHandler(back_to_dates,   pattern=r"^book:time:back$"),
            ],
            CONFIRM: [
                CallbackQueryHandler(confirm_booking,     pattern="^book:confirm$"),
                CallbackQueryHandler(cancel_booking_flow, pattern="^book:cancel$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_booking_flow, pattern="^book:cancel$"),
            CallbackQueryHandler(booking_start,       pattern="^main_menu$"),
        ],
        per_message=False,
    )
