import os
import logging
from fastapi import FastAPI, Request, Response, BackgroundTasks
from http import HTTPStatus
from telegram import Update
from bot.core import TelegramBot
from config import CONFIG
from contextlib import asynccontextmanager
import asyncio

# Setup logging
from utils.logger import setup_logging, get_logger
setup_logging()
logger = get_logger("asgi_app")

# Initialize the TelegramBot instance
bot_runner = TelegramBot()

# FastAPI app
app = FastAPI()

async def scheduled_grade_check():
    while True:
        try:
            logger.info("🔔 Running scheduled grade check (FastAPI background task)...")
            await bot_runner._notify_all_users_grades()
        except Exception as e:
            logger.error(f"❌ Exception in scheduled_grade_check: {e}", exc_info=True)
        interval = int(CONFIG.get('GRADE_CHECK_INTERVAL', 10)) * 60
        await asyncio.sleep(interval)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 FastAPI startup: Initializing Telegram bot and webhook...")
    await bot_runner.start()
    # Wait for app to be initialized (max 5 seconds)
    app_obj = bot_runner.app
    max_wait = 5.0
    waited = 0.0
    while app_obj is None and waited < max_wait:
        await asyncio.sleep(0.2)
        waited += 0.2
        app_obj = bot_runner.app
    if app_obj is None:
        logger.error(f"❌ TelegramBot.app is not initialized after startup (waited {max_wait}s)! Aborting webhook setup.")
        return
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
    current = await app_obj.bot.get_webhook_info()
    if current.url != webhook_url:
        await app_obj.bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook set to: {webhook_url}")
    else:
        logger.info(f"✅ Webhook already set to: {webhook_url}")
    # Start background grade check task
    asyncio.create_task(scheduled_grade_check())

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 FastAPI shutdown: Stopping Telegram bot...")
    await bot_runner.stop()

@app.post(f"/{CONFIG['TELEGRAM_TOKEN']}")
async def telegram_webhook(request: Request):
    app_obj = bot_runner.app
    max_wait = 5.0
    waited = 0.0
    while app_obj is None and waited < max_wait:
        await asyncio.sleep(0.2)
        waited += 0.2
        app_obj = bot_runner.app
    if app_obj is None:
        logger.error(f"❌ TelegramBot.app is not initialized for webhook (waited {max_wait}s)! Aborting update processing.")
        return Response(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    try:
        data = await request.json()
        update = Update.de_json(data, app_obj.bot)
        await app_obj.process_update(update)
        return Response(status_code=HTTPStatus.OK)
    except Exception as e:
        logger.error(f"❌ Error processing webhook update: {e}", exc_info=True)
        return Response(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}