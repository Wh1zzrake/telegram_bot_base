import logging
from telegram.ext import ApplicationBuilder, CommandHandler

from config import BOT_TOKEN
from handlers.start import start_handler
from handlers.menu import menu_handler
from handlers.info import info_handler

# Логирование
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Точка входа: регистрируем хендлеры и запускаем бота."""
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрация команд
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("menu", menu_handler))
    app.add_handler(CommandHandler("info", info_handler))

    logger.info("Бот запущен. Ожидаем сообщения...")
    app.run_polling()


if __name__ == "__main__":
    main()