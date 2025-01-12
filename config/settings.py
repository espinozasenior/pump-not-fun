from dotenv import load_dotenv
import os

load_dotenv()

# Bot configuration
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING")

# Database configuration
DATABASE_URL = "sqlite:///database/bot.db"

PUMP_FUN_CAS = [-1002439158541]