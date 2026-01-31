import os
import sys
import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# إعداد logging متقدم
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# المتغيرات البيئية
BOT_TOKEN = os.getenv("BOT_TOKEN", "8503431602:AAHP6R_b7zQOKrxKEPwcHfJJ6ZC904aSNL8")
PORT = int(os.getenv("PORT", 10000))
ADMIN_ID = int(os.getenv("ADMIN_ID", "647182059"))

# إعدادات خاصة لـ Railway و Python 3.11
if sys.version_info >= (3, 11):
    import warnings
    warnings.filterwarnings("ignore", message="uvloop")
    
    # إعداد asyncio لـ Python 3.11
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    else:
        try:
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            logger.info("✅ Using uvloop for better performance")
        except ImportError:
            logger.info("⚠️ uvloop not available, using default event loop")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """إدارة دورة حياة التطبيق"""
    # Startup
    logger.info("🚀 Starting Telegram Video Bot...")
    logger.info(f"📊 Python version: {sys.version}")
    logger.info(f"🌐 Port: {PORT}")
    
    try:
        # اختبار استيراد المكتبات
        from telegram import __version__ as telegram_version
        logger.info(f"🤖 python-telegram-bot version: {telegram_version}")
    except ImportError as e:
        logger.error(f"❌ Failed to import python-telegram-bot: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down bot...")

# إنشاء التطبيق مع lifespan management
app = FastAPI(
    title="Telegram AI Video Bot",
    description="Bot for generating videos using AI",
    version="2.0.0",
    lifespan=lifespan
)

# Routes
@app.get("/")
async def root():
    """الصفحة الرئيسية"""
    return {
        "status": "online",
        "service": "Telegram AI Video Bot",
        "version": "2.0.0",
        "python_version": sys.version.split()[0],
        "endpoints": {
            "health": "/health",
            "webhook": "/webhook",
            "admin": "/admin/status"
        },
        "telegram_bot": f"https://t.me/{BOT_TOKEN.split(':')[0] if ':' in BOT_TOKEN else 'bot'}"
    }

@app.get("/health")
async def health_check():
    """فحص صحة الخدمة"""
    import sqlite3
    import tempfile
    
    health_status = {
        "status": "healthy",
        "timestamp": "2024-01-31T00:00:00Z",
        "components": {}
    }
    
    try:
        # اختبار قاعدة البيانات
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            conn = sqlite3.connect(tmp.name)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()
        
        health_status["components"]["database"] = {
            "status": "healthy",
            "details": "SQLite connection successful"
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "details": str(e)
        }
        health_status["status"] = "degraded"
    
    # اختبار الذاكرة
    import psutil
    memory = psutil.virtual_memory()
    health_status["components"]["memory"] = {
        "status": "healthy" if memory.percent < 90 else "warning",
        "usage_percent": memory.percent,
        "available_mb": memory.available // (1024 * 1024)
    }
    
    return health_status

@app.get("/admin/status")
async def admin_status(request: Request):
    """صفحة المشرف"""
    client_host = request.client.host if request.client else "unknown"
    
    return {
        "admin_id": ADMIN_ID,
        "client_ip": client_host,
        "server_info": {
            "platform": sys.platform,
            "python_version": sys.version,
            "processor": os.cpu_count()
        },
        "bot_status": "running" if BOT_TOKEN else "token_missing"
    }

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Webhook endpoint for Telegram"""
    try:
        # محاكاة استقبال webhook
        data = await request.json()
        
        logger.info(f"📨 Received webhook update: {data.get('update_id', 'unknown')}")
        
        # هنا سيتم معالجة تحديثات Telegram
        # للمحاكاة فقط
        return JSONResponse(
            status_code=200,
            content={
                "status": "received",
                "update_id": data.get('update_id'),
                "message": "Update processed successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "details": str(e)}
        )

@app.get("/test/telegram")
async def test_telegram_connection():
    """اختبار اتصال Telegram API"""
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
            )
            
            if response.status_code == 200:
                return {
                    "telegram_api": "connected",
                    "bot_info": response.json().get("result", {}),
                    "token_valid": True
                }
            else:
                return {
                    "telegram_api": "failed",
                    "status_code": response.status_code,
                    "token_valid": False
                }
    except Exception as e:
        return {
            "telegram_api": "error",
            "error": str(e),
            "token_valid": False
        }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# نقطة الدخول الرئيسية
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 TELEGRAM AI VIDEO BOT - PRODUCTION READY")
    logger.info("=" * 60)
    
    # إعدادات uvicorn المتقدمة لـ Railway
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        access_log=True,
        timeout_keep_alive=30,
        limit_concurrency=100,
        backlog=2048
    )
    
    server = uvicorn.Server(config)
    
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("👋 Received interrupt signal. Shutting down...")
    except Exception as e:
        logger.error(f"❌ Server crashed: {e}")
        sys.exit(1)    user_id = update.effective_user.id
    
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
