from logger.logger import logger
from typing import Any, Dict, Optional
from config.settings import SOLANA_RPC_NODE, JUP_API
import asyncio
import base64
import aiohttp
import statistics
import time
import json
from solana.rpc.async_api import AsyncClient
from solders.message import to_bytes_versioned  # type: ignore
from solders.transaction import VersionedTransaction  # type: ignore
from solana.rpc.commitment import Processed
from solana.rpc.types import TxOpts
from config.settings import payer_keypair

async def get_recent_blockhash(client: AsyncClient):
    response = await client.get_latest_blockhash()
    return response.value.blockhash, response.value.last_valid_block_height

# Get the data on the priority fees over the last 150 blocks.
# Note that it calculates the priority fees median from the returned data.
# And if the majority of fees over the past 150 blocks are 0, you'll get a 0 here as well.
# I found the median approach more reliable and peace of mind over something like getting some
# fluke astronomical fee and using it. This can be easily drain your account.
async def get_recent_prioritization_fees(client: AsyncClient, input_mint: str):
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getRecentPrioritizationFees",
        "params": [[input_mint]]
    }
    await client.is_connected()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(client._provider.endpoint_uri, json=body) as response:
                json_response = await response.json()
                logger.info(f"Prioritization fee response: {json_response}")
                if json_response and "result" in json_response:
                    fees = [fee["prioritizationFee"] for fee in json_response["result"]]
                    return statistics.median(fees)
    except aiohttp.ClientError as e:
        logger.error(f"Error post {client._provider.endpoint_uri}: {str(e)}")
        return 0

async def get_quote(input_mint: str, output_mint: str, amount: int, slippage_bps: int) -> Optional[Dict[str, Any]]:
    quote_url = f"{JUP_API}/quote"
    quote_params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": "100000000",
        "slippageBps": str(slippage_bps),
        "onlyDirectRoutes": "true",
        "maxAccounts": "64",
        "asLegacyTransaction": "true"
    }
    headers = {'Accept': 'application/json'}
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
                return await response.json()
    except aiohttp.ClientError as e:
        logger.error(f"Error getting quote from Jupiter: {e}")
        return None

async def get_swap(wallet_address: str, quote_response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    swap_url = f"{JUP_API}/swap"
    swap_data = json.dumps({
        "quoteResponse": quote_response,
        "userPublicKey": wallet_address,
        "wrapAndUnwrapSol": True,
        "dynamicComputeUnitLimit": False,
        "asLegacyTransaction": True,
        "prioritizationFeeLamports": {
            "priorityLevelWithMaxLamports": {
                "maxLamports": 300000000, # 0.003 sol
                "priorityLevel": "veryHigh"
            }
        }        
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                swap_url,
                data=swap_data,
                headers=headers,
                timeout=10
            ) as response:
                if response.status == 422:
                    error_data = await response.json()
                    logger.error(f"Jupiter swap API validation error: {error_data}")
                    return None
                response.raise_for_status()
                swap_response = await response.json()
                logger.info(f"Swap response: {swap_response}")
                return swap_response                
    except aiohttp.ClientError as e:
        logger.error(f"Error getting swap data from Jupiter: {str(e)}")
        return None

async def jupiter_swap(input_mint, output_mint, amount, auto_multiplier, slippage_bps=1000):
    logger.info("Initializing Jupiter swap...")
    wallet_private_key = payer_keypair
    wallet_address = str(wallet_private_key.pubkey())
    quote_response = await get_quote(input_mint, output_mint, amount, slippage_bps)
    swap_response = await get_swap(wallet_address, quote_response)
    logger.info("Creating and signing transaction...")
    async with AsyncClient(SOLANA_RPC_NODE) as client:
        try:
            unsigned_tx = VersionedTransaction.from_bytes(
                base64.b64decode(swap_response['swapTransaction'])
            )
            signature = payer_keypair.sign_message(to_bytes_versioned(unsigned_tx.message))
            signed_txn = VersionedTransaction.populate(unsigned_tx.message, [signature])
            opts = TxOpts(skip_preflight=True, preflight_commitment=Processed)
            # logger.info("Signing transaction...")
            # signed_tx = VersionedTransaction(unsigned_tx.message, [wallet_private_key])
            # logger.info(f"Final transaction to be sent: {signed_tx}")
            logger.info("Sending transaction...")
            try:
                txn_sig = await client.send_raw_transaction(
                    txn=bytes(signed_txn), opts=opts
                )
                return txn_sig            
            except Exception as e:
                logger.error(f"Failed to send transaction: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Error creating or sending transaction: {str(e)}")
            return None

async def wait_for_confirmation(client, signature, max_timeout=60):
    start_time = time.time()
    while time.time() - start_time < max_timeout:
        try:
            status = await client.get_signature_statuses([signature])
            if status.value[0] is not None:
                return status.value[0].confirmation_status
        except Exception as e:
            logger.warning(f"Checking transaction status failed... {e}")
        await asyncio.sleep(1)
    return None

async def swap(input_mint, output_mint, amount, auto_multiplier = 1.1, slippage_bps = 1000):
    try:
        if auto_multiplier is not float:
            auto_multiplier = float(auto_multiplier)
        if slippage_bps is not int:
            slippage_bps = int(slippage_bps)
        if amount is not int:
            amount = int(amount)
        logger.info("Starting Jupiter swap...")
        logger.info(f"Input mint: {input_mint}")
        logger.info(f"Output mint: {output_mint}")
        logger.info(f"Amount: {amount} lamports")
        # Convert SOL amount to lamports (1 SOL = 10^9 lamports)
        # For example, 50 SOL = 50 * 10^9 lamports
        amount = int(amount * 1e9)  # Simpler decimal handling
        logger.info(f"Amount in lamports: {amount}")
        logger.info(f"Auto multiplier: {auto_multiplier}")

        result = await jupiter_swap(input_mint, output_mint, amount, auto_multiplier, slippage_bps)
        if result:
            tx_signature = result.value
            solscan_url = f"https://solscan.io/tx/{tx_signature}"
            logger.info(f"Transaction signature: {tx_signature}")
            logger.info(f"Solscan link: {solscan_url}")
            logger.info("Waiting for transaction confirmation...")
            async with AsyncClient(SOLANA_RPC_NODE) as client:
                confirmation_status = await wait_for_confirmation(client, tx_signature)
                logger.info(f"Transaction confirmation status: {confirmation_status}")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")