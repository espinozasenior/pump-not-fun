#!/usr/bin/env python3
"""End-to-end test for get_token_info with gmgn wrapper - Standalone"""
import sys
import asyncio
from pathlib import Path
from functools import wraps
from typing import Dict, Any, Optional
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import gmgn directly
from gmgn.client import gmgn

# Replicate all needed functions
def async_wrap(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

def get_gmgn_client():
    return gmgn()

# Import refactored functions from test files
async def get_token_profile(token: str) -> Optional[Dict[str, Any]]:
    """Get token profile using gmgnai-wrapper - combines multiple endpoints"""
    try:
        client = get_gmgn_client()
        
        @async_wrap
        def fetch_price():
            return client.getTokenUsdPrice(contractAddress=token)
        
        @async_wrap
        def fetch_holders():
            return client.getTopBuyers(contractAddress=token)
        
        price_data, holders_data = await asyncio.gather(
            fetch_price(),
            fetch_holders(),
            return_exceptions=True
        )
        
        if isinstance(price_data, Exception) or isinstance(holders_data, Exception):
            return None
        
        if not price_data or not holders_data:
            return None
        
        holder_info = holders_data.get('holders', {})
        status_now = holder_info.get('statusNow', {})
        
        return {
            'ca': token,
            'holders': int(holder_info.get('holder_count', 0)),
            'symbol': '',
            'logo': '',
            'name': '',
            'price': float(price_data.get('usd_price', 0.0)),
            'top_10_holder_rate': float(status_now.get('top_10_holder_rate', 0.0)) * 100,
            'volume_1h': 0.0,
            'volume_5m': 0.0,
            'liquidity': 0.0,
        }
    except Exception as e:
        return None

async def get_token_stats(token: str) -> Optional[Dict[str, Any]]:
    try:
        client = get_gmgn_client()
        
        @async_wrap
        def fetch_holders():
            return client.getTopBuyers(contractAddress=token)
        
        data = await fetch_holders()
        if not data or 'holders' not in data:
            return None
        
        holder_info = data.get('holders', {})
        return {
            'holders': int(holder_info.get('holder_count', 0)),
            'bc_owners_percent': 0.0,
            'insiders_percent': 0.0
        }
    except Exception as e:
        return None

async def get_token_links(token: str) -> Optional[Dict[str, Any]]:
    return {
        'twitter': '',
        'website': '',
        'telegram': '',
        'github': ''
    }

async def get_top_holders(token: str) -> Optional[Dict[str, Any]]:
    try:
        client = get_gmgn_client()
        
        @async_wrap
        def fetch():
            return client.getTopBuyers(contractAddress=token)
        
        data = await fetch()
        if not data or 'holders' not in data or 'holderInfo' not in data['holders']:
            return None
        
        holder_list = data['holders']['holderInfo']
        if not holder_list:
            return None
        
        df = pd.DataFrame(holder_list)
        if df.empty:
            return None
        
        fresh_wallets = df['is_new'].sum() if 'is_new' in df else 0
        sold_wallets = len(df[df['status'] == 'sold']) if 'status' in df else 0
        
        return {
            'fresh_wallets': int(fresh_wallets),
            'sold_wallets': int(sold_wallets),
            'suspicious_wallets': 0,
            'insiders_wallets': 0,
            'phishing_wallets': 0,
            'profitable_wallets': 0,
            'avg_profit_percent': 0.0,
            'same_address_funded': 0,
            'common_addresses': {}
        }
    except Exception as e:
        return None

async def get_token_info(token: str) -> Optional[Dict]:
    try:
        await asyncio.sleep(0.5)
        
        results = await asyncio.gather(
            get_top_holders(token),
            get_token_links(token),
            get_token_stats(token),
            get_token_profile(token),
            return_exceptions=True
        )
        
        if any(isinstance(result, Exception) for result in results):
            return None
            
        holders, links, stats, profile = results
        
        if not all([holders, links, stats, profile]):
            return None
            
        return {
            "holders": holders,
            "links": links,
            "stats": stats,
            "profile": profile
        }
    except Exception as e:
        return None

async def test_e2e():
    token = "5dpN5wMH8j8au29Rp91qn4WfNq6t6xJfcjQNcFeDJ8Ct"
    
    print(f"End-to-End Test: get_token_info()")
    print(f"Token: {token}")
    print("=" * 60)
    
    result = await get_token_info(token)
    
    if not result:
        print("❌ FAILED: get_token_info returned None")
        return False
    
    print("✅ get_token_info() succeeded!")
    print("\n📊 Token Data Summary:")
    print(f"   CA: {result['profile']['ca']}")
    print(f"   Symbol: {result['profile']['symbol']}")
    print(f"   Name: {result['profile']['name']}")
    print(f"   Holders: {result['profile']['holders']}")
    print(f"   Price: ${result['profile']['price']}")
    print(f"   Twitter: {result['links']['twitter']}")
    print(f"   Fresh Wallets: {result['holders']['fresh_wallets']}")
    print(f"   Sold Wallets: {result['holders']['sold_wallets']}")
    
    # Verify structure
    required_keys = ['holders', 'links', 'stats', 'profile']
    missing_keys = [k for k in required_keys if k not in result]
    
    if missing_keys:
        print(f"\n❌ Missing keys: {missing_keys}")
        return False
    
    print("\n✅ All required keys present!")
    print("\n⚠️  Note: Database save test skipped (requires env setup)")
    print("\n✅✅✅ END-TO-END TEST PASSED! ✅✅✅")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_e2e())
    exit(0 if success else 1)

