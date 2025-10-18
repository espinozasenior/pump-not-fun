from logger.logger import logger
from config.settings import HELIUS_API_KEY
from database.database import SmartWallet, Token, WalletHoldingHistory, AsyncSessionFactory
from sqlalchemy import select
from datetime import datetime, timedelta, UTC
import aiohttp
from typing import Dict, List, Optional, Any
import asyncio


async def get_wallet_transactions(wallet_address: str, days: int = 45) -> Optional[List[Dict[str, Any]]]:
    """
    Fetches transaction history for a wallet over the specified period using Helius API.
    
    Args:
        wallet_address (str): The wallet address to fetch transactions for
        days (int): Number of days to look back (default: 7)
        
    Returns:
        Optional[List[Dict[str, Any]]]: List of transaction data or None if request failed
    """
    api_url = f"https://api.helius.xyz/v0/addresses/{wallet_address}/transactions"
    
    # Calculate start time (7 days ago)
    start_time = int((datetime.now(UTC) - timedelta(days=days)).timestamp())
    
    params = {
        "api-key": HELIUS_API_KEY,
        # Removed type filter to get all transaction types, not just SWAPs
        "startTime": start_time,  # Start time based on days parameter
        "endTime": int(datetime.now(UTC).timestamp())  # Current time as end time
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params) as response:
                if response.status == 200:
                    transactions = await response.json()
                    return transactions
                else:
                    logger.error(f"Failed to fetch transactions: {await response.text()}")
                    return None
    except Exception as e:
        logger.error(f"Error fetching wallet transactions: {str(e)}")
        return None


