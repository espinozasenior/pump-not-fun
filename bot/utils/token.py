from logger.logger import logger
from database.database import AsyncSession, Token
from typing import Any, Dict, Optional, TypedDict
import aiohttp
import asyncio
import pandas as pd
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime

class TokenInfo(TypedDict):
    holders: dict
    profile: dict 
    stats: dict

GMGN_BASE_URL="https://gmgn.ai/defi/quotation/v1"
quote_params = {
    "device_id": "dd94f200-d3fc-46fb-8ccb-194706af0789",
    "client_id": "gmgn_web_2025.0126.145122",
    "from_app": "gmgn",
    "app_ver": "2025.0126.145122",
    "tz_name": "America/Chicago",
    "tz_offset": "-21600",
    "app_lang": "en",
    "limit": "20",
    "cost": "20",
    "order_by": "amount_percentage",
    "direction": "desc"
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": "https://gmgn.ai/",
    "Origin": "https://gmgn.ai",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

async def get_top_holders(token: str) -> Optional[Dict[str, Any]]:
    quote_url = f"{GMGN_BASE_URL}/tokens/top_holders/sol/{token}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                quote_url,
                headers=headers,
                params=quote_params,
                timeout=10
            ) as response:
                if response.status == 422:
                    error_data = await response.json()
                    logger.error(f"Jupiter quote API validation error: {error_data}")
                    return None
                response.raise_for_status()
                json_data = await response.json()
                # Assuming the JSON data is stored in a variable called 'data'
                df = pd.DataFrame(json_data['data'])

                # 1. Fresh wallets (is_new = True)
                fresh_wallets = df['is_new'].sum()

                # 2. Wallets that did sells (sell_tx_count_cur > 0)
                sold_wallets = (df['sell_tx_count_cur'] > 0).sum()

                # 3. Suspicious wallets (is_suspicious = True)
                suspicious_wallets = df['is_suspicious'].sum()

                # Count Insiders (wallets with "rat_trader" in maker_token_tags)
                insiders_count = df['maker_token_tags'].apply(lambda tags: 'rat_trader' in tags if isinstance(tags, list) else False).sum()

                # Count Phishing (wallets with "transfer_in" in maker_token_tags)
                phishing_count = df['maker_token_tags'].apply(lambda tags: 'transfer_in' in tags if isinstance(tags, list) else False).sum()

                # 4. Wallets in profit (profit > 0)
                profitable_wallets = (df['profit'] > 0).sum()

                # 5. Average profit percentage (for wallets with cost_cur > 0)
                mask = df['cost_cur'] > 0
                profit_percent = (df[mask]['profit'] / df[mask]['cost_cur']).mean() * 100

                # 6. Funded from same wallet address
                from_address_counts = df['native_transfer'].apply(lambda x: x['from_address']).value_counts()
                same_address_funded = from_address_counts[from_address_counts > 1].sum()

                # Filter addresses that appear more than once
                common_addresses = from_address_counts[from_address_counts > 1]

                # Print results
                print(f"1. Fresh wallets: {int(fresh_wallets)}")
                print(f"2. Wallets that did sells: {sold_wallets}")
                print(f"3. Suspicious wallets: {suspicious_wallets}")
                print(f"4. Number of Insiders (rat_trader): {insiders_count}")
                print(f"5. Number of Phishing (transfer_in): {phishing_count}")
                print(f"6. Wallets in profit: {profitable_wallets}")
                print(f"7. Average profit percent: {profit_percent:.2f}%")
                print(f"8. Funded from same address: {same_address_funded}")
                print(f"9. Wallet addresses that funded multiple wallets: {common_addresses}")

                return {
                    'fresh_wallets': int(fresh_wallets),
                    'sold_wallets': sold_wallets,
                    'suspicious_wallets': suspicious_wallets,
                    'insiders_wallets': insiders_count,
                    'phishing_wallets': phishing_count,
                    'profitable_wallets': profitable_wallets,
                    'avg_profit_percent': profit_percent,
                    'same_address_funded': same_address_funded,
                    'common_addresses': common_addresses.to_dict()
                }
    except aiohttp.ClientError as e:
        logger.error(f"Error getting quote from Jupiter: {e}")
        return None

