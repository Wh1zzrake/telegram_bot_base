from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from keyboards.reply import get_start_keyboard


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /start."""
    user = update.effective_user
    first_name = user.first_name if user else "друг"

    text = (
        f"👋 Привет, *{first_name}*!\n\n"
        "Я простой бот с базовыми командами.\n\n"
        "Что умею:\n"
        "• /menu — открыть меню\n"
        "• /info — информация о боте\n"
    )

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_start_keyboard(),
    )