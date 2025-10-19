"""
Token information utilities using gmgnai-wrapper library.

This module uses the gmgnai-wrapper to bypass Cloudflare protection
when fetching token data from GMGN.ai.

Refactored: 2025-10-18
"""
from logger.logger import logger
from database.database import AsyncSession, Token
from typing import Any, Dict, Optional, TypedDict
import aiohttp
import asyncio
import pandas as pd
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime

# GMGN Wrapper imports
from gmgn.client import gmgn
from functools import wraps

class TokenInfo(TypedDict):
    holders: dict
    links: dict 
    stats: dict
    profile:dict

# ============================================================================
# GMGN Wrapper - Async Adapter Layer
# ============================================================================

def async_wrap(func):
    """Wrap synchronous gmgn calls to work with async/await"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

# Global client instance (reused across calls)
_gmgn_client = None

def get_gmgn_client():
    """Get or create global gmgn client instance"""
    global _gmgn_client
    if _gmgn_client is None:
        _gmgn_client = gmgn()
    return _gmgn_client

# ============================================================================
# Legacy Code - Will be removed after migration
# ============================================================================

GMGN_BASE_URL="https://gmgn.ai/defi/quotation/v1"

quote_params = {
    "device_id": "dd94f200-d3fc-46fb-8ccb-194706af0789",
    "client_id": "gmgn_web_2025.0207.224528",
    "from_app": "gmgn",
    "app_ver": "2025.0207.224528",
    "tz_name": "America/Chicago",
    "tz_offset": "-21600",
    "app_lang": "en",
    "limit": "20",
    "cost": "20",
    "order_by": "amount_percentage",
    "direction": "desc",
    "size": "300",
}

# Updated headers to better mimic real browser requests
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://gmgn.ai/",
    "Origin": "https://gmgn.ai",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Ch-Ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

# Global session for connection pooling
_session: Optional[aiohttp.ClientSession] = None

async def get_session() -> aiohttp.ClientSession:
    """Get or create a shared aiohttp session with connection pooling"""
    global _session
    if _session is None or _session.closed:
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5, ttl_dns_cache=300)
        _session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=headers
        )
    return _session

async def close_session():
    """Close the global session"""
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None

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
            logger.warning(f"No holders data for token: {token}")
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
        
        logger.info(f"✅ Top holders analyzed for {token[:8]}... ({len(df)} holders)")
        return result
        
    except Exception as e:
        logger.error(f"Error getting top holders via wrapper: {e}")
        return None


async def get_token_profile(token: str) -> Optional[Dict[str, Any]]:
    """Get token profile using gmgnai-wrapper - COMPLETE with getTokenInfo()"""
    try:
        client = get_gmgn_client()
        
        # Use the updated getTokenInfo() endpoint - has EVERYTHING!
        @async_wrap
        def fetch_info():
            return client.getTokenInfo(contractAddress=token)
        
        data = await fetch_info()
        
        if not data or not isinstance(data, dict):
            logger.warning(f"No data returned from gmgn wrapper for token: {token}")
            return None
        
        # Extract data from response - ALL fields now available!
        price_data = data.get('price', {})
        dev_data = data.get('dev', {})
        
        # Map to expected format - NOW COMPLETE!
        result = {
            'ca': token,
            'holders': int(data.get('holder_count', 0)),
            'symbol': data.get('symbol', ''),
            'logo': data.get('logo', ''),
            'name': data.get('name', ''),
            'price': float(price_data.get('price', 0.0)) if price_data else 0.0,
            'top_10_holder_rate': float(dev_data.get('top_10_holder_rate', 0.0)) * 100 if dev_data else 0.0,
            'volume_1h': float(price_data.get('volume_1h', 0.0)) if price_data else 0.0,
            'volume_5m': float(price_data.get('volume_5m', 0.0)) if price_data else 0.0,
            'liquidity': float(data.get('liquidity', 0.0)),
        }
        
        logger.info(f"✅ Token profile fetched for {token[:8]}... ({result['symbol']}, {result['name']})")
        return result
        
    except Exception as e:
        logger.error(f"Error getting token profile via wrapper: {e}")
        return None

async def get_token_links(token: str) -> Optional[Dict[str, Any]]:
    """Get token social links using gmgnai-wrapper - COMPLETE with getTokenLinks()"""
    try:
        client = get_gmgn_client()
        
        @async_wrap
        def fetch_links():
            return client.getTokenLinks(contractAddress=token)
        
        data = await fetch_links()
        
        if not data or not isinstance(data, dict):
            logger.warning(f"No links data returned from gmgn wrapper for token: {token}")
            return {
                'twitter': '',
                'website': '',
                'telegram': '',
                'github': '',
                'discord': '',
                'description': '',
                'gmgn': '',
                'geckoterminal': '',
                'facebook': '',
                'instagram': '',
                'linkedin': '',
                'medium': '',
                'reddit': '',
                'tiktok': '',
                'youtube': '',
                'bitbucket': '',
                'verify_status': 0
            }
        
        # Extract ALL available links and metadata
        result = {
            'twitter': data.get('twitter_username', '').strip(),
            'website': data.get('website', '').strip(),
            'telegram': data.get('telegram', '').strip(),
            'github': data.get('github', '').strip(),
            'discord': data.get('discord', '').strip(),
            'description': data.get('description', '').strip(),
            'gmgn': data.get('gmgn', '').strip(),
            'geckoterminal': data.get('geckoterminal', '').strip(),
            'facebook': data.get('facebook', '').strip(),
            'instagram': data.get('instagram', '').strip(),
            'linkedin': data.get('linkedin', '').strip(),
            'medium': data.get('medium', '').strip(),
            'reddit': data.get('reddit', '').strip(),
            'tiktok': data.get('tiktok', '').strip(),
            'youtube': data.get('youtube', '').strip(),
            'bitbucket': data.get('bitbucket', '').strip(),
            'verify_status': int(data.get('verify_status', 0))
        }
        
        logger.info(f"✅ Token links fetched for {token[:8]}... (Twitter: {result['twitter']}, Website: {result['website']})")
        return result
        
    except Exception as e:
        logger.error(f"Error getting token links via wrapper: {e}")
        return None
    
async def get_token_stats(token: str) -> Optional[Dict[str, Any]]:
    """Get token statistics using gmgnai-wrapper - ENHANCED with getTokenStats()"""
    try:
        client = get_gmgn_client()
        
        @async_wrap
        def fetch_stats():
            return client.getTokenStats(contractAddress=token)
        
        data = await fetch_stats()
        
        if not data or not isinstance(data, dict):
            logger.warning(f"No stats data returned from gmgn wrapper for token: {token}")
            return None
        
        # Extract statistics - NOW WITH REAL DATA!
        stats = {
            'holders': int(data.get('holder_count', 0)),
            'bc_owners_percent': float(data.get('bluechip_owner_percentage', 0.0)) * 100,
            'insiders_percent': float(data.get('top_rat_trader_percentage', 0.0)) * 100
        }
        
        logger.info(f"✅ Token stats fetched for {token[:8]}... (BC: {stats['bc_owners_percent']:.2f}%, Insiders: {stats['insiders_percent']:.2f}%)")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting token stats via wrapper: {e}")
        return None

async def get_token_info(token: str) -> Optional[Dict]:
    try:
        # Add delay between gathering to avoid rate limiting
        await asyncio.sleep(0.5)
        
        # Run all requests concurrently
        results = await asyncio.gather(
            get_top_holders(token),
            get_token_links(token),
            get_token_stats(token),
            get_token_profile(token),
            return_exceptions=True
        )
        
        # Check if any request raised an exception
        if any(isinstance(result, Exception) for result in results):
            exceptions = [r for r in results if isinstance(r, Exception)]
            logger.error(f"One or more requests raised exceptions: {exceptions}")
            return None
            
        holders, links, stats, profile = results
        
        # Check which data is available - be more lenient
        missing_parts = []
        if not holders:
            missing_parts.append("holders")
        if not links:
            missing_parts.append("links")
        if not stats:
            missing_parts.append("stats")
        if not profile:
            missing_parts.append("profile")
            
        if missing_parts:
            logger.error(f"GMGN API blocked - Missing token data: {', '.join(missing_parts)}")
            logger.info("This is likely due to Cloudflare protection. Consider using alternative data sources or proxies.")
            return None
            
        return {
            "mint": token,
            "holders": holders,
            "links": links,
            "stats": stats,
            "profile": profile
        }
        
    except Exception as e:
        logger.error(f"Error getting token info: {e}")
        return None
    
async def get_wallet_token_stats(wallet_address: str, token_address: str, period: str = '7d') -> Optional[Dict[str, Any]]:
    """Get wallet stats using gmgnai-wrapper"""
    try:
        client = get_gmgn_client()
        
        # Validate period
        valid_periods = ['1d', '7d', '30d']
        if period not in valid_periods:
            logger.warning(f"Invalid period {period}, using 7d")
            period = '7d'
        
        @async_wrap
        def fetch():
            return client.getWalletInfo(walletAddress=wallet_address, period=period)
        
        data = await fetch()
        
        if not data or not isinstance(data, dict):
            logger.warning(f"No data returned for wallet: {wallet_address}")
            return None
        
        # Map to expected format (some fields may not be available)
        result = {
            'pnl': float(data.get('pnl', 0.0)),
            'realized_pnl': float(data.get('realized_profit', 0.0)),
            'unrealized_pnl': float(data.get('unrealized_profit', 0.0)),
            'total_trades': int(data.get('total_trades', 0)),
            'winrate': float(data.get('winrate', 0.0)),
        }
        
        logger.info(f"✅ Wallet stats fetched for {wallet_address[:8]}...")
        return result
        
    except Exception as e:
        logger.error(f"Error getting wallet stats via wrapper: {e}")
        return None

async def save_token_info(token_info: Dict[str, Any]) -> bool:
    try:
        from database.database import AsyncSessionFactory
        async with AsyncSessionFactory() as session:
            # Add helper function to safely convert values
            def get_native_int(val):
                return int(val.item()) if hasattr(val, 'item') else int(val)
            
            def get_native_float(val):
                return float(val.item()) if hasattr(val, 'item') else float(val)

            update_values = {
                'ca': token_info['profile']['ca'],
                'symbol': token_info['profile']['symbol'],
                'name': token_info['profile']['name'],
                'holders': token_info['profile']['holders'],
                'logo': token_info['profile']['logo'],
                'price': token_info['profile']['price'],
                'top_10_holder_rate': token_info['profile']['top_10_holder_rate'],
                'volume_1h': token_info['profile']['volume_1h'],
                'volume_5m': token_info['profile']['volume_5m'],
                'liquidity': token_info['profile']['liquidity'],
                'twitter': token_info['links']['twitter'],
                'github': token_info['links']['github'],
                'telegram': token_info['links']['telegram'],
                'website': token_info['links']['website'],
                'bc_owners_percent': get_native_float(token_info['stats']['bc_owners_percent']),
                'insiders_percent': get_native_float(token_info['stats']['insiders_percent']),
                'avg_profit_percent': get_native_float(token_info['holders']['avg_profit_percent']),
                'fresh_wallets': get_native_int(token_info['holders']['fresh_wallets']),
                'sold_wallets': get_native_int(token_info['holders']['sold_wallets']),
                'suspicious_wallets': get_native_int(token_info['holders']['suspicious_wallets']),
                'insiders_wallets': get_native_int(token_info['holders']['insiders_wallets']),
                'phishing_wallets': get_native_int(token_info['holders']['phishing_wallets']),
                'profitable_wallets': get_native_int(token_info['holders']['profitable_wallets']),
                'same_address_funded': get_native_int(token_info['holders']['same_address_funded']),
                'created_date': datetime.utcnow()  # Add this line to create timezone-naive UTC datetime
            }

            stmt = insert(Token).values(
                **update_values
            ).on_conflict_do_update(
                index_elements=['ca'],
                set_=update_values
            )

            await session.execute(stmt)
            await session.commit()
            return True
            
    except (IntegrityError, SQLAlchemyError) as e:
        logger.error(f"DB error saving token: {e}")
        await session.rollback()
        return False
    except KeyError as e:
        logger.error(f"Missing field in token info: {e}")
        return False
