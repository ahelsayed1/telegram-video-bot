import os
import logging
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from services.ai_service import FreeAIService
from services.search_service import WebSearchService

# تحميل المتغيرات البيئية
load_dotenv()

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تهيئة الخدمات المجانية
ai_service = FreeAIService()
search_service = WebSearchService()

# قائمة النكات العربية
ARABIC_JOKES = [
    "لماذا لا يثق العلماء في الذرات؟ لأنها تصنع كل شيء!",
    "ماذا قال الكمبيوتر للعامل؟ أنت بحاجة إلى إعادة تشغيل!",
    "لماذا يخشى الرياضيون من الرقم السلبي؟ لأنه تحت الصفر!",
    "ما هو الحيوان الذي يحب البرمجة؟ الأفعى (Python)!",
    "ماذا قال المبرمج عندما جاع؟ Hello World!",
    "لماذا يستخدم المبرمجون الإضاءة الخافتة؟ لأن الأضواء الساطعة تجذب البق (Bugs)!",
    "ماذا قال المبرمج لصديقه؟ while(true) { beHappy(); }",
    "لماذا توقف المبرمج عن الكتابة؟ لأنه وجد bug في القلم!",
    "ما هو الشيء المشترك بين المبرمج والسباح؟ كلاهما يعمل على الـ pool!",
    "لماذا ذهب المبرمج إلى الطبيب؟ لأنه كان يعاني من loop لا نهائي!"
]

