from config.settings import API_ID, API_HASH, WEBHOOK_SECRET, SESSION_STRING, WEBHOOK_ID, BOT_TOKEN
from bot.handlers import register_handlers
from bot.tasks import register_tasks
from logger.logger import logger
from bot.utils.monitor import edit_webhook, process_webhook
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client
import asyncio
from fastapi import FastAPI, Request, HTTPException
import uvicorn
from contextlib import asynccontextmanager
import os

PORT = 8000 if not os.getenv('RENDER') else int(os.getenv('PORT', '10000'))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Environment detection
    is_production = os.getenv('RENDER')
    
    if is_production:
        domain = os.getenv('RENDER_EXTERNAL_URL')
        webhook_url = f"{domain}/webhooks"
    else:
        # Local development with ngrok
        from pyngrok import ngrok
        tunnel = ngrok.connect(PORT, bind_tls=True)
        domain = tunnel.public_url
        webhook_url = f"{domain}/webhooks"
    
    logger.info(f"Webhook endpoint: {webhook_url}")
    
    # Update Helius webhook
    await edit_webhook(
        webhook_id=WEBHOOK_ID,
        url=webhook_url
    )

    # Initialize and START client first
    global client
    client = Client(
        "pump-not-fun",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
    )
    await client.start()  # <-- ADD THIS LINE
    
    # Start scheduler AFTER client is ready
    scheduler = AsyncIOScheduler()
    register_tasks(client, scheduler)
    scheduler.start()
    
    yield
    
    # Cleanup
    await client.stop()
    scheduler.shutdown()
    if not is_production:
        ngrok.kill()

# Create FastAPI app instance
web_app = FastAPI(lifespan=lifespan)

@web_app.post("/webhooks")
async def handle_webhook(request: Request):
    # Verify secret
    if request.headers.get("Authorization") != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid auth header")
    
    await process_webhook(await request.json(), client)
    
    return {"status": "ok"}

async def main():
    from database.database import engine
    await engine.dispose()  # Clean initial connection

    config = uvicorn.Config(
        web_app,
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        loop="asyncio"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
