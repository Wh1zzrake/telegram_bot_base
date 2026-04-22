from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from keyboards.reply import get_menu_keyboard


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /menu."""
    text = (
        "📂 *Главное меню*\n\n"
        "Выбери нужный раздел:"
    )

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_menu_keyboard(),
    )