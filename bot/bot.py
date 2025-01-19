import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram import BaseMiddleware
from utils.dotenv_config import TOKEN
from api.bot_api import setup_handlers
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        # Log the incoming message
        logger.info(f"Received message: {event.text} from user ID: {event.from_user.id}")

        # Call the next handler
        result = await handler(event, data)

        # Optionally, log the result of the handler
        logger.info(f"Handler executed for message: {event.text}")

        return result


# Set up middleware and handlers
dp.message.middleware(LoggingMiddleware())
setup_handlers(dp)


async def main():
    """Start the bot and log its initialization."""
    logger.info("Bot started!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())