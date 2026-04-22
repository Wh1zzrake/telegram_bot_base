from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from config import MASTER_NAME, SALON_NAME
from keyboards.inline import main_menu_keyboard, back_to_menu_keyboard

WELCOME_TEXT = (
    "👋 Добро пожаловать в *{salon}*!\n\n"
    "Меня зовут *{master}* — ваш мастер маникюра.\n\n"
    "Я помогу вам:\n"
    "• 📅 Записаться на удобное время\n"
    "• 💅 Выбрать услугу и узнать цену\n"
    "• 📋 Посмотреть ваши предстоящие записи\n\n"
    "Выберите действие ниже 👇"
)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = WELCOME_TEXT.format(salon=SALON_NAME, master=MASTER_NAME)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    text = WELCOME_TEXT.format(salon=SALON_NAME, master=MASTER_NAME)
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())


async def services_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from data.services import SERVICES
    query = update.callback_query
    await query.answer()
    lines = ["💅 *Услуги и цены*\n"]
    for s in SERVICES:
        lines.append(f"{s.emoji} *{s.name}*\n   ⏱ {s.duration_minutes} мин  |  💰 {s.price} ₽")
    await query.edit_message_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN, reply_markup=back_to_menu_keyboard())


async def contacts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    text = (
        f"📞 *Контакты*\n\n"
        f"Мастер: {MASTER_NAME}\n"
        f"Студия: {SALON_NAME}\n\n"
        f"По всем вопросам пишите прямо в этот бот!"
    )
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_to_menu_keyboard())
