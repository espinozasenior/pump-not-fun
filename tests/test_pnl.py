import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.resolve()))

from bot.utils.pnl import calculate_token_pnl, get_wallet_transactions
from datetime import datetime, timedelta, UTC
import json


async def test_get_wallet_transactions():
    """Test fetching transactions for a specific wallet"""
    wallet_address = "8VofoLz7RNn5A8Vqj2Er9p4gFMan7LXbHPieRaujcv3g"
    days = 30  # Look back 30 days to ensure we capture enough history
    
    print(f"\nFetching transactions for wallet {wallet_address} over the last {days} days...")
    transactions = await get_wallet_transactions(wallet_address, days)
    
    if transactions:
        print(f"Successfully fetched {len(transactions)} transactions")
        # Print a sample transaction for debugging
        if transactions:
            print("Sample transaction:")
            print(json.dumps(transactions[0], indent=2)[:500] + "...")
    else:
        print("Failed to fetch transactions")
    
    return transactions


async def test_calculate_token_pnl():
    """Test calculating PNL for a specific token in a wallet"""
    wallet_address = "AHduHwCF1DQ6RA4ec7Dj1izRCVadjyXqTjumv6XCz3Eo"
    token_mint = "GYTd9XbZTfwicCV28LGkwiDF4DgpXTTAi2UeCajfpump"
    days = 60  # Look back 15 days to match the user's statement about transactions
    
    print(f"\nCalculating PNL for token {token_mint} in wallet {wallet_address} over the last {days} days...")
    
    # We expect 6 buys and 3 sells for this wallet/token combination
    print(f"Expected: 6 buys and 3 sells")
    
    token_info = {"mint": token_mint}
    pnl_data = await calculate_token_pnl(wallet_address, token_info, days)
    
    print("\nPNL Results:")
    print(f"Token Mint: {pnl_data['token_mint']}")
    print(f"Invested: {pnl_data['invested']} SOL")
    print(f"Remaining Investment: {pnl_data['remaining_investment']} SOL")
    print(f"Realized PNL: {pnl_data['realized_pnl']} SOL")
    print(f"Profit Percentage: {pnl_data['profit_percentage']:.2f}%")
    print(f"Buy Volume: {pnl_data['buy_volume']} tokens")
    print(f"Sell Volume: {pnl_data['sell_volume']} tokens")
    print(f"Remaining Tokens: {pnl_data['remaining_tokens']} tokens")
    print(f"Average Buy Price: {pnl_data['avg_buy_price']} SOL/token")
    print(f"Average Sell Price: {pnl_data['avg_sell_price']} SOL/token")
    print(f"Buy Transactions: {pnl_data['buy_transactions']}")
    print(f"Sell Transactions: {pnl_data['sell_transactions']}")
    print(f"Total Transactions: {pnl_data['total_transactions']}")
    
    return pnl_data


async def main():
    """Run all tests"""
    print("=== Testing PNL Calculation Functions ===")
    
    # Test transaction fetching
    await test_get_wallet_transactions()
    
    # Test token PNL calculation
    await test_calculate_token_pnl()


if __name__ == "__main__":
    asyncio.run(main())