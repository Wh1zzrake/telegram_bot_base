from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_menu_keyboard() -> InlineKeyboardMarkup:
    """Inline-клавиатура для /menu."""
    keyboard = [
        [
            InlineKeyboardButton("📋 О боте", callback_data="info"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        ],
        [
            InlineKeyboardButton("🆘 Помощь", callback_data="help"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Inline-клавиатура для /start."""
    keyboard = [
        [InlineKeyboardButton("📂 Меню", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)