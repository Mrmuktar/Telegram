import os
import logging
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# .env-এর নামের সঙ্গে মিল রেখে পড়া হচ্ছে
TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_ID", "").split(",")
    if x.strip().isdigit()
}
DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL", "").strip()
SERVICE_ACCOUNT = os.getenv(
    "FIREBASE_CREDENTIALS", "serviceAccountKey.json"
).strip()


def init_firebase():
    if not DATABASE_URL:
        raise RuntimeError("FIREBASE_DATABASE_URL .env ফাইলে বসান")
    if not os.path.isfile(SERVICE_ACCOUNT):
        raise RuntimeError(
            f"Firebase service account JSON পাওয়া যায়নি: {SERVICE_ACCOUNT}"
        )
    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_ACCOUNT)
        firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})


def allowed(uid):
    return uid in ADMIN_IDS


def menu():
    rows = [
        [
            InlineKeyboardButton("📤 ভিডিও যোগ", callback_data="add_video"),
            InlineKeyboardButton("🗂 ক্যাটাগরি", callback_data="categories"),
        ],
        [
            InlineKeyboardButton("🔗 লিংক যোগ", callback_data="add_link"),
            InlineKeyboardButton("⚙️ সেটিংস", callback_data="settings"),
        ],
        [
            InlineKeyboardButton("📋 ভিডিও তালিকা", callback_data="list_videos"),
            InlineKeyboardButton("🗑️ ভিডিও ডিলিট", callback_data="delete_video"),
        ],
        [
            InlineKeyboardButton("📡 Mini App লিংক", callback_data="bot_link"),
            InlineKeyboardButton("📊 স্ট্যাটস", callback_data="stats"),
        ],
    ]
    return InlineKeyboardMarkup(rows)


def menu_button():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("↩️ Admin Menu", callback_data="home")]]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not allowed(update.effective_user.id):
        await update.effective_message.reply_text(
            "⛔ এই প্যানেল শুধু অনুমোদিত অ্যাডমিনের জন্য।"
        )
        return
    context.user_data.pop("mode", None)
    await update.effective_message.reply_text(
        "💎 VIRAL ZONE VIDEO — Admin Control\n\nযে কাজটি করতে চান নির্বাচন করুন:",
        reply_markup=menu()
    )


