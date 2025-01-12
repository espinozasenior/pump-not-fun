from config.settings import API_ID, API_HASH, SESSION_STRING
from bot.handlers import register_handlers
from bot.tasks import register_tasks

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client

app = Client(
    "pump-not-fun",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

tasks_app = AsyncIOScheduler()

if __name__ == "__main__":
    register_tasks(app, tasks_app)
    register_handlers(app)
    # tasks_app.start() - Commented out because prompting an no running event loop [asyncio.get_running_loop()] error
    app.run()