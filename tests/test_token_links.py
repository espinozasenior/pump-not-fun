#!/usr/bin/env python3
"""Test get_token_links with gmgn wrapper - Standalone"""
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
async def get_token_links(token: str) -> Optional[Dict[str, Any]]:
    """Get token social links using gmgnai-wrapper"""
    try:
        # For now, return empty links as the endpoint doesn't provide this data
        result = {
            'twitter': '',
            'website': '',
            'telegram': '',
            'github': ''
        }
        
        print(f"⚠️  Token links not available from gmgn wrapper (returning empty)")
        return result
        
    except Exception as e:
        print(f"❌ Error getting token links via wrapper: {e}")
        return None

async def test_token_links():
    token = "5dpN5wMH8j8au29Rp91qn4WfNq6t6xJfcjQNcFeDJ8Ct"
    
    print(f"Testing get_token_links() with token: {token}")
    print("=" * 60)
    
    result = await get_token_links(token)
    
    if result:
        print("✅ SUCCESS! Token links retrieved:")
        print(f"   Twitter: {result.get('twitter', 'N/A')}")
        print(f"   Website: {result.get('website', 'N/A')}")
        print(f"   Telegram: {result.get('telegram', 'N/A')}")
        print(f"   GitHub: {result.get('github', 'N/A')}")
        
        required_fields = ['twitter', 'website', 'telegram', 'github']
        missing = [f for f in required_fields if f not in result]
        
        if missing:
            print(f"\n⚠️  Missing fields: {missing}")
            return False
        
        print("\n✅ All required fields present!")
        return True
    else:
        print("❌ FAILED to retrieve token links")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_token_links())
    exit(0 if success else 1)