async def get_token_profile(token: str) -> Optional[Dict[str, Any]]:
    quote_url = f"https://gmgn.ai/api/v1/mutil_window_token_link_rug_vote/sol/{token}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                quote_url,
                headers=headers,
                params=quote_params,
                timeout=10
            ) as response:
                if response.status == 422:
                    error_data = await response.json()
                    logger.error(f"Jupiter quote API validation error: {error_data}")
                    return None
                response.raise_for_status()
                json_data = await response.json()
                # Assuming the JSON data is stored in a variable called 'data'
                # Extract the 'link' object
                link_data = json_data['data']['link']

                # # Validate if fields exist and are non-empty
                # has_twitter = bool(link_data.get('twitter_username', '').strip())
                # has_website = bool(link_data.get('website', '').strip())
                # has_telegram = bool(link_data.get('telegram', '').strip())
                # has_github = bool(link_data.get('github', '').strip())

                return {
                    'ca': token,
                    'twitter': link_data.get('twitter_username', '').strip(),
                    'website': link_data.get('website', '').strip(),
                    'telegram': link_data.get('telegram', '').strip(),
                    'github': link_data.get('github', '').strip()
                }
    except aiohttp.ClientError as e:
        logger.error(f"Error getting quote from Jupiter: {e}")
        return None
    
async def get_token_stats(token: str) -> Optional[Dict[str, Any]]:
    quote_url = f"https://gmgn.ai/api/v1/token_stat/sol/{token}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                quote_url,
                headers=headers,
                params=quote_params,
                timeout=10
            ) as response:
                if response.status == 422:
                    error_data = await response.json()
                    logger.error(f"Jupiter quote API validation error: {error_data}")
                    return None
                response.raise_for_status()
                json_data = await response.json()
                # Assuming the JSON data is stored in a variable called 'data'
                stats = json_data['data']
                print(f"Holders: {int(stats.get('holder_count', ''))}")
                print(f"Bluechip Owner %: {float(stats.get('bluechip_owner_percentage', '').strip()) * 100}")
                print(f"Insiders %: {float(stats.get('top_rat_trader_percentage', '').strip()) * 100}")
                return {
                    'holders': int(stats.get('holder_count', '')),
                    'bc_owners_percent': float(stats.get('bluechip_owner_percentage', '').strip()) * 100,
                    'insiders_percent': float(stats.get('top_rat_trader_percentage', '').strip()) * 100
                }
    except aiohttp.ClientError as e:
        logger.error(f"Error getting quote from Jupiter: {e}")
        return None

async def get_token_info(token: str) -> Optional[Dict]:
    try:
        # Run all requests concurrently
        results = await asyncio.gather(
            get_top_holders(token),
            get_token_profile(token),
            get_token_stats(token),
            return_exceptions=True
        )
        
        # Check if any request failed
        if any(isinstance(result, Exception) for result in results):
            logger.error("One or more requests failed")
            return None
            
        holders, profile, stats = results
        
        # Validate required data
        if not all([holders, profile, stats]):
            logger.error("Missing required token data")
            return None
            
        return {
            "holders": holders,
            "profile": profile,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting token info: {e}")
        return None
    
async def save_token_info(token_info: Dict[str, Any]) -> bool:
    try:
        async with AsyncSession() as session:
            # Add helper function to safely convert values
            def get_native_int(val):
                return int(val.item()) if hasattr(val, 'item') else int(val)
            
            def get_native_float(val):
                return float(val.item()) if hasattr(val, 'item') else float(val)

            update_values = {
                'symbol': None,  # Explicitly set to None since we're ignoring symbols
                'twitter': token_info['profile']['twitter'],
                'github': token_info['profile']['github'],
                'telegram': token_info['profile']['telegram'],
                'website': token_info['profile']['website'],
                'holders': token_info['stats']['holders'],
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
                ca=token_info['profile']['ca'],
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
        return False
    except KeyError as e:
        logger.error(f"Missing field in token info: {e}")
        return False
    
