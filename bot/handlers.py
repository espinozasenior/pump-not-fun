from config.settings import PUMP_FUN_CAS, HOMIES_CHAT_ID
from bot.callbacks.callbacks import language_callback
from bot.commands.commands import start_command
from bot.messages.messages import pumpfun_message_handler, user_in_chat_message_handler

from pyrogram import Client, filters

def register_handlers(app: Client):
    # app.on_message(filters.chat(PUMP_FUN_CAS) & filters.incoming)(pumpfun_message_handler)
    # app.on_message(filters.chat(HOMIES_CHAT_ID) & filters.incoming)(user_in_chat_message_handler)
    app.on_message(filters.command("start"))(start_command)
    app.on_callback_query(filters.regex(r"^change_lang$"))(language_callback)