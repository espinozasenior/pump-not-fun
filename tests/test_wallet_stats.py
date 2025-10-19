#!/usr/bin/env python3
"""Test get_wallet_stats with gmgn wrapper - Standalone"""
import sys
import asyncio
from pathlib import Path
from functools import wraps
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import gmgn directly
from gmgn.client import gmgn

# Replicate async_wrap and client logic
def async_wrap(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

def get_gmgn_client():
    return gmgn()

# Define the function we're testing - RENAMED
async def get_wallet_stats(wallet_address: str, period: str = '7d') -> Optional[Dict[str, Any]]:
    """Get general wallet statistics using gmgnai-wrapper (across all tokens)"""
    try:
        client = get_gmgn_client()
        
        # Validate period
        valid_periods = ['1d', '7d', '30d']
        if period not in valid_periods:
            print(f"⚠️  Invalid period {period}, using 7d")
            period = '7d'
        
        @async_wrap
        def fetch():
            return client.getWalletInfo(walletAddress=wallet_address, period=period)
        
        data = await fetch()
        
        if not data or not isinstance(data, dict):
            print(f"⚠️  No data returned for wallet: {wallet_address}")
            return None
        
        # Map to expected format
        result = {
            'pnl': float(data.get('pnl', 0.0)),
            'realized_pnl': float(data.get('realized_profit', 0.0)),
            'unrealized_pnl': float(data.get('unrealized_profit', 0.0)),
            'total_trades': int(data.get('total_trades', 0)),
            'winrate': float(data.get('winrate', 0.0)),
        }
        
        print(f"✅ Wallet stats fetched for {wallet_address[:8]}... (PNL: ${result['pnl']:.2f})")
        return result
        
    except Exception as e:
        print(f"❌ Error getting wallet stats via wrapper: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_wallet_stats():
    # Use your wallet address - token parameter removed
    wallet = "DfMxre4cKmvogbLrPigxmibVTTQDuzjdXojWzjCXXhzj"
    
    print(f"Testing get_wallet_stats()")
    print(f"  Wallet: {wallet}")
    print(f"  Period: 7d")
    print("=" * 60)
    
    result = await get_wallet_stats(wallet, period='7d')
    
    if result:
        print("✅ SUCCESS! Wallet stats retrieved:")
        print(f"   PNL: ${result.get('pnl', 0.0):.2f}")
        print(f"   Realized PNL: ${result.get('realized_pnl', 0.0):.2f}")
        print(f"   Unrealized PNL: ${result.get('unrealized_pnl', 0.0):.2f}")
        print(f"   Total Trades: {result.get('total_trades', 0)}")
        print(f"   Winrate: {result.get('winrate', 0.0):.2f}%")
        
        required_fields = ['pnl', 'realized_pnl', 'unrealized_pnl', 'total_trades', 'winrate']
        missing = [f for f in required_fields if f not in result]
        
        if missing:
            print(f"\n⚠️  Missing fields: {missing}")
            return False
        
        print("\n✅ All required fields present!")
        return True
    else:
        print("❌ FAILED to retrieve wallet stats")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_wallet_stats())
    exit(0 if success else 1)

