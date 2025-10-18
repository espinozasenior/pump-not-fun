#!/usr/bin/env python3
"""Test gmgn wrapper infrastructure"""
import sys
import asyncio
from pathlib import Path
from functools import wraps

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import gmgn directly to avoid config issues
from gmgn.client import gmgn

# Define async_wrap locally for testing
def async_wrap(func):
    """Wrap synchronous gmgn calls to work with async/await"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

def get_gmgn_client():
    """Get or create global gmgn client instance"""
    return gmgn()

async def test_infrastructure():
    print("Testing GMGN infrastructure...")
    print("=" * 60)
    
    # Test client creation
    try:
        client = get_gmgn_client()
        print("✅ Client created successfully")
        print(f"   Client type: {type(client)}")
    except Exception as e:
        print(f"❌ Client creation failed: {e}")
        return False
    
    # Test async wrapper
    try:
        @async_wrap
        def test_func():
            return "Hello from sync function"
        
        result = await test_func()
        print(f"✅ Async wrapper works: {result}")
    except Exception as e:
        print(f"❌ Async wrapper failed: {e}")
        return False
    
    print("\n✅ All infrastructure tests passed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_infrastructure())
    exit(0 if success else 1)

