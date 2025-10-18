# GMGN.AI API - 403 Forbidden Error Analysis & Solutions

## Problem Summary

The application is receiving **403 Forbidden** errors from GMGN.ai API endpoints. This is due to Cloudflare protection that blocks automated/bot requests.

### Affected Endpoints
- `https://gmgn.ai/api/v1/mutil_window_token_link_rug_vote/sol/{token}`
- `https://gmgn.ai/defi/quotation/v1/tokens/top_holders/sol/{token}`
- `https://gmgn.ai/api/v1/token_stat/sol/{token}`
- `https://gmgn.ai/api/v1/mutil_window_token_info`

## Changes Made

### 1. Updated HTTP Headers ✅
- Added modern browser User-Agent (Chrome 130)
- Added security headers: `Sec-Fetch-*`, `Sec-Ch-Ua-*`
- Better mimicking of real browser requests

### 2. Connection Pooling ✅
- Implemented shared `aiohttp.ClientSession` for connection reuse
- Added connection limits and DNS caching
- Reduced overhead and improved performance

### 3. Retry Logic with Exponential Backoff ✅
- Each API function now retries up to 2 times
- Progressive delays (1s, 2s) between retries
- Separate error logging for warnings vs final failures

### 4. Better Error Handling ✅
- Graceful degradation when APIs fail
- Detailed logging showing which parts failed
- Informative error messages about Cloudflare protection

## Why 403 Errors Persist

Despite improvements, GMGN.ai uses **Cloudflare Bot Protection** which:
- Detects automated requests through fingerprinting
- Requires JavaScript challenges
- May use TLS fingerprinting
- Tracks request patterns

## Solutions (Ranked by Feasibility)

### ⭐ **Solution 1: Use Proxies with Rotating IPs**
```python
# Add proxy support to session
connector = aiohttp.TCPConnector(
    limit=10,
    limit_per_host=5,
    ttl_dns_cache=300
)

proxy = "http://your-proxy-service:port"
session = aiohttp.ClientSession(
    connector=connector,
    headers=headers
)

# In requests
async with session.get(url, proxy=proxy) as response:
    ...
```

**Pros:**
- Most reliable for bypassing Cloudflare
- Can use residential proxies for better results
- Services: BrightData, Oxylabs, SmartProxy

**Cons:**
- Costs money ($50-500/month)
- Adds latency

---

### ⭐⭐ **Solution 2: Use Cloudflare Bypass Libraries**

```bash
pip install cloudscraper
# or
pip install curl_cffi
```

```python
import cloudscraper

scraper = cloudscraper.create_scraper()
response = scraper.get(url)
```

**Pros:**
- Free
- Handles Cloudflare challenges automatically
- Works with many protected sites

**Cons:**
- May not work with latest Cloudflare protection
- Synchronous (blocks async flow)
- Requires updates when Cloudflare changes

---

### ⭐⭐⭐ **Solution 3: Browser Automation (Playwright/Selenium)**

```python
from playwright.async_api import async_playwright

async def get_token_data_via_browser(token: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(f"https://gmgn.ai/sol/token/{token}")
        # Extract data from page
        await browser.close()
```

**Pros:**
- Most reliable - acts like real user
- Can handle any JavaScript challenge
- Can scrape rendered data

**Cons:**
- Much slower (2-5 seconds per request)
- High resource usage
- Expensive at scale

---

### ⭐⭐ **Solution 4: Find Alternative API/Data Sources**

Look for alternative sources for token data:
- **Jupiter API** - for price/swap data
- **Helius API** - for Solana token metadata
- **Birdeye API** - for DeFi analytics
- **CoinGecko/CoinMarketCap** - for basic token info
- **Direct Solana RPC** - for on-chain data

**Pros:**
- Legitimate API access
- Better rate limits
- More reliable

**Cons:**
- May not have exact same data as GMGN
- Some require API keys
- Different data structure

---

### ⭐ **Solution 5: Contact GMGN for API Access**

Reach out to GMGN.ai team for:
- Official API key
- IP whitelist
- Developer partnership

**Pros:**
- Legitimate access
- No workarounds needed
- Better support

**Cons:**
- May cost money
- May require business justification
- Takes time to get approval

---

## Recommended Approach

### Short-term (Immediate):
1. ✅ **Already implemented**: Better headers, retry logic, error handling
2. Try **cloudscraper** library (quick to test)
3. Add rate limiting between requests

### Medium-term:
1. Implement **rotating proxy service**
2. Or switch to **alternative data sources** (Helius, Birdeye)

### Long-term:
1. Contact GMGN for **official API access**
2. Build hybrid solution using multiple data sources

## Testing the Current Changes

The code now:
- Has better headers
- Retries failed requests
- Provides clear error messages
- Won't crash when API fails

However, **403 errors will likely continue** until you implement one of the solutions above (proxies, cloudscraper, or alternative APIs).

## Example: Adding Cloudscraper (Quick Fix)

```bash
pip install cloudscraper aiohttp-cloudscraper
```

Then modify `bot/utils/token.py`:
```python
import cloudscraper
from functools import lru_cache

@lru_cache(maxsize=1)
def get_scraper():
    return cloudscraper.create_scraper()

async def get_top_holders(token: str):
    scraper = get_scraper()
    url = f"{GMGN_BASE_URL}/tokens/top_holders/sol/{token}"
    
    # Use scraper instead of aiohttp
    response = await asyncio.to_thread(
        scraper.get, 
        url, 
        params=quote_params
    )
    
    if response.status_code == 200:
        return response.json()
    ...
```

This wraps sync cloudscraper in async context.

---

## Need Help?

If you want me to implement any of these solutions, let me know which approach you prefer:
1. **Cloudscraper** (easiest, test first)
2. **Proxy service** (most reliable, costs money)
3. **Alternative APIs** (different data, but legitimate)
4. **Browser automation** (slowest, but works)

