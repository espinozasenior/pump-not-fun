#!/usr/bin/env python3
"""Test get_token_profile with gmgn wrapper - Standalone"""
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

# Define the function we're testing
async def get_token_profile(token: str) -> Optional[Dict[str, Any]]:
    """Get token profile using gmgnai-wrapper - combines multiple endpoints"""
    try:
        client = get_gmgn_client()
        
        # Fetch data from multiple endpoints concurrently
        @async_wrap
        def fetch_price():
            return client.getTokenUsdPrice(contractAddress=token)
        
        @async_wrap
        def fetch_holders():
            return client.getTopBuyers(contractAddress=token)
        
        # Get data concurrently
        price_data, holders_data = await asyncio.gather(
            fetch_price(),
            fetch_holders(),
            return_exceptions=True
        )
        
        if isinstance(price_data, Exception) or isinstance(holders_data, Exception):
            print(f"❌ Failed to fetch token data: price={price_data}, holders={holders_data}")
            return None
        
        if not price_data or not holders_data:
            print(f"⚠️  No data returned from gmgn wrapper for token: {token}")
            return None
        
        # Extract holder info from holders response
        holder_info = holders_data.get('holders', {})
        status_now = holder_info.get('statusNow', {})
        
        # Map to expected format (combine available data)
        result = {
            'ca': token,
            'holders': int(holder_info.get('holder_count', 0)),
            'symbol': '',  # Not available from these endpoints
            'logo': '',    # Not available
            'name': '',    # Not available
            'price': float(price_data.get('usd_price', 0.0)),
            'top_10_holder_rate': float(status_now.get('top_10_holder_rate', 0.0)) * 100,
            'volume_1h': 0.0,   # Not available from these endpoints
            'volume_5m': 0.0,   # Not available
            'liquidity': 0.0,   # Not available
        }
        
        print(f"✅ Token profile fetched for {token[:8]}...")
        return result
        
    except Exception as e:
        print(f"❌ Error getting token profile via wrapper: {e}")
        return None

async def test_token_profile():
    # Test with your token address
    token = "5dpN5wMH8j8au29Rp91qn4WfNq6t6xJfcjQNcFeDJ8Ct"
    
    print(f"Testing get_token_profile() with token: {token}")
    print("=" * 60)
    
    result = await get_token_profile(token)
    
    if result:
        print("✅ SUCCESS! Token profile retrieved:")
        print(f"   CA: {result.get('ca', 'N/A')}")
        print(f"   Symbol: {result.get('symbol', 'N/A')}")
        print(f"   Name: {result.get('name', 'N/A')}")
        print(f"   Holders: {result.get('holders', 0)}")
        print(f"   Price: ${result.get('price', 0.0)}")
        print(f"   Liquidity: ${result.get('liquidity', 0.0)}")
        print(f"   Volume 1h: ${result.get('volume_1h', 0.0)}")
        print(f"   Top 10 Holder Rate: {result.get('top_10_holder_rate', 0.0):.2f}%")
        
        # Verify all required fields exist
        required_fields = ['ca', 'holders', 'symbol', 'name', 'price', 'liquidity']
        missing = [f for f in required_fields if f not in result]
        
        if missing:
            print(f"\n⚠️  Missing fields: {missing}")
            return False
        
        print("\n✅ All required fields present!")
        return True
    else:
        print("❌ FAILED to retrieve token profile")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_token_profile())
    exit(0 if success else 1)

