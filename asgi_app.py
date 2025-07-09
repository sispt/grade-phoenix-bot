import os
import logging
from fastapi import FastAPI, Request, Response
from http import HTTPStatus
from telegram import Update
from bot.core import TelegramBot
from config import CONFIG
from contextlib import asynccontextmanager

# Setup logging
from utils.logger import setup_logging, get_logger
setup_logging()
logger = get_logger("asgi_app")

# Initialize the TelegramBot instance
bot_runner = TelegramBot()

# FastAPI app
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 FastAPI startup: Initializing Telegram bot and webhook...")
    await bot_runner.start()
    # Set webhook (if not already set)
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        # Build from Railway or fallback
        railway_url = (
            os.getenv("RAILWAY_STATIC_URL") or 
            os.getenv("RAILWAY_PUBLIC_DOMAIN") or
            os.getenv("RAILWAY_DOMAIN") or
            (f"{os.getenv('RAILWAY_APP_NAME')}.up.railway.app" if os.getenv('RAILWAY_APP_NAME') else None) or
            "your-app-name.up.railway.app"
        )
        webhook_url = f"https://{railway_url}/{CONFIG['TELEGRAM_TOKEN']}"
    await bot_runner.app.bot.set_webhook(url=webhook_url)
    logger.info(f"✅ Webhook set to: {webhook_url}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 FastAPI shutdown: Stopping Telegram bot...")
    await bot_runner.stop()

@app.post(f"/{CONFIG['TELEGRAM_TOKEN']}")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, bot_runner.app.bot)
        await bot_runner.app.process_update(update)
        return Response(status_code=HTTPStatus.OK)
    except Exception as e:
        logger.error(f"❌ Error processing webhook update: {e}", exc_info=True)
        return Response(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"} 