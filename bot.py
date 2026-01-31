import logging
import os
import json
import sqlite3
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "647182059"))

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 **مرحباً ببوت توليد الفيديو!**\n\n"
        "أرسل /help للمساعدة"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 **أوامر البوت:**\n"
        "/start - بدء البوت\n"
        "/help - المساعدة\n"
        "/stats - الإحصائيات\n\n"
        "🚀 لتوليد فيديو، أرسل وصف الفيديو مباشرة."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.effective_user.id
    
    # Save user to database
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
        (user_id, update.effective_user.username or "")
    )
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"📝 **تم استلام النص:**\n{user_text[:100]}...\n\n"
        "🚧 **قيد التطوير:** سيتم توليد الفيديو قريباً!"
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(
        f"📊 **إحصائيات البوت:**\n"
        f"👥 المستخدمين: {user_count}\n"
        f"✅ الحالة: نشط\n"
        f"🌐 الوضع: Webhook"
    )

# FastAPI for Render
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.get("/")
async def home():
    return {"status": "online", "service": "Telegram Video Bot"}

@app.post("/webhook")
async def webhook(request: Request):
    """Handle Telegram webhook"""
    return {"status": "webhook_received"}

def main():
    """Start bot with webhook for Render"""
    init_db()
    
    # Create bot application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Get webhook URL from environment
    webhook_url = os.getenv("RENDER_EXTERNAL_URL", "")
    
    if webhook_url:
        # Production mode with webhook
        import asyncio
        
        async def setup_webhook():
            await application.bot.set_webhook(f"{webhook_url}/webhook")
            logger.info(f"Webhook set to: {webhook_url}/webhook")
        
        asyncio.run(setup_webhook())
        
        # Start FastAPI server
        port = int(os.getenv("PORT", "10000"))
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        # Development mode with polling
        logger.info("Starting bot in polling mode...")
        application.run_polling()

if __name__ == "__main__":
    main()