async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if not allowed(q.from_user.id):
        await q.edit_message_text("⛔ Access denied.")
        return

    action = q.data

    if action == "home":
        context.user_data.pop("mode", None)
        text = "💎 VIRAL ZONE VIDEO — Admin Control"
        await q.edit_message_text(text, reply_markup=menu())
        return

    if action == "add_video":
        context.user_data["mode"] = "add_video"
        text = (
            "📤 ভিডিও যোগ করুন — নিচের ৫টি তথ্য আলাদা লাইনে পাঠান:\n"
            "1. ভিডিওর নাম\n2. Image URL\n3. Download URL\n"
            "4. Category ID (যেমন general)\n5. Required ad count (যেমন 1)\n\n"
            "Image ও Download URL অবশ্যই http/https হতে হবে।"
        )
    elif action == "categories":
        context.user_data["mode"] = "categories"
        text = "🗂 ক্যাটাগরি যোগ করতে লিখুন:\ncategory_id | ক্যাটাগরির নাম"
    elif action == "add_link":
        context.user_data["mode"] = "add_link"
        text = "🔗 লিংক যোগ করতে লিখুন:\nলিংকের নাম | https://example.com"
    elif action == "settings":
        context.user_data["mode"] = "settings"
        text = "⚙️ সেটিংস লিখুন:\nads_limit | 20\nঅথবা\ntutorial_id | https://example.com"
    elif action == "bot_link":
        context.user_data["mode"] = "bot_link"
        text = "📱 Mini App link লিখুন:\nbot_app_link | https://t.me/YourBot/app"
    elif action == "list_videos":
        data = db.reference("videos").get() or {}
        if not isinstance(data, dict):
            data = {}
        lines = [
            f"• {k} — {v.get('name', '(নাম নেই)')}"
            for k, v in list(data.items())[-30:]
            if isinstance(v, dict)
        ]
        text = "📋 সর্বশেষ ভিডিও\n" + ("\n".join(lines) if lines else "কোনো ভিডিও নেই।")
    elif action == "delete_video":
        context.user_data["mode"] = "delete_video"
        data = db.reference("videos").get() or {}
        if not isinstance(data, dict):
            data = {}
        lines = [
            f"• {k} — {v.get('name', '')}"
            for k, v in list(data.items())[-20:]
            if isinstance(v, dict)
        ]
        text = "🗑️ ডিলিট করতে ভিডিও ID পাঠান:\n" + (
            "\n".join(lines) if lines else "কোনো ভিডিও নেই।"
        )
    elif action == "stats":
        videos = db.reference("videos").get() or {}
        links = db.reference("links").get() or {}
        if not isinstance(videos, dict):
            videos = {}
        if not isinstance(links, dict):
            links = {}
        views = sum(
            int(v.get("view_count", 0) or 0)
            for v in videos.values() if isinstance(v, dict)
        )
        text = (
            "📊 Dashboard Stats\n"
            f"🎬 Videos: {len(videos)}\n"
            f"🔗 Links: {len(links)}\n"
            f"👁 Total views: {views}"
        )
    else:
        text = "কাজটি নির্বাচন করুন।"

    await q.edit_message_text(text, reply_markup=menu_button())


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not allowed(update.effective_user.id):
        return

    mode = context.user_data.get("mode")
    if not mode:
        await update.effective_message.reply_text(
            "মেনু খুলতে /start লিখুন।", reply_markup=menu()
        )
        return

    text = (update.effective_message.text or "").strip()

    try:
        if mode == "add_video":
            parts = text.splitlines()
            if len(parts) < 5:
                raise ValueError(
                    "৫টি লাইন দিন: নাম, image URL, download URL, category ID, ad count"
                )
            name, image, download, category, req = [p.strip() for p in parts[:5]]
            if not image.startswith(("https://", "http://")):
                raise ValueError("Image URL http/https হতে হবে")
            if not download.startswith(("https://", "http://")):
                raise ValueError("Download URL http/https হতে হবে")
            try:
                ad_count = max(1, min(20, int(req)))
            except ValueError:
                raise ValueError("Ad count 1 থেকে 20-এর মধ্যে সংখ্যা হতে হবে")
            key = db.reference("videos").push().key
            db.reference(f"videos/{key}").set({
                "name": name[:180],
                "image_url": image,
                "download_link": download,
                "category": category or "general",
                "ad_watches_required": ad_count,
                "view_count": 0,
            })
            reply = f"✅ ভিডিও যোগ হয়েছে। ID: {key}"

        elif mode == "categories":
            if "|" not in text:
                raise ValueError("category_id | ক্যাটাগরির নাম এই ফরম্যাটে লিখুন")
            key, name = [x.strip() for x in text.split("|", 1)]
            if not key or not name:
                raise ValueError("Category ID এবং নাম দুটোই দিতে হবে")
            db.reference(f"filters/{key}").set({"name": name[:80]})
            reply = "✅ ক্যাটাগরি যোগ হয়েছে।"

        elif mode == "add_link":
            if "|" not in text:
                raise ValueError("লিংকের নাম | https://example.com এই ফরম্যাটে লিখুন")
            title, url = [x.strip() for x in text.split("|", 1)]
            if not url.startswith(("https://", "http://")):
                raise ValueError("সঠিক http/https URL দিন")
            key = db.reference("links").push().key
            db.reference(f"links/{key}").set({
                "title": title[:100],
                "url": url,
            })
            reply = "✅ লিংক যোগ হয়েছে।"

        elif mode == "settings":
            if "|" not in text:
                raise ValueError("key | value এই ফরম্যাটে লিখুন")
            key, value = [x.strip() for x in text.split("|", 1)]
            if not key:
                raise ValueError("Setting key খালি রাখা যাবে না")
            if key == "ads_limit":
                value = max(1, min(1000, int(value)))
            db.reference(f"settings/{key}").set(value)
            reply = "✅ সেটিংস সেভ হয়েছে।"

        elif mode == "bot_link":
            if "|" not in text:
                raise ValueError("bot_app_link | https://... এই ফরম্যাটে লিখুন")
            key, value = [x.strip() for x in text.split("|", 1)]
            if key != "bot_app_link":
                raise ValueError("key হিসেবে bot_app_link দিন")
            if not value.startswith("https://"):
                raise ValueError("Mini App URL অবশ্যই HTTPS হতে হবে")
            db.reference("settings/bot_app_link").set(value)
            reply = "✅ Mini App link সেভ হয়েছে।"

        elif mode == "delete_video":
            if not text or "/" in text:
                raise ValueError("সঠিক Video ID দিন")
            ref = db.reference(f"videos/{text}")
            if ref.get() is None:
                raise ValueError("এই Video ID পাওয়া যায়নি")
            ref.delete()
            reply = "🗑️ ভিডিও ডিলিট করা হয়েছে।"

        else:
            reply = "এই কাজটি পাওয়া যায়নি।"

    except Exception as e:
        reply = f"❌ {str(e)}"

    context.user_data.pop("mode", None)
    await update.effective_message.reply_text(reply, reply_markup=menu())


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN .env ফাইলে বসান")
    if not ADMIN_IDS:
        raise RuntimeError("ADMIN_ID-এ আপনার numeric Telegram ID দিন")

    init_firebase()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    print("VIRAL ZONE Firebase Admin Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
