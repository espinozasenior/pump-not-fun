#!/usr/bin/env python3
"""Test get_token_stats with gmgn wrapper - Standalone"""
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

# Define the function we're testing - ENHANCED VERSION
async def get_token_stats(token: str) -> Optional[Dict[str, Any]]:
    """Get token statistics using gmgnai-wrapper - ENHANCED with getTokenStats()"""
    try:
        client = get_gmgn_client()
        
        @async_wrap
        def fetch_stats():
            return client.getTokenStats(contractAddress=token)
        
        data = await fetch_stats()
        
        if not data or not isinstance(data, dict):
            print(f"⚠️  No stats data returned from gmgn wrapper for token: {token}")
            return None
        
        # Extract statistics - NOW WITH REAL DATA!
        stats = {
            'holders': int(data.get('holder_count', 0)),
            'bc_owners_percent': float(data.get('bluechip_owner_percentage', 0.0)) * 100,
            'insiders_percent': float(data.get('top_rat_trader_percentage', 0.0)) * 100
        }
        
        print(f"✅ Token stats fetched for {token[:8]}... (BC: {stats['bc_owners_percent']:.2f}%, Insiders: {stats['insiders_percent']:.2f}%)")
        return stats
        
    except Exception as e:
        print(f"❌ Error getting token stats via wrapper: {e}")
        return None

async def test_token_stats():
    token = "5dpN5wMH8j8au29Rp91qn4WfNq6t6xJfcjQNcFeDJ8Ct"
    
    print(f"Testing get_token_stats() with token: {token}")
    print("=" * 60)
    
    result = await get_token_stats(token)
    
    if result:
        print("✅ SUCCESS! Token stats retrieved:")
        print(f"   Holders: {result.get('holders', 0)}")
        print(f"   Bluechip Owners %: {result.get('bc_owners_percent', 0.0):.2f}%")
        print(f"   Insiders %: {result.get('insiders_percent', 0.0):.2f}%")
        
        required_fields = ['holders', 'bc_owners_percent', 'insiders_percent']
        missing = [f for f in required_fields if f not in result]
        
        if missing:
            print(f"\n⚠️  Missing fields: {missing}")
            return False
        
        print("\n✅ All required fields present!")
        return True
    else:
        print("❌ FAILED to retrieve token stats")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_token_stats())
    exit(0 if success else 1)

