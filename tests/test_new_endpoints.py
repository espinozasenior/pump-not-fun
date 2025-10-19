#!/usr/bin/env python3
"""Test new gmgn wrapper endpoints - Discovery"""
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))
from gmgn.client import gmgn

TOKEN = "5dpN5wMH8j8au29Rp91qn4WfNq6t6xJfcjQNcFeDJ8Ct"

print("=" * 80)
print("TESTING NEW GMGN WRAPPER ENDPOINTS - DISCOVERY")
print("=" * 80)
print(f"Token: {TOKEN}\n")

client = gmgn()

# Test 1: getTokenStats
print("\n" + "=" * 80)
print("🔍 TEST 1: getTokenStats()")
print("=" * 80)
try:
    stats = client.getTokenStats(contractAddress=TOKEN)
    print("Response Type:", type(stats))
    print("\nFull Response:")
    print(json.dumps(stats, indent=2))
    
    print("\n📋 Fields Available:")
    if isinstance(stats, dict):
        for key in stats.keys():
            print(f"   • {key}: {type(stats[key]).__name__}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: getTokenTrends
print("\n" + "=" * 80)
print("🔍 TEST 2: getTokenTrends()")
print("=" * 80)
try:
    trends = client.getTokenTrends(contractAddress=TOKEN)
    print("Response Type:", type(trends))
    print("\nFull Response:")
    print(json.dumps(trends, indent=2)[:3000])  # First 3000 chars
    
    print("\n📋 Fields Available:")
    if isinstance(trends, dict):
        for key in trends.keys():
            print(f"   • {key}: {type(trends[key]).__name__}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: getTokenHolders (first 20)
print("\n" + "=" * 80)
print("🔍 TEST 3: getTokenHolders()")
print("=" * 80)
try:
    holders = client.getTokenHolders(
        contractAddress=TOKEN, 
        limit=20,
        cost=20,
        orderby="amount_percentage",
        direction="desc"
    )
    print("Response Type:", type(holders))
    print("\nFull Response (first 2000 chars):")
    print(json.dumps(holders, indent=2)[:2000])
    
    print("\n📋 Fields Available:")
    if isinstance(holders, list) and len(holders) > 0:
        print("First holder fields:")
        for key in holders[0].keys():
            print(f"   • {key}: {type(holders[0][key]).__name__}")
    elif isinstance(holders, dict):
        for key in holders.keys():
            print(f"   • {key}: {type(holders[key]).__name__}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("DISCOVERY TEST COMPLETE")
print("=" * 80)

