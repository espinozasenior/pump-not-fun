from bot.languages.language_manager import lang_manager
from bot.keyboards.keyboards import get_start_keyboard
from bot.utils.decorators import get_user
from logger.logger import logger
from bot.utils.pnl import calculate_wallet_pnl
from database.database import SmartWallet
from sqlalchemy import select

from pyrogram.types import BotCommand, Message

async def get_bot_commands():
    return [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="pnl", description="Check wallet PNL"),
    ]

@get_user()
async def start_command(client, message: Message, user, session):
    try:
        await message.reply_text(
            lang_manager.get_text(user.language, "welcome_message", user.first_name),
            reply_markup=get_start_keyboard(user.language)
        )
    except Exception as e:
        logger.error(f"Error in start_command: {e}")

@get_user()
async def pnl_command(client, message: Message, user, session):
    try:
        # Check if wallet address was provided
        command_parts = message.text.split()
        
        if len(command_parts) > 1:
            # Use provided wallet address
            wallet_address = command_parts[1]
        else:
            # Get all wallets and let user choose
            wallets = (await session.execute(select(SmartWallet))).scalars().all()
            if not wallets:
                await message.reply_text("No wallets found in the database.")
                return
                
            # For simplicity, use the first wallet
            wallet_address = wallets[0].address
        
        # Send initial message
        status_message = await message.reply_text("Calculating PNL, please wait...")
        
        # Calculate PNL for the wallet
        days = 7  # Default to 7 days
        pnl_data = await calculate_wallet_pnl(wallet_address, days)
        
        if "error" in pnl_data:
            await status_message.edit_text(
                lang_manager.get_text(user.language, "pnl_error", pnl_data["error"])
            )
            return
        
        # Format the response
        response = [
            lang_manager.get_text(user.language, "pnl_response_title"),
            lang_manager.get_text(user.language, "pnl_wallet_info", 
                                 pnl_data["wallet_name"], pnl_data["wallet_address"]),
            lang_manager.get_text(user.language, "pnl_period", pnl_data["period_days"]),
            lang_manager.get_text(user.language, "pnl_total", round(pnl_data["total_realized_pnl"], 4)),
            lang_manager.get_text(user.language, "pnl_transactions", pnl_data["total_transactions"]),
            ""
        ]
        
        # Add token details if available
        if pnl_data["token_pnls"]:
            response.append(lang_manager.get_text(user.language, "pnl_token_details"))
            
            for token_pnl in pnl_data["token_pnls"]:
                # Try to get token symbol from database
                token_query = select(Token).where(Token.ca == token_pnl["token_mint"])
                token_result = await session.execute(token_query)
                token = token_result.scalar_one_or_none()
                
                token_symbol = token.symbol if token else token_pnl["token_mint"][:8] + "..."
                
                response.append(
                    lang_manager.get_text(user.language, "pnl_token_entry",
                                        token_symbol,
                                        round(token_pnl["realized_pnl"], 4),
                                        round(token_pnl["buy_volume"], 2),
                                        round(token_pnl["sell_volume"], 2))
                )
        else:
            response.append(lang_manager.get_text(user.language, "pnl_no_data"))
        
        # Update the status message with the PNL report
        await status_message.edit_text("\n".join(response))
        
    except Exception as e:
        logger.error(f"Error in pnl_command: {e}")
        await message.reply_text(
            lang_manager.get_text(user.language, "pnl_error", str(e))
        )