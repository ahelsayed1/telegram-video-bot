import logging
import os
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

# FastAPI
from fastapi import FastAPI, Request
import uvicorn

# ========== CONFIGURATION ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "647182059"))
# لا تحدد PORT - Railway سيعطيه تلقائياً
PORT = int(os.getenv("PORT", "8000"))  # Railway يستخدم 8000 أو 8080

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
        "أرسل لي وصف الفيديو الذي تريده\n\n"
        "📋 **الأوامر:**\n"
        "/help - للمساعدة\n"
        "/stats - إحصائياتك\n"
        "/admin - لوحة التحكم (للمشرف)"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 **دليل استخدام البوت:**\n\n"
        "🔹 **لإنشاء فيديو:**\n"
        "1. أرسل وصف الفيديو (مثال: 'فيديو دعائي لمطعم')\n"
        "2. انتظر معالجة الطلب\n"
        "3. استلم الفيديو الجاهز\n\n"
        "🔹 **الأوامر المتاحة:**\n"
        "/start - بدء البوت\n"
        "/help - هذه الرسالة\n"
        "/stats - إحصائياتك\n"
        "/admin - لوحة التحكم (للمشرف)\n\n"
        "🔹 **نصائح للوصف:**\n"
        "• كن واضحاً ووصفياً\n"
        "• حدد المدة المطلوبة\n"
        "• اذكر الألوان أو النمط\n\n"
        "💬 **للاقتراحات والدعم:** @ahelsayed1"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"📝 رسالة من {user_id}: {user_text[:50]}...")
    
    # Save to database
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    
    # Save user if not exists
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
        (user_id, update.effective_user.username or "", update.effective_user.first_name or "")
    )
    
    # Save video request
    cursor.execute(
        "INSERT INTO videos (user_id, description) VALUES (?, ?)",
        (user_id, user_text[:500])
    )
    
    conn.commit()
    conn.close()
    
    # Create interactive keyboard
    keyboard = [
        [
            InlineKeyboardButton("🎬 إنشاء الفيديو", callback_data="create"),
            InlineKeyboardButton("✏️ تعديل الوصف", callback_data="edit")
        ],
        [
            InlineKeyboardButton("❓ المساعدة", callback_data="help"),
            InlineKeyboardButton("📊 إحصائيات", callback_data="stats")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    response_text = (
        f"✅ **تم استلام وصف الفيديو!**\n\n"
        f"📝 **الوصف:**\n"
        f"_{user_text[:150]}{'...' if len(user_text) > 150 else ''}_\n\n"
        f"🤖 **ماذا تريد أن أفعل؟**\n"
        f"اختر أحد الخيارات أدناه:"
    )
    
    await update.message.reply_text(
        response_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM videos WHERE user_id = ?", (user_id,))
    video_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT created_at FROM users WHERE user_id = ?", (user_id,))
    join_date = cursor.fetchone()
    
    conn.close()
    
    stats_text = (
        f"📊 **إحصائياتك:**\n\n"
        f"👤 **معلوماتك:**\n"
        f"• المعرف: `{user_id}`\n"
        f"• تاريخ الانضمام: {join_date[0] if join_date else 'جديد'}\n\n"
        f"🎬 **الفيديوهات:**\n"
        f"• طلباتك: {video_count}\n"
        f"• المستخدمين الكلي: {total_users}\n\n"
        f"⭐ **مستواك:** {min(video_count // 3 + 1, 10)}/10"
    )
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ **غير مصرح لك.** هذه اللوحة للمشرف فقط.")
        return
    
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM videos")
    total_videos = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE date(created_at) = date('now')")
    today_users = cursor.fetchone()[0]
    
    conn.close()
    
    admin_text = (
        f"👑 **لوحة تحكم المشرف**\n\n"
        f"📊 **إحصائيات النظام:**\n"
        f"• المستخدمين الكلي: {total_users}\n"
        f"• الفيديوهات الكلية: {total_videos}\n"
        f"• مستخدمين اليوم: {today_users}\n\n"
        f"⚙️ **حالة الخادم:**\n"
        f"• البوت: ✅ نشط\n"
        f"• قاعدة البيانات: ✅ متصلة\n"
        f"• الصحة: ✅ جيدة"
    )
    
    await update.message.reply_text(admin_text, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    user_id = query.from_user.id
    
    if callback_data == "create":
        await query.edit_message_text(
            "🎬 **جارٍ إنشاء الفيديو...**\n\n"
            "⏳ قد يستغرق هذا بضع ثواني\n"
            "⚡ البوت يعمل على معالجة طلبك\n\n"
            "📊 **مراحل المعالجة:**\n"
            "1. تحليل النص ✅\n"
            "2. توليد المشاهد 🔄\n"
            "3. تركيب الفيديو ⏳"
        )
        
        # Simulate video processing
        await asyncio.sleep(3)
        
        await query.edit_message_text(
            "✅ **تم إنشاء الفيديو بنجاح!**\n\n"
            "📹 **معلومات الفيديو:**\n"
            "• المدة: 30 ثانية\n"
            "• الجودة: 720p HD\n"
            "• الصيغة: MP4\n\n"
            "📥 **للتحميل:**\n"
            "https://example.com/video.mp4\n\n"
            "🔄 **لإنشاء فيديو جديد:**\n"
            "أرسل وصفاً آخر"
        )
        
    elif callback_data == "edit":
        await query.edit_message_text(
            "✏️ **تعديل الوصف:**\n\n"
            "أرسل لي الوصف المعدل للفيديو...\n\n"
            "💡 **نصائح:**\n"
            "• أضف تفاصيل أكثر\n"
            "• حدد الألوان المفضلة\n"
            "• اذكر الموسيقى المناسبة"
        )
        
    elif callback_data == "help":
        await query.edit_message_text(
            "❓ **مساعدة سريعة:**\n\n"
            "📌 **لإنشاء فيديو:**\n"
            "أرسل وصف الفيديو وسأقوم بإنشائه\n\n"
            "📌 **أمثلة:**\n"
            "• 'فيديو دعائي 60 ثانية'\n"
            "• 'شرح برمجة بطريقة بسيطة'\n"
            "• 'مشهد طبيعة مع موسيقى هادئة'\n\n"
            "📞 **الدعم:** @ahelsayed1"
        )
        
    elif callback_data == "stats":
        conn = sqlite3.connect("bot_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM videos WHERE user_id = ?", (user_id,))
        video_count = cursor.fetchone()[0]
        conn.close()
        
        await query.edit_message_text(
            f"📊 **إحصائياتك الشخصية:**\n\n"
            f"👤 المعرف: `{user_id}`\n"
            f"🎬 الفيديوهات المنشأة: {video_count}\n"
            f"⭐ التقييم: {'⭐' * min(video_count, 5)}\n\n"
            f"🚀 **استمر في الإبداع!**"
        )

# ========== FASTAPI APP ==========
app = FastAPI(title="Telegram Video Bot")

@app.get("/")
async def home():
    return {
        "status": "online",
        "service": "Telegram Video Bot",
        "version": "2.0.0",
        "features": [
            "Telegram Bot with polling",
            "SQLite Database",
            "Interactive Keyboards",
            "Admin Dashboard",
            "Railway Optimized"
        ],
        "endpoints": {
            "home": "/",
            "health": "/health",
            "webhook": "/webhook (POST)"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint للـ Railway"""
    try:
        # Test database connection
        conn = sqlite3.connect("bot_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "users": user_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, 500

@app.post("/webhook")
async def webhook_handler(request: Request):
    """Webhook endpoint للـ Telegram"""
    try:
        data = await request.json()
        logger.info(f"📨 Webhook received: {data.get('update_id', 'unknown')}")
        return {"status": "ok", "message": "Webhook received"}
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return {"status": "error", "message": str(e)}, 500

# ========== MAIN FUNCTION ==========
def run_fastapi():
    """تشغيل FastAPI server"""
    logger.info(f"🚀 Starting FastAPI on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")

def run_bot():
    """تشغيل Telegram bot"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set!")
        return
    
    init_db()
    
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    logger.info("🤖 Starting Telegram bot in polling mode...")
    application.run_polling()

def main():
    """الدالة الرئيسية"""
    # بدء FastAPI في thread منفصل
    fastapi_thread = Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    
    # بدء Telegram bot
    run_bot()

if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN environment variable is not set!")
        logger.error("💡 Please set BOT_TOKEN in Railway Variables")
    else:
        main()
