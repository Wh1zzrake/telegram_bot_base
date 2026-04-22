import os

# Вставь токен сюда или задай переменную окружения: set BOT_TOKEN=ваш_токен
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")

# Информация о боте (используется в /info)
BOT_NAME = "MyBot"
BOT_VERSION = "1.0.0"
BOT_DESCRIPTION = "Демонстрационный бот с базовыми командами."