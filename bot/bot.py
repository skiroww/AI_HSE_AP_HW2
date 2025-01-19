from utils.dotenv_config import TOKEN
from aiogram import Bot, Dispatcher
from utils.link import LoggingMiddleware
from api.bot_api import setup_handlers


import asyncio

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Настраиваем middleware и обработчики
dp.message.middleware(LoggingMiddleware())
setup_handlers(dp)


async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())