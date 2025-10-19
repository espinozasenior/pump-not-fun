# Function Rename: get_wallet_token_stats → get_wallet_stats

## Summary

Renamed `get_wallet_token_stats()` to `get_wallet_stats()` to accurately reflect its purpose and remove an unused parameter.

## Rationale

### Problem with Old Name

**Function:** `get_wallet_token_stats(wallet_address, token_address, period)`

**Issues:**
1. **Misleading name** - Implies token-specific stats but returns general wallet stats
2. **Unused parameter** - `token_address` was passed but completely ignored
3. **Confusing implementation** - Used `getWalletInfo()` which doesn't take token_address

**What was happening:**
```python
# Code passed token_mint but it was ignored:
pnl_data = await get_wallet_token_stats(wallet.address, token_mint)

# Inside function, token_mint was never used:
client.getWalletInfo(walletAddress=wallet_address, period=period)  # ← No token_address!
```

### Solution: Rename and Simplify

**New Function:** `get_wallet_stats(wallet_address, period)`

**Improvements:**
- ✅ Accurate name - "wallet stats" = general wallet statistics
- ✅ No unused parameters - Only takes what it uses
- ✅ Matches GMGN method - Aligns with `getWalletInfo()` purpose
- ✅ Clearer intent - Obvious it's for general wallet performance

---

## GMGN Wrapper Methods Clarification

### getWalletInfo(walletAddress, period) ✅ Used by get_wallet_stats()

**Purpose:** Get **general** wallet statistics across ALL tokens

**Returns:**
```python
{
    'pnl': float,              # Overall wallet PNL
    'realized_profit': float,  # Total realized profit
    'unrealized_profit': float,# Total unrealized profit  
    'total_trades': int,       # Total number of trades
    'winrate': float           # Overall win rate %
}
```

**Use Case:** "How is this wallet performing overall?"

### getWalletOnTokenStats(walletAddress, contractAddress) ⭐ Available but not yet used

**Purpose:** Get wallet statistics for **SPECIFIC** token

**Returns:**
```python
{
    'token_address': str,
    'name': str,
    'symbol': str,
    'holdings': {...},
    'trades': [...],          # Historical trades for THIS token
    'realized_profit': float, # Profit from THIS token
    'unrealized_profit': float,
    'total_trade': int,       # Trades for THIS token
    # ... much more detailed position data
}
```

**Use Case:** "How is this wallet performing on THIS specific token?"

**Future Enhancement:** Could create `get_wallet_token_position()` using this endpoint.

---

## Changes Made

### 1. bot/utils/token.py

**BEFORE:**
```python
async def get_wallet_token_stats(wallet_address: str, token_address: str, period: str = '7d'):
    """Get wallet stats using gmgnai-wrapper"""
    # Uses getWalletInfo(wallet_address, period)
    # token_address parameter IGNORED!
```

**AFTER:**
```python
async def get_wallet_stats(wallet_address: str, period: str = '7d'):
    """Get general wallet statistics using gmgnai-wrapper (across all tokens)"""
    # Uses getWalletInfo(wallet_address, period)
    # Cleaner - only parameters actually used
```

**Changes:**
- Function name: `get_wallet_token_stats` → `get_wallet_stats`
- Parameters: Removed unused `token_address` parameter
- Docstring: Clarified "general wallet statistics across all tokens"
- Log message: Added PNL value to log for debugging

### 2. bot/utils/monitor.py

**Import Updated:**
```python
# BEFORE:
from bot.utils.token import get_token_info, get_wallet_token_stats

# AFTER:
from bot.utils.token import get_token_info, get_wallet_stats
```

**Call Site 1 (Line 164):**
```python
# BEFORE:
pnl_data = await get_wallet_token_stats(wallet.address, token_mint)

# AFTER:
pnl_data = await get_wallet_stats(wallet.address, period='7d')
```

**Call Site 2 (Line 215):**
```python
# BEFORE:
pnl_data = await get_wallet_token_stats(wallet.address, token_mint)

# AFTER:
pnl_data = await get_wallet_stats(wallet.address, period='7d')
```

**Changes:**
- Updated function name in both calls
- Removed token_mint/token_address argument (was unused anyway)
- Made period explicit ('7d')

### 3. tests/test_wallet_stats.py

