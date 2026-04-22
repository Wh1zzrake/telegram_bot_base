import asyncio, logging
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler
from config import BOT_TOKEN
from handlers.start import start_handler, main_menu_handler, services_list_handler, contacts_handler
from handlers.booking import get_booking_conversation, my_bookings_handler, client_cancel_booking
from handlers.admin import admin_command, admin_today, admin_week, admin_all, admin_cancel_booking
from services.scheduler import setup_scheduler
from api.n8n_webhook import run_api_server, set_bot

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не задан. Скопируйте .env.example → .env")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(get_booking_conversation())

    app.add_handler(CallbackQueryHandler(main_menu_handler,    pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(services_list_handler,pattern="^services_list$"))
    app.add_handler(CallbackQueryHandler(contacts_handler,     pattern="^contacts$"))
    app.add_handler(CallbackQueryHandler(my_bookings_handler,  pattern="^my_bookings$"))
    app.add_handler(CallbackQueryHandler(client_cancel_booking,pattern=r"^cancel_booking:"))
    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer(), pattern="^noop$"))

    app.add_handler(CallbackQueryHandler(admin_today,          pattern="^admin:today$"))
    app.add_handler(CallbackQueryHandler(admin_week,           pattern="^admin:week$"))
    app.add_handler(CallbackQueryHandler(admin_all,            pattern="^admin:all$"))
    app.add_handler(CallbackQueryHandler(admin_cancel_booking, pattern=r"^admin:cancel:"))

    scheduler = setup_scheduler(app.bot)
    scheduler.start()
    set_bot(app.bot)

    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        logger.info("Бот запущен!")
        api_task = asyncio.create_task(run_api_server())
        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            api_task.cancel()
            scheduler.shutdown(wait=False)
            await app.updater.stop()
            await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
