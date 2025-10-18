#!/usr/bin/env python3
"""Quick test to see the improved error handling"""

import asyncio
import sys
sys.path.insert(0, '.')

from bot.utils.token import get_token_info

async def test():
    print("Testing GMGN API with improved error handling...")
    print("=" * 60)
    
    # Test with a known token
    token = "8vGr1eX9vfpootWiUPYa5kYoGx9bTuRy2Xc4dNMrpump"
    
    result = await get_token_info(token)
    
    if result:
        print("✅ Success! Token data retrieved:")
        print(f"  - Symbol: {result['profile']['symbol']}")
        print(f"  - Holders: {result['profile']['holders']}")
    else:
        print("❌ Failed to retrieve token data")
        print("Check logs above for details")

if __name__ == "__main__":
    asyncio.run(test())
