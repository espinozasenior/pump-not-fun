#!/usr/bin/env python3
import asyncio
from logger.logger import logger                 
from bot.utils.monitor import create_swap_webhook
from config.settings import WEBHOOK_SECRET, WEBHOOK_URL, WALLETS
                                                                                        
async def create_webhook(webhook_url: str, addresses: list[str], auth_header: str = None) -> bool:
    wallets = list(map(lambda item: item["address"], addresses))
    result = await create_swap_webhook(                                                             
        webhook_url=webhook_url,                              
        addresses=wallets,                                                                                 
        auth_header=auth_header                                            
    )
    logger.debug(f"Webhook creation result: {result}")
    return result

if __name__ == "__main__":
    asyncio.run(create_webhook(WEBHOOK_URL, WALLETS, WEBHOOK_SECRET))
