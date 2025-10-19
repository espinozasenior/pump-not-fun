from logger.logger import logger
from config.settings import SOL_MINT, SOL_AMOUNT, AUTO_MULTIPLIER, SLIPPAGE_BPS, ALLOWED_USERS, HOMIES_CHAT_ID
import re
# from pyrogram.enums import MessageEntityType
from pyrogram.types import Message, MessageEntity
from pyrogram import Client
from bot.utils.jupiter_swap import swap
from bot.utils.token import get_token_info, save_token_info
from bot.keyboards.keyboards import get_buy_button

async def forward_message(client: Client, message: Message, token_info: dict, chat_id: int, wallet_info: dict = None):
        try:
            # Safely get contract address
            ca = token_info.get('profile', {}).get('ca', 'N/A') if token_info else 'N/A'
            
            msg = await client.send_message(
                chat_id=chat_id,
                text=format_forward_message(token_info, wallet_info),
                reply_markup=get_buy_button(ca),
                disable_web_page_preview=False
            )
            logger.debug(f"Forwarded message: {msg.id} / link {msg.link}")
        except Exception as e:
            logger.error(f"Forward error: {e}")


def format_wallet_token_pnl(wallet: dict) -> str:
    if wallet.get('pnl') is None:
        return "No data available"
    return f"""
    **Wallet Token PNL:**

  Trades: {wallet.get('pnl').get('data', '').get('total_trade', 0)}
  **TXs (30d)**
  🟢{wallet.get('pnl').get('data' '').get('buy_30d', 0)} | 🔴{wallet.get('pnl').get('data', '').get('sell_30d', 0)}

  **Total Profit:**
  {
    f"🔴 -${abs(safe_float(wallet.get('pnl').get('data', '').get('realized_profit', 0))):.2f}" 
    if safe_float(wallet.get('pnl').get('data').get('realized_profit', 0)) < 0 
    else f"🟢 +${safe_float(wallet.get('pnl').get('data').get('realized_profit', 0)):.2f}"
  }({
    f"{safe_float(wallet.get('pnl').get('data').get('total_pnl', 0)) * 100:.2f}%" 
    if safe_float(wallet.get('pnl').get('data').get('total_pnl', 0)) < 0
    else f"+{safe_float(wallet.get('pnl').get('data').get('total_pnl', 0)) * 100:.2f}%"
  })

  **Unrealized:**
  {
    f"🔴 -${abs(safe_float(wallet.get('pnl').get('data').get('unrealized_profit', 0))):.2f}" 
    if safe_float(wallet.get('pnl').get('data').get('unrealized_profit', 0)) < 0 
    else f"🟢 +${safe_float(wallet.get('pnl').get('data').get('unrealized_profit', 0)):.2f}"
  }({
    f"{safe_float(wallet.get('pnl').get('data').get('unrealized_pnl', 0)) * 100:.2f}%" 
    if safe_float(wallet.get('pnl').get('data').get('unrealized_pnl', 0)) < 0
    else f"+{safe_float(wallet.get('pnl').get('data').get('unrealized_pnl', 0)) * 100:.2f}%"
  })

  **Balance:**
  ${wallet.get('pnl').get('data').get('holding_cost', 0)}

  **Bought/Sold**
  ${safe_float(wallet.get('pnl').get('data').get('history_bought_cost', 0.0)):.2f} | ${safe_float(wallet.get('pnl').get('data').get('history_sold_income', 0.0)):.2f}

  **Avg Cost/Sold**
  ${safe_float(wallet.get('pnl').get('data').get('history_avg_cost', 0.0)):.4f} | ${safe_float(wallet.get('pnl').get('data').get('avg_sold', 0.0)):.4f}
"""

def format_forward_message(token_info: dict, wallet: dict = None) -> str:
    # Helper function to safely convert values to float
    def safe_float(value, default=0.0):
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
            
    return f"""**#{wallet['name'] if wallet['name'] else "N/A"}** { wallet['description'] if wallet['description'] else "" }

📌**CA:** `{token_info.get('profile').get('ca', 'N/A')}`
Name: **{token_info.get('profile').get('name', 'N/A')}**
Symbol: **{token_info.get('profile').get('symbol', 'N/A')}**
🏷️ Price: {token_info.get('profile').get('price', 0)}
💸 MC: 
💰 LP: ${token_info.get('profile').get('liquidity', 0)}
👥 **Holders:** {token_info.get('stats').get('holders', 0)}
📊 **TOP 100 Metrics:**
    - 📈 Profit Avg: {token_info.get('holders').get('avg_profit_percent', 0):.2f}%
    - 🔝 Top 10 holders: {token_info.get('profile').get('top_10_holder_rate', 0):.2f}%
    - 📉 BC Owners: {token_info.get('stats').get('bc_owners_percent', 0):.2f}%
    - 💰 Profitable wallets: {token_info.get('holders').get('profitable_wallets', 0)}
    - 🌱 Fresh wallets: {token_info.get('holders').get('fresh_wallets', 0)}
    - 💸 Sold wallets: {token_info.get('holders').get('sold_wallets', 0)}
    - 🕵️ Insiders: {token_info.get('holders').get('insiders_wallets', 0)} ({token_info.get('stats').get('insiders_percent', 0):.2f}%)
    - 🎣 Phishing wallets: {token_info.get('holders').get('phishing_wallets', 0)}
    - 🚩 Suspicious wallets: {token_info.get('holders').get('suspicious_wallets', 0)}
    - 🎅🏾 With common source: {token_info.get('holders').get('same_address_funded', 0)}        

🔗 **Socials:**
    - Twitter: https://x.com/{token_info.get('links').get('twitter', 'N/A')}
    - Telegram: {token_info.get('links').get('telegram', 'N/A')}
    - Github: {token_info.get('links').get('github', 'N/A')}
    - Website: {token_info.get('links').get('website', 'N/A')}

{ format_wallet_token_pnl(token_info.get('pnl'))}
"""

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
                    await forward_message(_, message, token_info, HOMIES_CHAT_ID)
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
