import os
import logging
from fastapi import FastAPI
import uvicorn

# إعداد logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# التطبيق
app = FastAPI(title="Telegram Video Bot")

@app.get("/")
async def home():
    return {
        "status": "online",
        "service": "Telegram Video Bot",
        "message": "Bot is starting up..."
    }

@app.get("/health")
async def health_check():
    """أبسط healthcheck ممكن"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-31T00:00:00Z"
    }

@app.post("/webhook")
async def webhook_handler():
    """Webhook placeholder"""
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
