import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from fastapi import FastAPI
import uvicorn
from threading import Thread

# ========== CONFIGURATION ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "647182059"))

# إعداد logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== TELEGRAM BOT HANDLERS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /start"""
    user = update.effective_user
    logger.info(f"🎯 Received /start from user: {user.id}")
    
    # إنشاء لوحة مفاتيح
    keyboard = [
        [InlineKeyboardButton("🎬 إنشاء فيديو", callback_data="create")],
        [InlineKeyboardButton("❓ المساعدة", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # إرسال الرسالة
    await update.message.reply_text(
        f"🎬 **مرحباً {user.first_name}!**\n\n"
        "أنا بوت إنشاء الفيديوهات الذكي.\n"
        "أرسل وصف الفيديو وسأقوم بإنشائه.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    logger.info(f"✅ Sent response to /start for user: {user.id}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /help"""
    logger.info(f"📚 Received /help from user: {update.effective_user.id}")
    
    await update.message.reply_text(
        "📋 **أوامر البوت:**\n\n"
        "/start - بدء البوت\n"
        "/help - المساعدة\n"
        "/ping - اختبار الاتصال\n\n"
        "🚀 **لإنشاء فيديو:**\n"
        "أرسل وصف الفيديو الذي تريده."
    )
    logger.info(f"✅ Sent /help response")

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /ping"""
    await update.message.reply_text("🏓 **pong!** البوت يعمل بنجاح.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الرسائل النصية"""
    user_text = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"📝 Received text from {user_id}: {user_text[:50]}")
    
    await update.message.reply_text(
        f"✅ **تم استلام طلبك:**\n\n"
        f"📝 {user_text}\n\n"
        f"🚀 البوت يعمل على معالجة طلبك..."
    )
    logger.info(f"✅ Responded to text message from {user_id}")

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أزرار Inline Keyboard"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "create":
        await query.edit_message_text("🎬 **جارٍ إنشاء الفيديو...**\n⏳ يرجى الانتظار قليلاً.")
    elif query.data == "help":
        await query.edit_message_text("❓ **مساعدة:**\nأرسل /help لعرض الأوامر المتاحة.")

# ========== BOT SETUP ==========
def setup_bot():
    """إعداد وتشغيل بوت تليجرام"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN is not set!")
        return
    
    logger.info("🤖 Starting Telegram Bot Setup...")
    
    try:
        # إنشاء تطبيق البوت
        application = Application.builder().token(BOT_TOKEN).build()
        
        # إضافة معالجات الأوامر
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("ping", ping_command))
        
        # إضافة معالج الرسائل النصية
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        # إضافة معالج الأزرار
        application.add_handler(CallbackQueryHandler(handle_button))
        
        logger.info("✅ All bot handlers configured")
        logger.info("📋 Registered commands: /start, /help, /ping")
        
        # بدء البوت
        logger.info("🔄 Starting bot polling...")
        application.run_polling(
            drop_pending_updates=True,
            close_loop=False
        )
        
    except Exception as e:
        logger.error(f"❌ Bot setup failed: {e}")
        import time
        time.sleep(5)
        setup_bot()  # إعادة المحاولة

# ========== FASTAPI ==========
app = FastAPI(title="Telegram Bot")

@app.get("/")
async def home():
    return {
        "status": "online",
        "service": "Telegram Video Bot",
        "bot_status": "running" if BOT_TOKEN else "not_configured"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": "2024-01-31T00:00:00Z"}

@app.get("/test")
async def test():
    """نقطة اختبار للتأكد من أن الخادم يعمل"""
    return {
        "message": "Server is working!",
        "bot_token_set": bool(BOT_TOKEN),
        "endpoints": ["/", "/health", "/test"]
    }

# ========== MAIN ==========
def main():
    """الدالة الرئيسية"""
    logger.info("=" * 50)
    logger.info("🚀 TELEGRAM BOT - SIMPLE WORKING VERSION")
    logger.info("=" * 50)
    
    # تشغيل البوت في thread منفصل
    if BOT_TOKEN:
        logger.info("🤖 Starting bot in separate thread...")
        bot_thread = Thread(target=setup_bot, daemon=True)
        bot_thread.start()
        logger.info("✅ Bot thread started successfully")
    else:
        logger.warning("⚠️ BOT_TOKEN not set, running API only")
    
    # تشغيل FastAPI
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🌐 Starting FastAPI on port {port}")
    logger.info(f"🔗 Health check: http://0.0.0.0:{port}/health")
    logger.info(f"🔗 Test endpoint: http://0.0.0.0:{port}/test")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
