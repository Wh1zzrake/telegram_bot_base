from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import BOT_NAME, BOT_VERSION, BOT_DESCRIPTION


async def info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /info."""
    text = (
        f"ℹ️ *{BOT_NAME}*\n\n"
        f"📌 Версия: `{BOT_VERSION}`\n"
        f"📝 Описание: {BOT_DESCRIPTION}\n\n"
        "🛠 Разработан на Python + python-telegram-bot"
    )

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)