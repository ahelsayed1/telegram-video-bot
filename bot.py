import os
import logging
from fastapi import FastAPI
import uvicorn

# إعداد logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إنشاء التطبيق
app = FastAPI()

@app.get("/")
def home():
    return {"status": "Telegram Bot is ready!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/webhook")
async def telegram_webhook():
    return {"status": "received"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    logger.info(f"Starting bot on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
