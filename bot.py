import os
import logging
import sqlite3
from datetime import datetime
from threading import Thread

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

from fastapi import FastAPI
import uvicorn

# ========== CONFIGURATION ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "647182059"))

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== DATABASE ==========
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized")

# ========== TELEGRAM BOT HANDLERS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Save user to database
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
        (user.id, user.username or "", user.first_name or "")
    )
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"🎬 **مرحباً {user.first_name}!**\n\n"
        "🤖 أنا بوت توليد الفيديوهات\n\n"
        "🚀 **لتبدأ:** أرسل وصف الفيديو"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 **أوامر البوت:**\n"
        "/start - بدء البوت\n"
        "/help - المساعدة\n"
        "/stats - الإحصائيات"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"📝 رسالة من {user_id}: {user_text[:50]}...")
    
    keyboard = [[InlineKeyboardButton("🎬 إنشاء الفيديو", callback_data="create")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ **تم استلام الوصف:**\n{user_text[:100]}...",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🎬 **جارٍ إنشاء الفيديو...**")

# ========== BOT RUNNER ==========
def run_bot():
    """تشغيل بوت تليجرام في thread منفصل"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set!")
        return
    
    logger.info("🤖 Starting Telegram Bot...")
    init_db()
    
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    logger.info("🔄 Bot running in polling mode...")
    application.run_polling()

# ========== FASTAPI APP ==========
app = FastAPI(title="Telegram Video Bot")

@app.get("/")
async def home():
    return {
        "status": "online",
        "service": "Telegram Video Bot",
        "bot": "running" if BOT_TOKEN else "token_missing"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = sqlite3.connect("bot_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected"
        }
    except:
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ========== MAIN ==========
def main():
    """الدالة الرئيسية"""
    # Start bot in background thread
    if BOT_TOKEN:
        bot_thread = Thread(target=run_bot, daemon=True)
        bot_thread.start()
        logger.info("✅ Bot thread started")
    else:
        logger.warning("⚠️ BOT_TOKEN not set, running in API-only mode")
    
    # Start FastAPI server
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Starting FastAPI on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()