async def calculate_token_pnl(wallet_address: str, token_info: Optional[dict], days: int = 7) -> Dict[str, Any]:
    """
    Calculates realized PNL for a specific token in a wallet over the specified period.
    
    Args:
        wallet_address (str): The wallet address
        token_info (Optional[dict]): The token mint information
        days (int): Number of days to look back (default: 7)
        
    Returns:
        Dict[str, Any]: Dictionary containing PNL data
    """
    # Check if token_info is None or missing required fields
    if token_info is None:
        logger.error("Token info is None")
        return {
            "invested": 0,
            "realized_pnl": 0,
            "buy_volume": 0,
            "sell_volume": 0,
            "buy_transactions": 0,
            "sell_transactions": 0,
            "avg_buy_price": 0,
            "avg_sell_price": 0
        }
        
    # Ensure token_info has the required mint field
    if "mint" not in token_info:
        logger.error("Token info missing 'mint' field")
        return {
            "invested": 0,
            "realized_pnl": 0,
            "buy_volume": 0,
            "sell_volume": 0,
            "buy_transactions": 0,
            "sell_transactions": 0,
            "avg_buy_price": 0,
            "avg_sell_price": 0
        }
        
    # Increase history days to ensure we capture all transactions
    history_days = max(days * 3, 45)
    transactions = await get_wallet_transactions(wallet_address, history_days)
    
    if not transactions:
        return {
            "invested": 0,
            "realized_pnl": 0,
            "buy_volume": 0,
            "sell_volume": 0,
            "buy_transactions": 0,
            "sell_transactions": 0,
            "avg_buy_price": 0,
            "avg_sell_price": 0
        }
    
    # Filter transactions for the specific token
    token_transactions = []
    for txn in transactions:
        token_transfers = txn.get("tokenTransfers", [])
        for transfer in token_transfers:
            if transfer.get("mint") == token_info.get("mint"):
                token_transactions.append(txn)
                break
    
    # Calculate buy and sell volumes and prices
    buy_volume = 0
    sell_volume = 0
    buy_value_sol = 0
    sell_value_sol = 0
    buy_transactions = 0
    sell_transactions = 0
    
    # SOL mint address
    SOL_MINT = "So11111111111111111111111111111111111111112"
    
    # Debug information
    logger.info(f"Found {len(token_transactions)} transactions for token {token_info.get('mint')}")
    
    # First pass: Process buy transactions to calculate average buy price
    for txn in token_transactions:
        token_transfers = txn.get("tokenTransfers", [])
        
        # Skip if no token transfers
        if not token_transfers:
            continue
            
        # Identify token transfers for our specific token and SOL
        target_token_transfers = []
        sol_transfers = []
        
        for transfer in token_transfers:
            if transfer.get("mint") == token_info.get("mint"):
                target_token_transfers.append(transfer)
            elif transfer.get("mint") == SOL_MINT:
                sol_transfers.append(transfer)
        
        # Skip if no transfers for our target token
        if not target_token_transfers:
            continue
            
        # Determine if this is a buy or sell transaction
        is_buying = False
        is_selling = False
        token_amount = 0
        sol_amount = 0
        
        # Check if we're receiving the token (buying) or sending the token (selling)
        for transfer in target_token_transfers:
            if transfer.get("toUserAccount") == wallet_address:
                is_buying = True
                token_amount += transfer.get("tokenAmount", 0)
            elif transfer.get("fromUserAccount") == wallet_address:
                is_selling = True
                token_amount += transfer.get("tokenAmount", 0)
        
        # Debug transaction type
        if is_buying and not is_selling:
            logger.info(f"Found BUY transaction: {txn.get('signature')}")
        elif is_selling and not is_buying:
            logger.info(f"Found SELL transaction: {txn.get('signature')}")
        
        # For buys: Look for SOL going out
        if is_buying and not is_selling:
            for transfer in sol_transfers:
                if transfer.get("fromUserAccount") == wallet_address:
                    sol_amount += transfer.get("tokenAmount", 0)
            
            # If we found both token coming in and SOL going out, it's a valid buy
            if token_amount > 0 and sol_amount > 0:
                buy_volume += token_amount
                buy_value_sol += sol_amount
                buy_transactions += 1
                logger.info(f"Recorded BUY: {token_amount} tokens for {sol_amount} SOL")
    
    # Calculate average buy price after processing all buy transactions
    avg_buy_price_sol = buy_value_sol / buy_volume if buy_volume > 0 else 0
    logger.info(f"Average buy price: {avg_buy_price_sol} SOL per token")
    
    # Second pass: Process sell transactions using the calculated average buy price
    for txn in token_transactions:
        token_transfers = txn.get("tokenTransfers", [])
        
        # Skip if no token transfers
        if not token_transfers:
            continue
            
        # Identify token transfers for our specific token and SOL
        target_token_transfers = []
        sol_transfers = []
        
        for transfer in token_transfers:
            if transfer.get("mint") == token_info.get("mint"):
                target_token_transfers.append(transfer)
            elif transfer.get("mint") == SOL_MINT:
                sol_transfers.append(transfer)
        
        # Skip if no transfers for our target token
        if not target_token_transfers:
            continue
            
        # Determine if this is a sell transaction
        is_selling = False
        token_amount = 0
        sol_amount = 0
        
        # Check if we're sending the token (selling)
        for transfer in target_token_transfers:
            if transfer.get("fromUserAccount") == wallet_address:
                is_selling = True
                token_amount += transfer.get("tokenAmount", 0)
        
        # Skip if not a sell transaction
        if not is_selling:
            continue
            
        logger.info(f"Processing SELL transaction: {txn.get('signature')}")
        
        # First check for SOL transfers
        for transfer in sol_transfers:
            if transfer.get("toUserAccount") == wallet_address:
                sol_amount += transfer.get("tokenAmount", 0)
        
        # If no SOL was received, check for other tokens received in the same transaction
        if sol_amount == 0:
            other_token_transfers = []
            for transfer in token_transfers:
                # Skip the target token and SOL transfers
                if transfer.get("mint") != token_info.get("mint") and transfer.get("mint") != SOL_MINT:
                    # Only count tokens received by the wallet
                    if transfer.get("toUserAccount") == wallet_address:
                        other_token_transfers.append(transfer)
            
            # Log other tokens received
            if other_token_transfers:
                for other_transfer in other_token_transfers:
                    other_token_mint = other_transfer.get("mint")
                    other_token_amount = other_transfer.get("tokenAmount", 0)
                    logger.info(f"Found non-SOL token received in sell: {other_token_mint}, amount: {other_token_amount}")
                    
                    # We don't have price data for these tokens, so we'll estimate based on the target token's average buy price
                    # This assumes the trade was roughly at market value
                    estimated_sol_value = avg_buy_price_sol * token_amount if avg_buy_price_sol > 0 else 0
                    sol_amount += estimated_sol_value
                    logger.info(f"Estimated SOL value for received token: {estimated_sol_value} SOL")
        
        # If we found token going out, record it as a sell
        if token_amount > 0:
            sell_volume += token_amount
            sell_value_sol += sol_amount
            sell_transactions += 1
            logger.info(f"Recorded SELL: {token_amount} tokens for {sol_amount} SOL")
    
    # Log summary
    logger.info(f"Summary - Buy transactions: {buy_transactions}, Sell transactions: {sell_transactions}")
    logger.info(f"Summary - Buy volume: {buy_volume}, Sell volume: {sell_volume}")
    
    # Calculate average sell price in SOL (buy price was already calculated)
    avg_sell_price_sol = sell_value_sol / sell_volume if sell_volume > 0 else 0
    
    # Calculate realized PNL in SOL
    realized_pnl_sol = sell_value_sol - (avg_buy_price_sol * sell_volume) if sell_volume > 0 else 0
    
    # Calculate unrealized PNL for remaining tokens
    remaining_tokens = buy_volume - sell_volume
    unrealized_pnl = 0  # We don't have current price data to calculate unrealized PNL
    
    # Calculate profit percentage if applicable
    profit_percentage = (realized_pnl_sol / (avg_buy_price_sol * sell_volume)) * 100 if sell_volume > 0 and avg_buy_price_sol > 0 else 0
    
    # Calculate remaining investment
    remaining_investment = avg_buy_price_sol * (buy_volume - sell_volume) if buy_volume > sell_volume else 0
    
    # Calculate total investment (including what's been sold and what remains)
    total_investment = buy_value_sol
    
    return {
        "token_mint": token_info.get("mint"),
        "invested": buy_value_sol,  # Total amount of SOL used to buy target token
        "remaining_investment": remaining_investment,
        "realized_pnl": realized_pnl_sol,
        "profit_percentage": profit_percentage,
        "buy_volume": buy_volume,
        "sell_volume": sell_volume,
        "remaining_tokens": buy_volume - sell_volume,
        "avg_buy_price": avg_buy_price_sol,
        "avg_sell_price": avg_sell_price_sol,
        "buy_transactions": buy_transactions,
        "sell_transactions": sell_transactions,
        "total_transactions": buy_transactions + sell_transactions
    }


