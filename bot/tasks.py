from bot.commands.commands import get_bot_commands
from logger.logger import logger
from datetime import datetime, timedelta, UTC
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client

def register_tasks(app: Client, tasks_app: AsyncIOScheduler):
    async def on_startup():
        if app.bot_token:
            await app.set_bot_commands(await get_bot_commands())
        identity = "Bot" if app.bot_token else "User"
        me = await app.get_me()
        logger.info(f"{identity} account @{me.username} is running!")

    # Only run startup tasks if actually starting up
    tasks_app.add_job(
        on_startup,
        'date',
        run_date=datetime.now() + timedelta(seconds=3)  # Allow warmup time
    )