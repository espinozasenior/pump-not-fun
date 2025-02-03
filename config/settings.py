from dotenv import load_dotenv
import os
from solana.rpc.api import Client
from solders.keypair import Keypair #type: ignore

load_dotenv()

# Bot configuration
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING")

# Wallet and swap configurations
WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")
SOLANA_RPC_NODE = os.getenv("SOLANA_RPC_NODE")
SOL_MINT = "So11111111111111111111111111111111111111112"
AUTO_MULTIPLIER = os.getenv("SOLANA_AUTO_MULTIPLIER") # a 10% bump to the median of getRecentPrioritizationFees over last 150 blocks
SLIPPAGE_BPS = os.getenv("SOLANA_SLIPPAGE_BPS") # slippage tolerance 1000 = 10%
SOL_AMOUNT = os.getenv("SOL_AMOUNT_TO_SPEND") # Amount of SOL to swap in lamports
JUP_API = "https://quote-api.jup.ag/v6"
# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Jupiter
client = Client(SOLANA_RPC_NODE)
payer_keypair = Keypair.from_base58_string(WALLET_PRIVATE_KEY)

HOMIES_CHAT_ID = os.getenv("HOMIES_CHAT_ID")
PUMP_FUN_CAS = [-1002439158541]

# Helius configuration
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WALLETS = []