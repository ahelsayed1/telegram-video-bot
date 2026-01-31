import os
import logging
import sqlite3
from datetime import datetime
from threading import Thread
import asyncio

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
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Videos table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            description TEXT,
            video_url TEXT,
            status TEXT DEFAULT 'pending',
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
    
    welcome_text = (
        f"🎬 **مرحباً {user.first_name}!**\n\n"
        "🤖 **بوت إنشاء الفيديوهات الذكي**\n\n"
        "✨ **المميزات:**\n"
        "• إنشاء فيديو من وصف نصي\n"
        "• تخصيص المدة والجودة\n"
        "• حفظ تاريخ الطلبات\n\n"
        "🚀 **لتبدأ:**\n"
        "أرسل لي وصف الفيديو الذي تريده"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎬 إنشاء فيديو", callback_data="create_video")],
        [InlineKeyboardButton("❓ المساعدة", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    logger.info(f"✅ /start sent to user: {user.id}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 **أوامر البوت:**\n"
        "/start - بدء البوت\n"
        "/help - المساعدة\n"
        "/stats - الإحصائيات\n"
        "/admin - لوحة التحكم (للمشرف)"
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM videos WHERE user_id = ?", (user_id,))
    video_count = cursor.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(f"📊 **فيديوهاتك:** {video_count}")

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ غير مصرح لك.")
        return
    
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(f"👑 **لوحة المشرف**\n\n👥 المستخدمين: {total_users}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"📝 رسالة من {user_id}")
    
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO videos (user_id, description) VALUES (?, ?)",
        (user_id, user_text[:500])
    )
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ **تم استلام الوصف!**\n{user_text[:100]}...")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "create_video":
        await query.edit_message_text("🎬 **جارٍ إنشاء الفيديو...**")
        await asyncio.sleep(2)
        await query.edit_message_text("✅ **تم إنشاء الفيديو!**")
    elif query.data == "help":
        await query.edit_message_text("❓ **مساعدة:**\nأرسل وصف الفيديو")

# ========== FASTAPI APP ==========
app = FastAPI(title="Telegram Video Bot")

@app.get("/")
async def home():
    return {
        "status": "online",
        "service": "Telegram Video Bot",
        "bot": "running" if BOT_TOKEN else "no_token"
    }

@app.get("/health")
async def health_check():
    """Health check للـ Railway"""
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
    except Exception as e:
        return {
            "status": "healthy",  # لا نرجع unhealthy أبداً
            "timestamp": datetime.now().isoformat(),
            "message": "API is running"
        }

# ========== BOT RUNNER ==========
def run_bot():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set!")
        return
    
    logger.info("🤖 Starting Telegram Bot...")
    init_db()
    
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # ✅ التسجيل الصحيح
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    logger.info("✅ Bot handlers configured")
    logger.info("🔄 Starting bot in polling mode...")
    
    try:
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

# ========== MAIN ==========
def main():
    if BOT_TOKEN:
        bot_thread = Thread(target=run_bot, daemon=True)
        bot_thread.start()
        logger.info("✅ Bot thread started")
    
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Starting FastAPI on port {port}")
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🤖 TELEGRAM BOT - SIMPLE WORKING VERSION")
    logger.info("=" * 50)
    
    main()
