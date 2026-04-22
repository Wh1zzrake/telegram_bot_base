from datetime import date, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import BOOKING_DAYS_AHEAD
from data.services import SERVICES, PAYMENT_METHODS


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записаться",    callback_data="book:start")],
        [InlineKeyboardButton("📋 Мои записи",    callback_data="my_bookings")],
        [InlineKeyboardButton("ℹ️ Услуги и цены", callback_data="services_list")],
        [InlineKeyboardButton("📞 Контакты",      callback_data="contacts")],
    ])


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
    ])


def services_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for s in SERVICES:
        label = f"{s.emoji} {s.name} — {s.price} ₽ ({s.duration_minutes} мин)"
        rows.append([InlineKeyboardButton(label, callback_data=f"book:service:{s.id}")])
    rows.append([InlineKeyboardButton("◀️ Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)


def dates_keyboard() -> InlineKeyboardMarkup:
    today = date.today()
    rows, row = [], []
    for i in range(BOOKING_DAYS_AHEAD):
        d = today + timedelta(days=i)
        if d.weekday() == 6:  # пропускаем воскресенье
            continue
        WEEKDAYS = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]
        label = f"{d.day:02d}.{d.month:02d} {WEEKDAYS[d.weekday()]}"
        row.append(InlineKeyboardButton(label, callback_data=f"book:date:{d.isoformat()}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("◀️ Назад", callback_data="book:start")])
    return InlineKeyboardMarkup(rows)


def times_keyboard(available_slots: list[str], chosen_date_iso: str) -> InlineKeyboardMarkup:
    rows, row = [], []
    for slot in available_slots:
        row.append(InlineKeyboardButton(slot, callback_data=f"book:time:{slot}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    if not available_slots:
        rows.append([InlineKeyboardButton("Нет свободных слотов", callback_data="noop")])
    rows.append([InlineKeyboardButton("◀️ Назад", callback_data="book:service:back")])
    return InlineKeyboardMarkup(rows)


def payment_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(label, callback_data=f"book:pay:{key}")] for key, label in PAYMENT_METHODS]
    rows.append([InlineKeyboardButton("◀️ Назад", callback_data="book:time:back")])
    return InlineKeyboardMarkup(rows)


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Подтвердить", callback_data="book:confirm"),
        InlineKeyboardButton("❌ Отмена",      callback_data="book:cancel"),
    ]])


def cancel_booking_keyboard(booking_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отменить запись", callback_data=f"cancel_booking:{booking_id}")],
        [InlineKeyboardButton("🏠 Главное меню",    callback_data="main_menu")],
    ])


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Записи сегодня",  callback_data="admin:today")],
        [InlineKeyboardButton("📆 Записи на неделю", callback_data="admin:week")],
        [InlineKeyboardButton("📊 Все записи",       callback_data="admin:all")],
    ])


def admin_booking_actions_keyboard(booking_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отменить запись", callback_data=f"admin:cancel:{booking_id}")],
        [InlineKeyboardButton("◀️ Назад",           callback_data="admin:today")],
    ])
