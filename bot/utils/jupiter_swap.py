from logger.logger import logger
from config.settings import WALLET_PRIVATE_KEY, SOLANA_RPC_NODE, JUP_API
import asyncio
import base58
import base64
import aiohttp
import statistics
import time
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders.compute_budget import set_compute_unit_price

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

async def jupiter_swap(input_mint, output_mint, amount, auto_multiplier, slippage_bps=1000):
    logger.info("Initializing Jupiter swap...")
    wallet_private_key = Keypair.from_bytes(base58.b58decode(WALLET_PRIVATE_KEY))
    wallet_address = wallet_private_key.pubkey()
    logger.info(f"Wallet address: {wallet_address}")

    async with AsyncClient(SOLANA_RPC_NODE) as client:
        logger.info("Getting recent blockhash...")
        recent_blockhash, last_valid_block_height = await get_recent_blockhash(client)
        logger.info(f"Recent blockhash: {recent_blockhash}")
        logger.info(f"Last valid block height: {last_valid_block_height}")

        # logger.info("Getting recent prioritization fees...")
        # try:
        #     prioritization_fee = await get_recent_prioritization_fees(client, input_mint)
        #     prioritization_fee *= auto_multiplier
        #     logger.info(f"Prioritization fee: {prioritization_fee}")
        # except Exception as e:
        #     logger.error(f"Error getting prioritization fees: {str(e)}")
        #     return 0

    # logger.info(f"Total amount (including prioritization fee): {total_amount}")

    logger.info("Getting quote from Jupiter...")
    quote_url = f"{JUP_API}/quote"
    quote_params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": str(amount),
        "slippageBps": str(slippage_bps),
        "onlyDirectRoutes": "true",
        "maxAccounts": str(64),
        "asLegacyTransaction": "true"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                quote_url,
                params=quote_params,
                timeout=10
            ) as response:
                if response.status == 422:
                    error_data = await response.json()
                    logger.error(f"Jupiter quote API validation error: {error_data}")
                    return None
                response.raise_for_status()
                quote_response = await response.json()
                logger.info(f"Quote response: {quote_response}")
    except aiohttp.ClientError as e:
        logger.error(f"Error getting quote from Jupiter: {e}")
        return None

    logger.info("Getting swap data from Jupiter...")
    swap_url = f"{JUP_API}/swap"
    swap_data = {
        "quoteResponse": quote_response,
        "userPublicKey": str(wallet_address),
        "wrapAndUnwrapSol": True,
        "dynamicComputeUnitLimit": False,
        "prioritizationFeeLamports": "auto",
        "asLegacyTransaction": True
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                swap_url,
                json=swap_data,
                headers={"Content-Type": "application/json"},
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

    logger.info("Creating and signing transaction...")
    async with AsyncClient(SOLANA_RPC_NODE) as client:
        try:
            swap_transaction = swap_response['swapTransaction']
            logger.info(f"Swap transaction length: {len(swap_transaction)}")
            logger.info(f"Swap transaction type: {type(swap_transaction)}")
            
            transaction_bytes = base64.b64decode(swap_transaction)
            logger.info(f"Decoded transaction length: {len(transaction_bytes)}")
            
            unsigned_tx = VersionedTransaction.from_bytes(transaction_bytes)
            logger.info(f"Deserialized transaction: {unsigned_tx}")

            # Add ComputeBudget instruction to do the prioritization fee as implemented in solders
            # compute_budget_ix = set_compute_unit_price(int(prioritization_fee))
            # unsigned_tx.message.instructions.insert(0, compute_budget_ix)
            
            signed_tx = VersionedTransaction(unsigned_tx.message, [wallet_private_key])
            
            logger.info(f"Final transaction to be sent: {signed_tx}")
            
            logger.info("Sending transaction...")
            result = await client.send_transaction(signed_tx)
            logger.info("Transaction sent.")
            tx_signature = result.value
            tx_details = await client.get_transaction(tx_signature)
            logger.info(f"Confirmed transaction details: {tx_details}")
            return result
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
            logger.error(f"Error checking transaction status: {e}")
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