**BEFORE:**
```python
async def get_wallet_token_stats(wallet_address: str, token_address: str, period: str = '7d'):
    # ...

async def test_wallet_stats():
    wallet = "DfMxre4c..."
    token = "5dpN5wMH..."
    result = await get_wallet_token_stats(wallet, token, period='7d')
```

**AFTER:**
```python
async def get_wallet_stats(wallet_address: str, period: str = '7d'):
    # ...

async def test_wallet_stats():
    wallet = "DfMxre4c..."
    # Token parameter removed - not needed for general wallet stats
    result = await get_wallet_stats(wallet, period='7d')
```

**Changes:**
- Updated function name
- Removed token parameter (not needed)
- Updated test description

### 4. bot/messages/messages.py

**Updated docstring reference:**
```python
# BEFORE:
"""Format wallet PNL data for display - matches get_wallet_token_stats() structure"""

# AFTER:
"""Format wallet PNL data for display - matches get_wallet_stats() structure"""
```

---

## Test Results

```bash
Testing get_wallet_stats()
  Wallet: DfMxre4cKmvogbLrPigxmibVTTQDuzjdXojWzjCXXhzj
  Period: 7d
============================================================
✅ Wallet stats fetched for DfMxre4c... (PNL: $0.71)
✅ SUCCESS! Wallet stats retrieved:
   PNL: $0.71
   Realized PNL: $102269.89
   Unrealized PNL: $0.00
   Total Trades: 0
   Winrate: 0.69%

✅ All required fields present!
```

**Result: ✅ Test PASSED**

---

## Files Modified

- ✅ `bot/utils/token.py` - Function renamed, parameter removed
- ✅ `bot/utils/monitor.py` - Import + 2 calls updated
- ✅ `tests/test_wallet_stats.py` - Test updated
- ✅ `bot/messages/messages.py` - Docstring updated

**Total: 4 files**

---

## Impact

### ✅ Benefits:
- **Clearer naming** - Function name matches what it actually does
- **No confusion** - Obvious it returns general wallet stats, not token-specific
- **Cleaner code** - No unused parameters cluttering signature
- **Better alignment** - Matches GMGN's `getWalletInfo()` naming
- **Maintainability** - Easier for future developers to understand

### ⚠️ Breaking Changes:
- Function signature changed (removed parameter)
- Any external code calling this function needs update
- **Impact:** Minimal - only 2 internal call sites

### 🔧 Backward Compatibility:
- **Not maintained** - This is a breaking rename
- **Acceptable** - All usage is internal to this codebase
- **Migration** - All call sites updated in this commit

---

## Future Enhancement Opportunity

Now that naming is clear, we could add token-specific stats:

```python
async def get_wallet_token_position(wallet_address: str, token_address: str) -> Optional[Dict[str, Any]]:
    """
    Get wallet position for SPECIFIC token using getWalletOnTokenStats().
    
    Returns detailed position data including:
    - Current holdings
    - Historical trades for this token pair
    - Realized/unrealized profit for this token
    - Average costs and trade history
    """
    client = get_gmgn_client()
    
    @async_wrap
    def fetch():
        return client.getWalletOnTokenStats(
            walletAddress=wallet_address,
            contractAddress=token_address
        )
    
    data = await fetch()
    # Map detailed position data...
    return result
```

This would give you:
- `get_wallet_stats()` - **"How is my wallet doing overall?"**
- `get_wallet_token_position()` - **"What's my position in THIS token?"**

Could show detailed token-specific P&L in swap notifications!

---

## Commit Message

```
refactor(token): Rename get_wallet_token_stats to get_wallet_stats

Remove unused token_address parameter and clarify function purpose.

BREAKING CHANGE: Function signature changed

- Function: get_wallet_token_stats() → get_wallet_stats()
- Parameters: (wallet_address, token_address, period) → (wallet_address, period)
- Reason: token_address was never used, function returns general wallet stats

The function uses getWalletInfo() which provides general wallet statistics
across all tokens, not token-specific stats. The old name and signature were
misleading.

Updated:
- bot/utils/token.py: Function definition
- bot/utils/monitor.py: Import + 2 calls
- tests/test_wallet_stats.py: Test script
- bot/messages/messages.py: Docstring reference

All tests passing. No functional changes, just clearer naming.
```

---

## Status

✅ **COMPLETE** - Ready to commit

Function renamed, all call sites updated, all tests passing.

