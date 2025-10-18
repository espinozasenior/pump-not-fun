#!/usr/bin/env python3
"""Test raw gmgn API response"""
import sys
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gmgn.client import gmgn

# Test with the user's token
token = "5dpN5wMH8j8au29Rp91qn4WfNq6t6xJfcjQNcFeDJ8Ct"

print("Testing with user's token...")
print(f"Token: {token}")

print(f"Testing raw GMGN API response for token: {token}")
print("=" * 60)

client = gmgn()

print("\n🔍 Testing getTokenInfo...")
data = client.getTokenInfo(contractAddress=token)
print(json.dumps(data, indent=2))

print("\n\n🔍 Testing getTopBuyers...")
data2 = client.getTopBuyers(contractAddress=token)
print(json.dumps(data2, indent=2) if isinstance(data2, dict) else f"Type: {type(data2)}, First 500 chars: {str(data2)[:500]}")

print("\n\n🔍 Testing getSecurityInfo...")
data3 = client.getSecurityInfo(contractAddress=token)
print(json.dumps(data3, indent=2) if isinstance(data3, dict) else str(data3)[:500])

print("\n\n🔍 Testing getTokenUsdPrice...")
data4 = client.getTokenUsdPrice(contractAddress=token)
print(json.dumps(data4, indent=2) if isinstance(data4, dict) else str(data4)[:500])