# قائمة الاقتباسات العربية
ARABIC_QUOTES = [
    "التعلم ليس إجباريًا للبقاء، بل هو اختيار للازدهار.",
    "النجاح ليس مفتاح السعادة، بل السعادة مفتاح النجاح.",
    "لا تنتظر الفرصة، اصنعها.",
    "أعظم مجد في الحياة ليس في عدم السقوط، بل في النهوض بعد كل سقوط.",
    "المستقبل يبدأ اليوم، ليس غدًا.",
    "الحلم لا يتحقق بالمعجزات، بل بالعمل والمثابرة.",
    "القراءة هي الغذاء للعقل كما الطعام للجسد.",
    "لا تخف من الفشل، بل خف من عدم المحاولة.",
    "الوقت كالسيف إن لم تقطعه قطعك.",
    "العلم نور والجهل ظلام."
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة ترحيبية"""
    user = update.effective_user
    welcome_message = f"""
🎉 أهلاً وسهلاً {user.first_name}!

🤖 أنا **مساعدك الذكي المجاني**، مدعوم بتقنيات الذكاء الاصطناعي والبحث المجاني.

✨ **ما أستطيع عمله لك:**

🔍 **البحث والمعرفة:**
▫️ `/ask سؤالك` - للإجابة على أسئلتك
▫️ `/search موضوع` - للبحث في الإنترنت
▫️ `/summarize رابط` - لتلخيص المقالات
▫️ `/news موضوع` - لأحدث الأخبار

💬 **الترفيه والتواصل:**
▫️ محادثة مباشرة (اكتب رسالة عادية)
▫️ `/joke` - نكتة مضحكة
▫️ `/quote` - اقتباس ملهم
▫️ `/help` - عرض جميع الأوامر

📚 **مواضيع يمكنني مساعدتك فيها:**
- البرمجة والتقنية
- العلوم والرياضيات
- الثقافة العامة
- الأخبار والتحديثات
- النصائح والإرشادات

⚡ **مميزات خاصة:**
- مجاني 100% ولا يحتاج أي API keys
- يعمل 24/7 على Railway
- يدعم اللغة العربية بشكل كامل
- نتائج بحث حية من مصادر موثوقة

🚀 **جرب هذه الأوامر الآن:**
/ask ما هو الذكاء الاصطناعي؟
/search أخبار التقنية اليوم
/news العلوم
/joke
    """
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض جميع الأوامر"""
    help_text = """
📚 **دليل الأوامر الكامل:**

🎯 **الأوامر الأساسية:**
▫️ `/start` - رسالة الترحيب
▫️ `/help` - هذه الرسالة

🤔 **البحث والمعرفة:**
▫️ `/ask [سؤال]` - سؤال مباشر للذكاء الاصطناعي
▫️ `/search [كلمة]` - بحث في الإنترنت (3 نتائج)
▫️ `/search5 [كلمة]` - بحث في الإنترنت (5 نتائج)
▫️ `/summarize [رابط]` - تلخيص صفحة ويب
▫️ `/news [موضوع]` - آخر الأخبار
▫️ `/wiki [موضوع]` - بحث في ويكيبيديا

😄 **الترفيه:**
▫️ `/joke` - نكتة عشوائية
▫️ `/quote` - اقتباس ملهم
▫️ `/fact` - معلومة عشوائية
▫️ `/riddle` - لغز عشوائي

🛠️ **الأدوات:**
▫️ `/calc [عملية]` - آلة حاسبة
▫️ `/time` - الوقت الحالي
▫️ `/date` - التاريخ اليوم
▫️ `/ping` - اختبار سرعة البوت

💬 **المحادثة:**
▫️ يمكنك محادثتي مباشرة! فقط اكتب رسالة وسأرد عليك.

🔍 **نصائح للبحث:**
- استخدم كلمات دقيقة للحصول على نتائج أفضل
- يمكنك البحث باللغة العربية أو الإنجليزية
- الروابط المباشرة أسهل في التلخيص

❓ **مثال للاستخدام:**
`/ask كيف أتعلم البرمجة؟`
`/search وصفات حلويات`
`/news التكنولوجيا`
    """
    await update.message.reply_text(help_text)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """سؤال مباشر للذكاء الاصطناعي"""
    if not context.args:
        await update.message.reply_text("⚠️ اكتب سؤالك بعد الأمر /ask\nمثال: /ask ما هو الذكاء الاصطناعي؟")
        return
    
    question = " ".join(context.args)
    await update.message.reply_chat_action("typing")
    
    try:
        # محاولة الإجابة من قاعدة المعرفة أولاً
        answer = await ai_service.get_answer(question)
        await update.message.reply_text(answer)
        
        # إذا كانت الإجابة قصيرة، أضف اقتراحاً للبحث
        if len(answer) < 100:
            await update.message.reply_text(
                f"🔍 هل تريد المزيد من المعلومات عن '{question}'؟\n"
                f"جرب: /search {question}"
            )
    except Exception as e:
        logger.error(f"Ask error: {e}")
        await update.message.reply_text("🔍 جاري البحث عن إجابة في الإنترنت...")
        
        try:
            web_result = await search_service.search_web(question, num_results=1)
            if web_result:
                await update.message.reply_text(
                    f"📚 **بناء على بحثي:**\n\n"
                    f"{web_result[0]['snippet'][:500]}\n\n"
                    f"للمزيد: /search {question}"
                )
            else:
                await update.message.reply_text("⚠️ لم أجد إجابة دقيقة، جرب صياغة السؤال بشكل مختلف.")
        except:
            await update.message.reply_text("❌ حدث خطأ، جرب مرة أخرى بعد قليل.")

async def web_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بحث في الإنترنت"""
    if not context.args:
        await update.message.reply_text("🔍 اكتب ما تريد البحث عنه\nمثال: /search وصفات كعك")
        return
    
    query = " ".join(context.args)
    await update.message.reply_chat_action("typing")
    
    try:
        # تحديد عدد النتائج بناءً على الأمر
        num_results = 5 if update.message.text.startswith('/search5') else 3
        
        results = await search_service.search_web(query, num_results=num_results)
        
        if results:
            response = f"🔎 **نتائج البحث عن:** '{query}'\n\n"
            
            for i, result in enumerate(results, 1):
                title = result.get('title', 'بدون عنوان')
                snippet = result.get('snippet', '')
                url = result.get('url', '')
                
                # تقصير العنوان إذا كان طويلاً
                if len(title) > 50:
                    title = title[:50] + "..."
                
                response += f"**{i}. {title}**\n"
                response += f"{snippet}\n"
                if url:
                    response += f"📎 {url}\n"
                response += "\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
        else:
            await update.message.reply_text("⚠️ لم أجد نتائج، جرب كلمات بحث مختلفة.")
            
    except Exception as e:
        logger.error(f"Search error: {e}")
        await update.message.reply_text("❌ حدث خطأ في البحث، جرب مرة أخرى.")

async def summarize_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تلخيص صفحة ويب"""
    if not context.args:
        await update.message.reply_text("📄 أرسل الرابط بعد /summarize\nمثال: /summarize https://example.com/article")
        return
    
    url = context.args[0]
    
    # التحقق من أن الرابط يبدأ بـ http
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    await update.message.reply_chat_action("typing")
    
    try:
        summary = await search_service.summarize_webpage(url)
        
        if len(summary) > 3000:
            # إذا كان الملخص طويلاً، نقسمه
            part1 = summary[:3000]
            part2 = summary[3000:]
            
            await update.message.reply_text(f"📄 **ملخص المقال:**\n\n{part1}")
            await update.message.reply_text(part2)
        else:
            await update.message.reply_text(f"📄 **ملخص المقال:**\n\n{summary}")
            
    except Exception as e:
        logger.error(f"Summarize error: {e}")
        await update.message.reply_text(f"❌ لا يمكن تلخيص هذا الرابط:\n{str(e)}")

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جلب آخر الأخبار"""
    topic = " ".join(context.args) if context.args else "technology"
    
    # ترجمة المواضيع العربية
    topic_translations = {
        "تقنية": "technology",
        "تكنولوجيا": "technology",
        "علوم": "science",
        "رياضة": "sports",
        "اقتصاد": "business",
        "أعمال": "business",
        "صحة": "health",
        "فن": "entertainment",
        "ترفيه": "entertainment"
    }
    
    english_topic = topic_translations.get(topic.lower(), topic)
    
    await update.message.reply_chat_action("typing")
    
    try:
        news = await search_service.get_news(english_topic)
        
        if news and len(news) > 0:
            response = f"📰 **آخر أخبار {topic}:**\n\n"
            
            for i, item in enumerate(news[:5], 1):
                title = item.get('title', '')
                snippet = item.get('snippet', '')
                source = item.get('source', '')
                
                response += f"**{i}. {title}**\n"
                if snippet:
                    response += f"{snippet}\n"
                if source:
                    response += f"📰 {source}\n"
                response += "\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"⚠️ لم أجد أخبار عن '{topic}' حالياً.\nجرب: /news تقنية")
            
    except Exception as e:
        logger.error(f"News error: {e}")
        await update.message.reply_text("❌ لا يمكن جلب الأخبار حالياً.")

async def wikipedia_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بحث في ويكيبيديا"""
    if not context.args:
        await update.message.reply_text("📚 اكتب موضوع البحث\nمثال: /wiki الذكاء الاصطناعي")
        return
    
    query = " ".join(context.args)
    await update.message.reply_chat_action("typing")
    
    try:
        wiki_result = await search_service.wikipedia_search(query)
        await update.message.reply_text(wiki_result, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Wiki error: {e}")
        await update.message.reply_text(f"⚠️ لم أجد معلومات عن '{query}' في ويكيبيديا.")

async def tell_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نكتة عشوائية"""
    joke = random.choice(ARABIC_JOKES)
    await update.message.reply_text(f"😂 {joke}\n\n💡 جرب /quote لاقتباس ملهم")

async def inspirational_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اقتباس ملهم"""
    quote = random.choice(ARABIC_QUOTES)
    await update.message.reply_text(f"💫 {quote}\n\n😄 جرب /joke لنكتة مضحكة")

async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معلومة عشوائية"""
    facts = [
        "أول كمبيوتر شخصي ظهر في السبعينات وكان يزن أكثر من 50 كجم!",
        "الإنترنت يحتاج إلى 2% من الطاقة العالمية لتشغيله.",
        "هناك أكثر من 700 لغة برمجة في العالم.",
        "أول رسالة إلكترونية أرسلت عام 1971 كانت تحتوي على النص 'QWERTYUIOP'.",
        "المبرمجون يكتبون في المتوسط 15-20 سطر كود يومياً.",
        "أول موقع ويب أنشأه تيم برنرز لي في عام 1991 ولا يزال يعمل.",
        "90% من البيانات العالمية تم إنشاؤها في العامين الماضيين فقط.",
        "هناك أكثر من 1.8 مليار موقع ويب على الإنترنت.",
        "لغة Python سميت على اسم مسرحية بريطانية وليس الثعبان.",
        "أول فيروس كمبيوتر ظهر عام 1971 وكان اسمه 'Creeper'."
    ]
    
    fact = random.choice(facts)
    await update.message.reply_text(f"📚 **معلومة تقنية:**\n\n{fact}")

async def random_riddle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغز عشوائي"""
    riddles = [
        ("ما هو الشيء الذي كلما أخذت منه كبر؟", "الحفرة"),
        ("ما هو الشيء الذي له عين واحدة ولا يرى؟", "الإبرة"),
        ("ما هو الشيء الذي يمشي بلا رجلين ويبكي بلا عينين؟", "السحاب"),
        ("ما هو الشيء الذي يكون أخضر في الأرض وأسود في السوق وأحمر في البيت؟", "الشاي"),
        ("ما هو الشيء الذي يحمل طعامه فوق رأسه؟", "القلم")
    ]
    
    riddle, answer = random.choice(riddles)
    
    await update.message.reply_text(f"❓ **لغز:** {riddle}")
    
    # إجابة بعد 5 ثوانٍ
    import asyncio
    await asyncio.sleep(5)
    await update.message.reply_text(f"💡 **الإجابة:** {answer}")

async def calculator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آلة حاسبة بسيطة"""
    if not context.args:
        await update.message.reply_text("🧮 استخدم: /calc [عملية]\nمثال: /calc 5 + 3\n/calc 10 * 2")
        return
    
    expression = " ".join(context.args)
    
    try:
        # الأمان: السماح فقط بالعمليات الحسابية البسيطة
        allowed_chars = set("0123456789+-*/.() ")
        
        if any(char not in allowed_chars for char in expression):
            await update.message.reply_text("⚠️ مسموح فقط بالأرقام والعمليات الحسابية (+, -, *, /, .)")
            return
        
        # تقييم العملية
        result = eval(expression)
        await update.message.reply_text(f"🧮 {expression} = {result}")
        
    except Exception as e:
        logger.error(f"Calc error: {e}")
        await update.message.reply_text("❌ تعبير غير صحيح، جرب:\n/calc 10 + 5\n/calc 20 / 4")

async def current_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الوقت الحالي"""
    from datetime import datetime
    import pytz
    
    # توقيت الرياض (توقيت السعودية)
    try:
        riyadh_tz = pytz.timezone('Asia/Riyadh')
        riyadh_time = datetime.now(riyadh_tz)
        time_str = riyadh_time.strftime("%Y-%m-%d %I:%M:%S %p")
        
        await update.message.reply_text(f"🕒 **الوقت في الرياض:**\n{time_str}")
    except:
        # إذا فشل، استخدم الوقت المحلي
        local_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        await update.message.reply_text(f"🕒 **الوقت الحالي:**\n{local_time}")

async def current_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التاريخ الحالي"""
    from datetime import datetime
    
    # التاريخ باللغة العربية
    months_arabic = [
        "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
        "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
    ]
    
    days_arabic = [
        "الاثنين", "الثلاثاء", "الأربعاء", "الخميس",
        "الجمعة", "السبت", "الأحد"
    ]
    
    now = datetime.now()
    arabic_date = f"{now.day} {months_arabic[now.month-1]} {now.year}"
    arabic_day = days_arabic[now.weekday()]
    
    await update.message.reply_text(f"📅 **التاريخ اليوم:**\n{arabic_date}\n**اليوم:** {arabic_day}")

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختبار سرعة البوت"""
    import time
    
    start_time = time.time()
    message = await update.message.reply_text("🏓 بنج...")
    end_time = time.time()
    
    ping_time = round((end_time - start_time) * 1000, 2)
    
    await message.edit_text(f"🏓 بونج!\n⏱️ زمن الاستجابة: {ping_time} مللي ثانية\n✅ البوت يعمل بشكل طبيعي")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل العادية"""
    message = update.message.text
    
    if not message or message.startswith('/'):
        return
    
    await update.message.reply_chat_action("typing")
    
    try:
        # استخدام خدمة AI مجانية للرد
        response = await ai_service.chat(message)
        
        # إذا كانت الإجابة قصيرة، أضف اقتراحات
        if len(response) < 50:
            response += "\n\n💡 يمكنك استخدام:\n/ask للأسئلة المحددة\n/search للبحث\n/news للأخبار"
        
        await update.message.reply_text(response[:4000])
        
    except Exception as e:
        logger.error(f"Message error: {e}")
        await update.message.reply_text(
            "💬 يمكنني مساعدتك في:\n"
            "• الإجابة على الأسئلة: /ask سؤالك\n"
            "• البحث في الإنترنت: /search موضوع\n"
            "• تلخيص المقالات: /summarize رابط\n"
            "• النكات والترفيه: /joke"
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأخطاء"""
    logger.error(f"Error: {context.error}")
    
    if update and update.message:
        await update.message.reply_text(
            "⚠️ حدث خطأ غير متوقع.\n"
            "يمكنك المحاولة مرة أخرى أو تجربة أمر آخر.\n"
            "استخدم /help لعرض جميع الأوامر."
        )

def main():
    """الدالة الرئيسية لتشغيل البوت"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("❌ خطأ: TELEGRAM_BOT_TOKEN غير موجود في المتغيرات البيئية")
        print("📝 أضف التوكن في ملف .env أو متغيرات Railway")
        return
    
    # إنشاء تطبيق البوت
    application = Application.builder().token(token).build()
    
    # إضافة جميع الأوامر
    commands = [
        CommandHandler("start", start),
        CommandHandler("help", help_command),
        CommandHandler("ask", ask_question),
        CommandHandler("search", web_search),
        CommandHandler("search5", web_search),  # بحث بخمس نتائج
        CommandHandler("summarize", summarize_url),
        CommandHandler("news", get_news),
        CommandHandler("wiki", wikipedia_search),
        CommandHandler("joke", tell_joke),
        CommandHandler("quote", inspirational_quote),
        CommandHandler("fact", random_fact),
        CommandHandler("riddle", random_riddle),
        CommandHandler("calc", calculator),
        CommandHandler("time", current_time),
        CommandHandler("date", current_date),
        CommandHandler("ping", ping_command)
    ]
    
    for handler in commands:
        application.add_handler(handler)
    
    # معالج الرسائل العادية
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # معالج الأخطاء
    application.add_error_handler(error_handler)
    
    # بدء البوت
    print("=" * 50)
    print("🚀 بوت تليجرام الذكي المجاني")
    print("📅 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("⚡ الإصدار: 2.0 (مجاني بالكامل)")
    print("💻 يعمل على: Railway (مجاني)")
    print("=" * 50)
    
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
