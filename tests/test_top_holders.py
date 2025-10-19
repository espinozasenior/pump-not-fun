#!/usr/bin/env python3
"""Test get_top_holders with gmgn wrapper - Standalone"""
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

# Replicate async_wrap and client logic
def async_wrap(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

def get_gmgn_client():
    return gmgn()

# Define the function we're testing - ENHANCED VERSION
async def get_top_holders(token: str) -> Optional[Dict[str, Any]]:
    """Get top holders analysis using gmgnai-wrapper - ENHANCED with getTokenHolders()"""
    try:
        client = get_gmgn_client()
        
        @async_wrap
        def fetch():
            return client.getTokenHolders(
                contractAddress=token,
                limit=100,
                cost=20,
                orderby="amount_percentage",
                direction="desc"
            )
        
        data = await fetch()
        
        if not data or not isinstance(data, list):
            print(f"⚠️  No holders data for token: {token}")
            return None
        
        df = pd.DataFrame(data)
        
        if df.empty:
            return None
        
        # Excluded addresses
        EXCLUDED_ADDRESSES = {
            "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9",
            "39azUYFWPz3VHgKCf3VChUwbpURdCHRxjWVowf5jUJjg",
            "AeBwztwXScyNNuQCEdhS54wttRQrw3Nj1UtqddzB4C7b",
        }
        
        # Analysis with new data structure
        fresh_wallets = df['is_new'].sum() if 'is_new' in df else 0
        sold_wallets = (df['sell_tx_count_cur'] > 0).sum() if 'sell_tx_count_cur' in df else 0
        suspicious_wallets = df['is_suspicious'].sum() if 'is_suspicious' in df else 0
        
        # Check for wallet tags in wallet_tag_v2 field
        insiders_count = df['wallet_tag_v2'].apply(
            lambda tag: 'rat_trader' in tag if isinstance(tag, str) else False
        ).sum() if 'wallet_tag_v2' in df else 0
        
        phishing_count = df['wallet_tag_v2'].apply(
            lambda tag: 'transfer_in' in tag if isinstance(tag, str) else False
        ).sum() if 'wallet_tag_v2' in df else 0
        
        profitable_wallets = (df['profit'] > 0).sum() if 'profit' in df else 0
        
        mask = df['cost_cur'] > 0 if 'cost_cur' in df else pd.Series([False] * len(df))
        profit_percent = (df[mask]['profit'] / df[mask]['cost_cur']).mean() * 100 if mask.any() else 0.0
        
        # Same address funding - using account_address
        same_address_funded = 0
        common_addresses = {}
        
        if 'account_address' in df:
            from_address_counts = (
                df['account_address']
                .apply(lambda addr: addr if addr not in EXCLUDED_ADDRESSES else None)
                .value_counts(dropna=True)
            )
            same_address_funded = from_address_counts[from_address_counts > 1].sum()
            common_addresses = from_address_counts[from_address_counts > 1].to_dict()
        
        result = {
            'fresh_wallets': int(fresh_wallets),
            'sold_wallets': int(sold_wallets),
            'suspicious_wallets': int(suspicious_wallets),
            'insiders_wallets': int(insiders_count),
            'phishing_wallets': int(phishing_count),
            'profitable_wallets': int(profitable_wallets),
            'avg_profit_percent': float(profit_percent),
            'same_address_funded': int(same_address_funded),
            'common_addresses': common_addresses
        }
        
        print(f"✅ Top holders analyzed for {token[:8]}... ({len(df)} holders)")
        return result
        
    except Exception as e:
        print(f"❌ Error getting top holders via wrapper: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_top_holders():
    token = "5dpN5wMH8j8au29Rp91qn4WfNq6t6xJfcjQNcFeDJ8Ct"
    
    print(f"Testing get_top_holders() with token: {token}")
    print("=" * 60)
    
    result = await get_top_holders(token)
    
    if result:
        print("✅ SUCCESS! Top holders analyzed:")
        print(f"   Fresh Wallets: {result.get('fresh_wallets', 0)}")
        print(f"   Sold Wallets: {result.get('sold_wallets', 0)}")
        print(f"   Suspicious Wallets: {result.get('suspicious_wallets', 0)}")
        print(f"   Insiders: {result.get('insiders_wallets', 0)}")
        print(f"   Phishing: {result.get('phishing_wallets', 0)}")
        print(f"   Profitable Wallets: {result.get('profitable_wallets', 0)}")
        print(f"   Avg Profit %: {result.get('avg_profit_percent', 0.0):.2f}%")
        print(f"   Same Address Funded: {result.get('same_address_funded', 0)}")
        
        required_fields = [
            'fresh_wallets', 'sold_wallets', 'suspicious_wallets',
            'insiders_wallets', 'phishing_wallets', 'profitable_wallets',
            'avg_profit_percent', 'same_address_funded', 'common_addresses'
        ]
        missing = [f for f in required_fields if f not in result]
        
        if missing:
            print(f"\n⚠️  Missing fields: {missing}")
            return False
        
        print("\n✅ All required fields present!")
        return True
    else:
        print("❌ FAILED to retrieve top holders")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_top_holders())
    exit(0 if success else 1)

