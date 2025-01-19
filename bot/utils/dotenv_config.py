import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TG_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

if not WEATHER_API_KEY:
    raise ValueError("Переменная окружения WEATHER_API_KEY не установлена!")

if not TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")