import logging
from aiogram import BaseMiddleware
from aiogram.types import Message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        # Log the incoming message
        logger.info(f"Received message: {event.text} from user ID: {event.from_user.id}")
        
        # Call the next handler
        result = await handler(event, data)
        
        # Optionally, log the result of the handler
        logger.info(f"Handler executed for message: {event.text}")
        
        return result