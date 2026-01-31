import os
import sys
import logging
import json
import sqlite3
from datetime import datetime
from typing import Dict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from fastapi import FastAPI, Request, Response
import uvicorn

# ========== إعدادات ==========
BOT_TOKEN = os.getenv("BOT_TOKEN", "8503431602:AAHP6R_b7zQOKrxKEPwcHfJJ6ZC904aSNL8")
ADMIN_ID = int(os.getenv("ADMIN_ID", "647182059"))
PORT = int(os.getenv("PORT", "10000"))
DB_NAME = "bot_data.db"

# إعداد logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== FastAPI App ==========
app = FastAPI(title="Telegram Video Bot")

# ========== قاعدة البيانات ==========
def init_db():
    """تهيئة قاعدة البيانات"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            description TEXT,
            duration INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized")

# ========== معالجات Telegram ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /start"""
    user = update.effective_user
    
    # حفظ المستخدم في قاعدة البيانات
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
        (user.id, user.username or "")
    )
    conn.commit()
    conn.close()
    
    welcome_text = (
        "🎬 **مرحباً بك في بوت توليد الفيديو بالذكاء الاصطناعي!**\n\n"
        "🤖 **كيفية الاستخدام:**\n"
        "1. أرسل وصفاً للفيديو الذي تريده\n"
        "2. سأقوم بتحليله وتحسينه\n"
        "3. ثم أنشئ لك الفيديو\n\n"
        "🚀 **ابدأ الآن بإرسال وصف للفيديو!**\n\n"
        "📊 **أوامر البوت:**\n"
        "/start - بدء البوت\n"
        "/help - المساعدة\n"
        "/stats - إحصائياتك\n"
        "/admin - لوحة التحكم (للمشرف)"
    )
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /help"""
    help_text = (
        "📋 **أوامر البوت:**\n\n"
        "🎬 **لإنشاء فيديو:**\n"
        "• أرسل وصف الفيديو مباشرة\n"
        "• مثال: 'فيديو تعريفي عن الذكاء الاصطناعي'\n\n"
        "⚙️ **الأوامر:**\n"
        "/start - بدء البوت\n"
        "/help - هذه الرسالة\n"
        "/stats - إحصائياتك\n"
        "/admin - لوحة التحكم (للمشرف فقط)\n\n"
        "📞 **للتواصل والدعم:**\n"
        "@ahelsayed1"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /stats"""
    user_id = update.effective_user.id
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # عدد المستخدمين الكلي
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    # عدد فيديوهات المستخدم
    cursor.execute("SELECT COUNT(*) FROM videos WHERE user_id=?", (user_id,))
    user_videos = cursor.fetchone()[0]
    
    conn.close()
    
    stats_text = (
        f"📊 **إحصائيات البوت:**\n\n"
        f"👤 **معلوماتك:**\n"
        f"• المعرف: {user_id}\n"
        f"• الفيديوهات المنشأة: {user_videos}\n\n"
        f"🌐 **عام:**\n"
        f"• إجمالي المستخدمين: {total_users}\n"
        f"• حالة البوت: ✅ نشط\n"
        f"• المنصة: Railway 🚄"
    )
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /admin"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ **غير مصرح لك.** هذه اللوحة للمشرف فقط.")
        return
    
    conn = sqlite3.connect(DB_NAME)
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
        f"📊 **الإحصائيات:**\n"
        f"• المستخدمين الكلي: {total_users}\n"
        f"• الفيديوهات الكلية: {total_videos}\n"
        f"• مستخدمين اليوم: {today_users}\n\n"
        f"⚙️ **إعدادات النظام:**\n"
        f"• البوت: ✅ نشط\n"
        f"• Webhook: ✅ مفعل\n"
        f"• الذاكرة: ⚡ جيدة\n\n"
        f"🔧 **الأوامر:**\n"
        "/broadcast - إرسال إشعار للجميع\n"
        "/users - قائمة المستخدمين"
    )
    
    await update.message.reply_text(admin_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية"""
    user_text = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"📝 رسالة من {user_id}: {user_text[:50]}...")
    
    # حفظ الفيديو في قاعدة البيانات (محاكاة)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO videos (user_id, description) VALUES (?, ?)",
        (user_id, user_text[:500])
    )
    conn.commit()
    conn.close()
    
    # إنشاء لوحة مفاتيح تفاعلية
    keyboard = [
        [
            InlineKeyboardButton("🎬 إنشاء الفيديو", callback_data="create_video"),
            InlineKeyboardButton("✏️ تعديل الوصف", callback_data="edit_description")
        ],
        [
            InlineKeyboardButton("❓ المساعدة", callback_data="help"),
            InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    response_text = (
        f"✅ **تم استلام وصف الفيديو!**\n\n"
        f"📝 **الوصف:**\n"
        f"{user_text[:200]}{'...' if len(user_text) > 200 else ''}\n\n"
        f"🤖 **ماذا تريد أن تفعل؟**\n"
        f"يمكنني إنشاء فيديو بناءً على هذا الوصف"
    )
    
    await update.message.reply_text(
        response_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أزرار Inline Keyboard"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    user_id = query.from_user.id
    
    if callback_data == "create_video":
        await query.edit_message_text(
            "🎬 **جارٍ إنشاء الفيديو...**\n\n"
            "⏳ قد يستغرق هذا بضع ثواني\n"
            "⚡ البوت يعمل على معالجة طلبك"
        )
        
        # محاكاة إنشاء الفيديو
        await query.edit_message_text(
            "✅ **تم إنشاء الفيديو بنجاح!**\n\n"
            "📹 **معلومات الفيديو:**\n"
            "• المدة: 30 ثانية\n"
            "• الجودة: 720p\n"
            "• الصيغة: MP4\n\n"
            "📥 **التحميل:**\n"
            "يمكنك تنزيل الفيديو من الرابط:\n"
            "https://example.com/video.mp4\n\n"
            "🔄 **لإنشاء فيديو جديد:**\n"
            "أرسل وصفاً آخر"
        )
        
    elif callback_data == "edit_description":
        await query.edit_message_text(
            "✏️ **تعديل الوصف:**\n\n"
            "أرسل لي الوصف المعدل للفيديو..."
        )
        
    elif callback_data == "help":
        await query.edit_message_text(
            "❓ **مساعدة:**\n\n"
            "📌 **لإنشاء فيديو:**\n"
            "1. أرسل وصف الفيديو\n"
            "2. اضغط على 'إنشاء الفيديو'\n"
            "3. انتظر حتى ينتهي البوت\n"
            "4. حمّل الفيديو\n\n"
            "⚡ **نصائح:**\n"
            "• كن واضحاً في الوصف\n"
            "• استخدم جمل قصيرة\n"
            "• حدد الجمهور المستهدف\n\n"
            "📞 **الدعم:** @ahelsayed1"
        )
        
    elif callback_data == "stats":
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM videos WHERE user_id=?", (user_id,))
        video_count = cursor.fetchone()[0]
        conn.close()
        
        await query.edit_message_text(
            f"📊 **إحصائياتك:**\n\n"
            f"👤 المعرف: {user_id}\n"
            f"🎬 الفيديوهات المنشأة: {video_count}\n"
            f"⭐ التقييم: ⭐⭐⭐⭐☆\n\n"
            f"🚀 **استمر في الإبداع!**"
        )

# ========== إعداد Telegram Bot ==========
def setup_telegram_bot():
    """إعداد وتكوين بوت التليجرام"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("admin", admin_panel))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    return application

# ========== FastAPI Routes ==========
@app.get("/")
async def home():
    """الصفحة الرئيسية"""
    return {
        "status": "online",
        "service": "Telegram AI Video Bot",
        "platform": "Railway",
        "endpoints": {
            "home": "/",
            "health": "/health",
            "webhook": "/webhook"
        }
    }

@app.get("/health")
async def health_check():
    """فحص صحة الخدمة"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    conn.close()
    
    return {
        "status": "healthy",
        "database": "connected",
        "users_count": user_count,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Webhook لتلقي تحديثات Telegram"""
    try:
        json_data = await request.json()
        update = Update.de_json(json_data, telegram_app.bot)
        
        await telegram_app.initialize()
        await telegram_app.process_update(update)
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}, 500

# ========== التشغيل ==========
if __name__ == "__main__":
    # تهيئة قاعدة البيانات
    init_db()
    
    # إعداد بوت التليجرام
    telegram_app = setup_telegram_bot()
    
    logger.info("=" * 50)
    logger.info("🚀 Starting Telegram Video Bot")
    logger.info(f"📊 Admin ID: {ADMIN_ID}")
    logger.info(f"🌐 Port: {PORT}")
    logger.info("=" * 50)
    
    # تشغيل FastAPI
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
