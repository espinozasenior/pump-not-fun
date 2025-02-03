from logger.logger import logger
from config.settings import HELIUS_API_KEY, HOMIES_CHAT_ID, WEBHOOK_SECRET, WALLETS
from database.database import SmartWallet, Token, WalletHoldingHistory, AsyncSessionFactory
from sqlalchemy import select, delete
from datetime import datetime, timedelta, UTC
from pyrogram import Client
import aiohttp
from bot.utils.wallet import check_multiple_wallets

async def create_swap_webhook(webhook_url: str, addresses: list[str], auth_header: str = None) -> bool:
    """
    Create a Helius webhook monitoring successful swaps for specified addresses.
    
    Args:
        webhook_url: URL to receive swap notifications
        addresses: List of wallet addresses to monitor
        auth_header: Optional authentication header for webhook security
    
    Returns:
        True if webhook created successfully, False otherwise
    """
    api_url = f"https://api.helius.xyz/v0/webhooks?api-key={HELIUS_API_KEY}"
    
    payload = {
        "webhookURL": webhook_url,
        "accountAddresses": addresses,
        "webhookType": "enhanced",
        "transactionTypes": ["SWAP"],
        "txnStatus": "success",
        "authHeader": auth_header
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Created swap webhook: {data.get('webhookId')}")
                    return True
                
                error = await response.text()
                logger.error(f"Webhook creation failed ({response.status}): {error}")
                return False
                
    except Exception as e:
        logger.error(f"Webhook creation exception: {str(e)}")
        return False

async def get_webhooks() -> list[dict]:                                                
     """Retrieve all existing webhooks filtered for swap monitoring"""                  
     api_url = f"https://api.helius.xyz/v0/webhooks?api-key={HELIUS_API_KEY}"           
                                                                                        
     try:                                                                               
         async with aiohttp.ClientSession() as session:
             async with session.get(api_url) as response:                               
                 if response.status == 200:                                             
                     all_webhooks = await response.json()                               
                     return [                                                           
                         {
                             "id": wh["webhookId"],
                             "url": wh["webhookURL"],
                             "addresses": wh.get("accountAddresses", []),
                             "type": wh["webhookType"]
                         }
                         for wh in all_webhooks                                         
                         if "SWAP" in wh.get("transactionTypes", [])                    
                     ]                                                                  
                 return []                                                              
     except Exception as e:                                                             
         logger.error(f"Webhook retrieval failed: {str(e)}")                            
         return []                                                                      
                                                                                        
async def edit_webhook(webhook_id: str, new_addresses: list[str] = None, new_url: str = None) -> bool:
    """Update existing webhook with new addresses or URL"""                            
    api_url = f"https://api.helius.xyz/v0/webhooks/{webhook_id}?api-key={HELIUS_API_KEY}"
    wallets = list(map(lambda item: item["address"], WALLETS))
                                                                                        
    update_data = {
        "webhookType": "enhanced",
        "accountAddresses": wallets,
        "transactionTypes": ["SWAP"],
        "txnStatus": "success",
        "authHeader": WEBHOOK_SECRET
    }

    if new_addresses:                                                                  
        update_data["accountAddresses"] = new_addresses                                
    if new_url:                                                                        
        update_data["webhookURL"] = new_url                                            
                                                                                    
    try:                                                                               
        async with aiohttp.ClientSession() as session:
            async with session.put(
                api_url,
                headers=
                {
                    "Content-Type": "application/json"
                },
                json=update_data
            ) as response:             
                if response.status == 200:                                             
                    logger.info(f"Updated webhook {webhook_id}")                       
                    return True                                                        
                logger.error(f"Webhook update failed: {await response.text()}")        
                return False                                                           
    except Exception as e:                                                             
        logger.error(f"Webhook edit error: {str(e)}")                                  
        return False                                                                   
                                                                                        
async def process_webhook(request_data: dict, client: Client):
    """Handle incoming webhook notifications"""
    try:
        # Extract swap transaction details
        txn = request_data[0]
        text = ""
        # FIX: Use the AsyncSessionFactory directly
        async with AsyncSessionFactory() as session:  # Changed from get_session()
            try:
                # Unnecessary check if swap is successful because webhook is filtered for success
                # if txn.get("type") == "SWAP" and txn.get("transactionError") == None:
                
                # if source is PUMP_FUN, only one token transfer is expected and ownser is not feePayer
                if txn.get("source") == "PUMP_FUN":
                    # Get wallet addresse involved in the swap
                    owner = txn.get("tokenTransfers", None)[0].get("toUserAccount")
                    # Query to find a wallet by address
                    query = select(SmartWallet).where(SmartWallet.address == owner)
                    result = await session.execute(query)
                    
                    # Fetch the first result (if any)
                    wallet = result.scalars().first()
                    # if not wallet:
                    #     logger.error(f"Wallet not found: {owner}")
                    #     return None
                    # Format message details
                    token = txn.get("tokenTransfers", {})[0]
                    text=(
                        f"🔄 Swap detected from: {wallet.name}\n"
                        f"Bought {token.get('tokenAmount', 0):.2f} of {token.get('mint', 'Unknown')}\n"
                        f"in PUMP FUN\n"
                    )
                else:
                    owner = txn.get("feePayer", None)
                    # Query to find a wallet by address
                    query = select(SmartWallet).where(SmartWallet.address == owner)
                    result = await session.execute(query)
                    wallet = result.scalars().first()
                    token_a = txn.get("tokenTransfers", {})[0]
                    token_b = txn.get("tokenTransfers", {})[1]
                    text=(
                        f"🔄 Swap detected from: {wallet.name}\n"
                        f"Swapped {token_a.get('tokenAmount', 0):.2f} {"SOL" if token_a.get('mint') == "So11111111111111111111111111111111111111112" else token_a.get('mint')}\n"
                        f"for {token_b.get('tokenAmount', 0):.2f} {"SOL" if token_a.get('mint') == "So11111111111111111111111111111111111111112" else token_a.get('mint')}\n"
                        # f"Signature: {txn.get('signature', '')[:10]}..."
                    )
                await client.send_message(
                    chat_id=HOMIES_CHAT_ID,
                    text=text
                )
            except Exception as e:
                logger.error(f"Error getting token info: {str(e)}")
                return None
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return None

async def fetch_wallet_holdings(wallet_addresses: list[str]) -> dict:
    """Get ALL token balances for multiple wallets"""
    result = await check_multiple_wallets(wallet_addresses)
    return result

async def monitor_wallets(client: Client):
    async with AsyncSessionFactory() as session:
        try:
            wallets = (await session.execute(select(SmartWallet))).scalars().all()
            
            if not wallets:
                return

            # Get current holdings for ALL wallets
            holdings_map = await fetch_wallet_holdings([w.address for w in wallets])
            
            # Process each wallet
            for wallet in wallets:
                current_mints = holdings_map.get(wallet.address, {})
                
                # Get historical holdings from last 24h
                history = await session.execute(
                    select(WalletHoldingHistory.token_mint)
                    .where(
                        WalletHoldingHistory.wallet_address == wallet.address,
                        WalletHoldingHistory.last_seen >= datetime.now(UTC) - timedelta(hours=24)
                    )
                )
                known_mints = {m for m in history.scalars().all()}
                
                # Find new acquisitions
                new_mints = set(current_mints.keys()) - known_mints
                
                for mint in new_mints:
                    # Record new holding
                    session.add(WalletHoldingHistory(
                        wallet_address=wallet.address,
                        token_mint=mint,
                        first_seen=datetime.now(UTC),
                        last_seen=datetime.now(UTC)
                    ))
                    
                    # Get token info if exists
                    token = await session.execute(
                        select(Token).where(Token.ca == mint)
                    )
                    token = token.scalar_one_or_none()
                    
                    await client.send_message(
                        chat_id=HOMIES_CHAT_ID,
                        text=(
                            f"🚨 {wallet.name} acquired NEW TOKEN\n"
                            f"Mint: `{mint}`\n"
                            f"{f'Symbol: {token.symbol}' if token else ''}"
                        )
                    )
                
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Monitoring error: {str(e)}")
