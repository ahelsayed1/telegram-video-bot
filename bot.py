import logging
import os
import sqlite3
from datetime import datetime
import asyncio
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

# FastAPI
from fastapi import FastAPI
import uvicorn

# ========== CONFIGURATION ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "647182059"))
PORT = int(os.getenv("PORT", "8000"))

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global app
app = FastAPI(title="Telegram Video Bot")

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
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
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
        "🤖 أنا بوت توليد الفيديوهات الذكي\n\n"
        "📌 **ما يمكنني فعله:**\n"
        "• توليد فيديو من وصف نصي\n"
        "• تخصيص مدة وجودة الفيديو\n"
        "• تتبع تاريخ طلباتك\n\n"
        "🚀 **لتبدأ:**\n"
        "أرسل لي وصف الفيديو الذي تريده"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 **دليل استخدام البوت:**\n\n"
        "🔹 **لإنشاء فيديو:**\n"
        "1. أرسل وصف الفيديو\n"
        "2. انتظر معالجة الطلب\n"
        "3. استلم الفيديو الجاهز\n\n"
        "🔹 **الأوامر:**\n"
        "/start - بدء البوت\n"
        "/help - المساعدة\n"
        "/stats - إحصائياتك\n"
        "/admin - لوحة التحكم (للمشرف)\n\n"
        "💬 **الدعم:** @ahelsayed1"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"📝 رسالة من {user_id}: {user_text[:50]}...")
    
    # Save to database
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
        (user_id, update.effective_user.username or "", update.effective_user.first_name or "")
    )
    
    cursor.execute(
        "INSERT INTO videos (user_id, description) VALUES (?, ?)",
        (user_id, user_text[:500])
    )
    conn.commit()
    conn.close()
    
    keyboard = [
        [InlineKeyboardButton("🎬 إنشاء الفيديو", callback_data="create")],
        [InlineKeyboardButton("❓ المساعدة", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ **تم استلام وصف الفيديو!**\n\nوصفك: {user_text[:100]}...",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM videos WHERE user_id = ?", (user_id,))
    video_count = cursor.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(
        f"📊 **إحصائياتك:**\n\n"
        f"🎬 الفيديوهات المنشأة: {video_count}\n"
        f"⭐ المستوى: {min(video_count // 3 + 1, 10)}/10"
    )

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

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "create":
        await query.edit_message_text("🎬 **جارٍ إنشاء الفيديو...**\n⏳ يرجى الانتظار")
        await asyncio.sleep(2)
        await query.edit_message_text("✅ **تم إنشاء الفيديو!**\n📥 رابط التحميل: example.com/video.mp4")
    elif query.data == "help":
        await query.edit_message_text("❓ **مساعدة:**\nأرسل وصف الفيديو وسأقوم بإنشائه")

# ========== FASTAPI ROUTES ==========
@app.get("/")
async def home():
    return {
        "status": "online",
        "service": "Telegram Video Bot",
        "version": "2.0",
        "bot": "running" if BOT_TOKEN else "token_missing"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint للـ Railway"""
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
        return {"status": "unhealthy", "error": str(e)}, 500

# ========== BOT RUNNER ==========
def run_bot():
    """تشغيل بوت تليجرام في thread منفصل"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set!")
        return
    
    logger.info("🤖 Starting Telegram Bot...")
    
    # Initialize database
    init_db()
    
    # Create and configure bot
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Run bot with polling
    logger.info("🔄 Bot running in polling mode...")
    application.run_polling()

# ========== MAIN ==========
def main():
    """الدالة الرئيسية - تشغيل FastAPI والبوت"""
    
    # Start bot in a separate thread
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    logger.info(f"🚀 Starting FastAPI server on port {PORT}")
    logger.info(f"🌐 Health check available at: /health")
    logger.info(f"🏠 Home page at: /")
    
    # Start FastAPI server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=PORT,
        log_level="info"
    )

if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.error("❌ Please set BOT_TOKEN environment variable in Railway!")
        logger.error("💡 Go to Railway → Variables → Add BOT_TOKEN")
    else:
        main()    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ **تم استلام وصف الفيديو!**\n\nوصفك: {user_text[:100]}...",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM videos WHERE user_id = ?", (user_id,))
    video_count = cursor.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(
        f"📊 **إحصائياتك:**\n\n"
        f"🎬 الفيديوهات المنشأة: {video_count}\n"
        f"⭐ المستوى: {min(video_count // 3 + 1, 10)}/10"
    )

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

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "create":
        await query.edit_message_text("🎬 **جارٍ إنشاء الفيديو...**\n⏳ يرجى الانتظار")
        await asyncio.sleep(2)
        await query.edit_message_text("✅ **تم إنشاء الفيديو!**\n📥 رابط التحميل: example.com/video.mp4")
    elif query.data == "help":
        await query.edit_message_text("❓ **مساعدة:**\nأرسل وصف الفيديو وسأقوم بإنشائه")

# ========== FASTAPI ROUTES ==========
@app.get("/")
async def home():
    return {"status": "online", "service": "Telegram Video Bot", "version": "2.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint للـ Railway"""
    try:
        conn = sqlite3.connect("bot_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500

@app.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """Webhook للـ Telegram (يمكن استخدامه مستقبلاً)"""
    try:
        data = await request.json()
        logger.info(f"📨 Webhook received")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

# ========== STARTUP EVENT ==========
@app.on_event("startup")
async def startup_event():
    """بدء البوت عند تشغيل FastAPI"""
    global bot_application
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set!")
        return
    
    logger.info("🚀 Starting Telegram Bot...")
    
    # Initialize database
    init_db()
    
    # Create bot application
    bot_application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    bot_application.add_handler(CommandHandler("start", start))
    bot_application.add_handler(CommandHandler("help", help_command))
    bot_application.add_handler(CommandHandler("stats", stats_command))
    bot_application.add_handler(CommandHandler("admin", admin_command))
    bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    bot_application.add_handler(CallbackQueryHandler(button_handler))
    
    # Start bot in background
    bot_application.job_queue.start()
    await bot_application.initialize()
    await bot_application.start()
    
    logger.info("🤖 Bot started successfully!")
    logger.info(f"🌐 FastAPI running on port {PORT}")

@app.on_event("shutdown")
async def shutdown_event():
    """إيقاف البوت عند إغلاق FastAPI"""
    global bot_application
    if bot_application:
        logger.info("🛑 Stopping bot...")
        await bot_application.stop()
        await bot_application.shutdown()

# ========== MAIN ==========
if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.error("❌ Please set BOT_TOKEN environment variable")
    else:
        logger.info(f"🚀 Starting server on port {PORT}")
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=PORT,
            log_level="info"
        )
