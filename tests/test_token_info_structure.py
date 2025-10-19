#!/usr/bin/env python3
"""Test actual token_info structure matches expected usage"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Set env vars
import os
os.environ.setdefault('DATABASE_URL', 'postgresql://x:x@x/x')
os.environ.setdefault('HELIUS_API_KEY', 'x')
os.environ.setdefault('BOT_TOKEN', 'x')
os.environ.setdefault('WALLET_PRIVATE_KEY', '5' * 88)

from bot.utils.token import get_token_info

async def test():
    token = '5dpN5wMH8j8au29Rp91qn4WfNq6t6xJfcjQNcFeDJ8Ct'
    
    print("Testing token_info structure compatibility...")
    print("=" * 80)
    
    result = await get_token_info(token)
    
    if not result:
        print("❌ Failed to get token_info")
        return False
    
    print("\n✅ token_info retrieved successfully!")
    print("\nStructure Analysis:")
    print("-" * 80)
    
    # Check top-level keys
    required_keys = ['holders', 'links', 'stats', 'profile']
    for key in required_keys:
        if key in result:
            print(f"✅ '{key}' key exists")
            print(f"   Type: {type(result[key])}")
            if isinstance(result[key], dict):
                print(f"   Fields: {list(result[key].keys())[:5]}...")
        else:
            print(f"❌ '{key}' key MISSING!")
    
    # Test specific accesses used in messages.py
    print("\n" + "=" * 80)
    print("FIELD ACCESS COMPATIBILITY TEST")
    print("=" * 80)
    
    tests = [
        ("token_info.get('profile').get('ca')", lambda: result.get('profile').get('ca')),
        ("token_info.get('profile').get('name')", lambda: result.get('profile').get('name')),
        ("token_info.get('profile').get('symbol')", lambda: result.get('profile').get('symbol')),
        ("token_info.get('profile').get('price')", lambda: result.get('profile').get('price')),
        ("token_info.get('profile').get('liquidity')", lambda: result.get('profile').get('liquidity')),
        ("token_info.get('stats').get('holders')", lambda: result.get('stats').get('holders')),
        ("token_info.get('holders').get('avg_profit_percent')", lambda: result.get('holders').get('avg_profit_percent')),
        ("token_info.get('profile').get('top_10_holder_rate')", lambda: result.get('profile').get('top_10_holder_rate')),
        ("token_info.get('stats').get('bc_owners_percent')", lambda: result.get('stats').get('bc_owners_percent')),
        ("token_info.get('holders').get('profitable_wallets')", lambda: result.get('holders').get('profitable_wallets')),
        ("token_info.get('holders').get('fresh_wallets')", lambda: result.get('holders').get('fresh_wallets')),
        ("token_info.get('holders').get('sold_wallets')", lambda: result.get('holders').get('sold_wallets')),
        ("token_info.get('holders').get('insiders_wallets')", lambda: result.get('holders').get('insiders_wallets')),
        ("token_info.get('stats').get('insiders_percent')", lambda: result.get('stats').get('insiders_percent')),
        ("token_info.get('holders').get('phishing_wallets')", lambda: result.get('holders').get('phishing_wallets')),
        ("token_info.get('holders').get('suspicious_wallets')", lambda: result.get('holders').get('suspicious_wallets')),
        ("token_info.get('holders').get('same_address_funded')", lambda: result.get('holders').get('same_address_funded')),
        ("token_info.get('links').get('twitter')", lambda: result.get('links').get('twitter')),
        ("token_info.get('links').get('telegram')", lambda: result.get('links').get('telegram')),
        ("token_info.get('links').get('github')", lambda: result.get('links').get('github')),
        ("token_info.get('links').get('website')", lambda: result.get('links').get('website')),
    ]
    
    failed = []
    for test_name, test_func in tests:
        try:
            value = test_func()
            print(f"✅ {test_name} = {value}")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
            failed.append(test_name)
    
    if failed:
        print(f"\n❌ FAILED TESTS: {len(failed)}")
        for f in failed:
            print(f"   - {f}")
        return False
    else:
        print(f"\n✅ ALL {len(tests)} FIELD ACCESSES WORK!")
        return True

if __name__ == "__main__":
    success = asyncio.run(test())
    exit(0 if success else 1)