async def calculate_wallet_pnl(wallet_address: str, days: int = 7) -> Dict[str, Any]:
    """
    Calculates total realized PNL for a wallet across all tokens over the specified period.
    
    Args:
        wallet_address (str): The wallet address
        days (int): Number of days to look back (default: 7)
        
    Returns:
        Dict[str, Any]: Dictionary containing wallet PNL data
    """
    async with AsyncSessionFactory() as session:
        try:
            # Get wallet info
            wallet_query = select(SmartWallet).where(SmartWallet.address == wallet_address)
            wallet_result = await session.execute(wallet_query)
            wallet = wallet_result.scalar_one_or_none()
            
            if not wallet:
                logger.error(f"Wallet not found: {wallet_address}")
                return {"error": "Wallet not found"}
            
            # Get historical holdings from the specified period
            history_query = select(WalletHoldingHistory.token_mint).where(
                WalletHoldingHistory.wallet_address == wallet_address,
                WalletHoldingHistory.first_seen >= datetime.now(UTC) - timedelta(days=days)
            ).distinct()
            
            history_result = await session.execute(history_query)
            token_mints = history_result.scalars().all()
            
            # Calculate PNL for each token
            token_pnl_tasks = [calculate_token_pnl(wallet_address, {"mint": mint}, days) for mint in token_mints]
            token_pnls = await asyncio.gather(*token_pnl_tasks)
            
            # Calculate total metrics
            total_realized_pnl = sum(pnl["realized_pnl"] for pnl in token_pnls)
            total_invested = sum(pnl["invested"] for pnl in token_pnls)
            total_remaining_investment = sum(pnl["remaining_investment"] for pnl in token_pnls)
            total_buy_transactions = sum(pnl["buy_transactions"] for pnl in token_pnls)
            total_sell_transactions = sum(pnl["sell_transactions"] for pnl in token_pnls)
            total_transactions = total_buy_transactions + total_sell_transactions
            
            # Calculate overall profit percentage
            overall_profit_percentage = (total_realized_pnl / (total_invested - total_remaining_investment)) * 100 if (total_invested - total_remaining_investment) > 0 else 0
            
            return {
                "wallet_address": wallet_address,
                "wallet_name": wallet.name,
                "period_days": days,
                "total_invested": total_invested,
                "total_remaining_investment": total_remaining_investment,
                "total_realized_pnl": total_realized_pnl,
                "overall_profit_percentage": overall_profit_percentage,
                "total_buy_transactions": total_buy_transactions,
                "total_sell_transactions": total_sell_transactions,
                "total_transactions": total_transactions,
                "token_pnls": token_pnls
            }
            
        except Exception as e:
            logger.error(f"Error calculating wallet PNL: {str(e)}")
            return {"error": str(e)}


async def calculate_all_wallets_pnl(days: int = 7) -> List[Dict[str, Any]]:
    """
    Calculates realized PNL for all tracked wallets over the specified period.
    
    Args:
        days (int): Number of days to look back (default: 7)
        
    Returns:
        List[Dict[str, Any]]: List of wallet PNL data
    """
    async with AsyncSessionFactory() as session:
        try:
            # Get all wallets
            wallets_query = select(SmartWallet)
            wallets_result = await session.execute(wallets_query)
            wallets = wallets_result.scalars().all()
            
            # Calculate PNL for each wallet
            wallet_pnl_tasks = [calculate_wallet_pnl(wallet.address, days) for wallet in wallets]
            wallet_pnls = await asyncio.gather(*wallet_pnl_tasks)
            
            return wallet_pnls
            
        except Exception as e:
            logger.error(f"Error calculating all wallets PNL: {str(e)}")
            return [{"error": str(e)}]