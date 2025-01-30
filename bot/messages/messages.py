from logger.logger import logger
from config.settings import SOL_MINT, SOL_AMOUNT, AUTO_MULTIPLIER, SLIPPAGE_BPS, ALLOWED_USERS
import re
# from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from pyrogram import Client
from bot.utils.jupiter_swap import swap
from bot.utils.token import get_token_info, save_token_info

async def user_in_chat_message_handler(_:Client, message:Message):
    # Expresión regular para capturar el token
    pump_fun_pattern = r"\b([A-Za-z0-9]+pump)\b"
     # Check if message is from allowed chat
    if not message.from_user or message.from_user.id not in ALLOWED_USERS:
        return

    if message.caption is not None:
        logger.info(f"New msg from: {message.chat.title}")
        logger.info(f"Member: {message.from_user.full_name}")
        # Buscar el token pumpfun en publicaciones con caption (photos)
        match = re.search(pump_fun_pattern, message.caption)
        if match:
            try:
                token = str(match.group(1)).strip()
                logger.info(f"Token found: {token}")
                await swap(SOL_MINT, token, SOL_AMOUNT, AUTO_MULTIPLIER, SLIPPAGE_BPS)
            except (AttributeError, IndexError) as e:
                logger.error(f"Error extracting token: {e}")
                return
        else:
            logger.info("Not a pump token in caption")
    if message.text is not None:
        logger.info(f"New msg from: {message.chat.title}")
        logger.info(f"Member: {message.from_user.full_name}")
        # Buscar el token pumpfun en publicaciones de texto
        match = re.search(pump_fun_pattern, message.text)
        if match:
            try:
                token = str(match.group(1)).strip()
                logger.info(f"Token found: {token}")
                await swap(SOL_MINT, token, SOL_AMOUNT, AUTO_MULTIPLIER, SLIPPAGE_BPS)
            except (AttributeError, IndexError) as e:
                logger.error(f"Error extracting token: {e}")
                return
        else:
            logger.info("Not a pump token in member post")

async def pumpfun_message_handler(_:Client, message:Message):
    # Expresión regular para capturar el token
    pump_fun_pattern = r"\b([A-Za-z0-9]+pump)\b"

    if message.caption is not None:
        logger.info(f"New msg from: {message.sender_chat.title}")
        # Buscar el token pumpfun en publicaciones con caption (photos)
        match = re.search(pump_fun_pattern, message.caption)
        if match:
            try:
                token = str(match.group(1)).strip()
                logger.info(f"Token found: {token}")
                token_info = await get_token_info(token)
                if token_info is not None:
                    await save_token_info(token_info)
                # await swap(SOL_MINT, token, SOL_AMOUNT, AUTO_MULTIPLIER, SLIPPAGE_BPS)
            except (AttributeError, IndexError) as e:
                logger.error(f"Error extracting token: {e}")
                return
        else:
            logger.info("Not a pump token")

        # TODO: Find socials and name through caption's entities array
        # logger.info(f"Message entities: {message.caption}")
        # for entity in message.caption_entities:
        #     if entity.type == MessageEntityType.CODE:
        #         phone_text = message.caption[entity.offset:entity.offset + entity.length]
        #         logger.info(f"Número de teléfono detectado: {phone_text}")
        #         logger.info(f"Número de teléfono detectado: {entity}")