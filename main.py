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
from pyngrok import ngrok
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start ngrok tunnel
    public_url = ngrok.connect(8000, bind_tls=True).public_url
    logger.info(f"Webhook URL: {public_url}/webhooks")
    
    # Initialize webhook
    
    await edit_webhook(
        webhook_id=WEBHOOK_ID,
        new_url=f"{public_url}/webhooks"
    )
    
    yield  # App runs here
    
    # Cleanup
    ngrok.kill()

# Create FastAPI app instance
web_app = FastAPI(lifespan=lifespan)

@web_app.post("/webhooks")
async def handle_webhook(request: Request):
    # Verify secret
    if request.headers.get("Authorization") != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid auth header")
    
    await process_webhook(await request.json(), app)
    
    return {"status": "ok"}

async def main():
    # Initialize database PROPERLY
    from database.database import init_db, engine
    # await init_db()
    await engine.dispose()  # Clean initial connection
    
    # Create Pyrogram client
    global app 
    app = Client(
        "pump-not-fun",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
    )
    async with app:
        # Add web server startup
        config = uvicorn.Config(
            web_app,
            port=8000,
            log_level="info",
            loop="asyncio"
        )
        server = uvicorn.Server(config)
        asyncio.create_task(server.serve())

        # Initialize and start scheduler
        scheduler = AsyncIOScheduler()
        register_tasks(app, scheduler)
        scheduler.start()
        
        # Register handlers after initialization
        # register_handlers(app)
        
        # Keep running
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
