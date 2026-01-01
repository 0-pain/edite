import telebot
from telebot import types
import csv
import json
import os
from datetime import datetime

# ========= الإعدادات =========
TOKEN = "7521086803:AAFQPIGYfzM1HicORhLQBcNNPp5iv-TN0-4"
ADMIN_ID = 8163245201

DATA_DIR = "data"
USERS_FILE = "users.json"

bot = telebot.TeleBot(TOKEN)

photo = "https://t.me/mybotinfo/2"
dev = "https://t.me/o21211"

# ========= تهيئة =========
os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

user_files = {}

# ========= دوال =========
def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def register_user(user):
    users = load_users()
    uid = str(user.id)
    if uid not in users:
        users[uid] = {
            "name": user.first_name or "",
            "username": user.username or "",
            "vip_until": None,
            "banned": False,
            "joined": datetime.now().isoformat()
        }
        save_users(users)

def is_vip(uid):
    users = load_users()
    u = users.get(str(uid))
    if not u or not u.get("vip_until"):
        return False
    try:
        return datetime.now() < datetime.fromisoformat(u["vip_until"])
    except:
        return False

# ========= START =========
@bot.message_handler(commands=["start"])
def start(message):
    register_user(message.from_user)
    status = "⭐ VIP" if is_vip(message.from_user.id) else "👤 عادي"

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("📁 إرسال ملف", callback_data="upload"),
        types.InlineKeyboardButton("👨‍💻 المطور", url=dev)
    )

    bot.send_photo(
        message.chat.id,
        photo,
        caption=f"مرحباً {message.from_user.first_name}\nحالتك: {status}",
        reply_markup=kb
    )

# ========= رفع الملفات =========
@bot.callback_query_handler(func=lambda c: c.data == "upload")
def upload(call):
    bot.answer_callback_query(call.id)
    if call.from_user.id != ADMIN_ID and not is_vip(call.from_user.id):
        return bot.send_message(call.message.chat.id, "🚫 VIP فقط")

    bot.send_message(call.message.chat.id, "📂 أرسل ملفات TXT أو CSV")

@bot.message_handler(content_types=["document"])
def handle_docs(message):
    register_user(message.from_user)
    uid = str(message.from_user.id)

    if message.from_user.id != ADMIN_ID and not is_vip(message.from_user.id):
        return bot.reply_to(message, "🚫 VIP فقط")

    doc = message.document
    name = doc.file_name.lower()

    if not (name.endswith(".txt") or name.endswith(".csv")):
        return bot.reply_to(message, "❌ الصيغة غير مدعومة")

    info = bot.get_file(doc.file_id)
    data = bot.download_file(info.file_path)

    path = os.path.join(DATA_DIR, f"{uid}_{doc.file_name}")
    with open(path, "wb") as f:
        f.write(data)

    user_files.setdefault(uid, []).append(path)

    bot.reply_to(message, "✅ تم حفظ الملف\n🔍 أرسل BIN / PREFIX للبحث")

# ========= البحث مع الحفظ =========
def collect_results(file_path, prefix, results):
    lower = file_path.lower()

    try:
        if lower.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    card = line.split("|")[0].strip()
                    if card.startswith(prefix):
                        results.append(line)

        elif lower.endswith(".csv"):
            for enc in ("utf-8", "cp1256", "latin-1"):
                try:
                    with open(file_path, newline="", encoding=enc, errors="ignore") as f:
                        reader = csv.reader(f)
                        for row in reader:
                            if not row:
                                continue
                            card = str(row[0]).strip()
                            if card.startswith(prefix):
                                results.append(" | ".join(row))
                    break
                except:
                    continue

    except Exception as e:
        results.append(f"ERROR: {e}")

# ========= استقبال رقم البحث =========
@bot.message_handler(func=lambda m: m.text and m.text.isdigit())
def handle_search(message):
    uid = str(message.from_user.id)

    if uid not in user_files or not user_files[uid]:
        return bot.reply_to(message, "📁 أرسل ملف أولاً")

    prefix = message.text.strip()

    if not (6 <= len(prefix) <= 12):
        return bot.reply_to(message, "🔢 أدخل رقم من 6 إلى 12 خانة")

    bot.send_message(message.chat.id, f"🔍 جاري البحث عن {prefix} ...")

    results = []

    for path in user_files[uid]:
        collect_results(path, prefix, results)

    if not results:
        return bot.send_message(message.chat.id, f"❌ لا توجد بطاقات تبدأ بـ {prefix}")

    # ---- حفظ النتائج ----
    out_file = os.path.join(DATA_DIR, f"RESULT_{prefix}_{uid}.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(results))

    bot.send_document(
        message.chat.id,
        open(out_file, "rb"),
        caption=f"✅ تم العثور على {len(results)} بطاقة"
    )

    if prefix=="/r":
    	os.remove(out_file)
    	for f in user_files[uid]:
    	       try:
    	       	os.remove(f)
    	       except:
    	       	pass
@bot.message_handler(commands=["end"])
def end_session(message):
    uid = str(message.from_user.id)

    if uid not in user_files or not user_files[uid]:
        return bot.reply_to(message, "❌ لا توجد ملفات محفوظة")

    removed = 0
    for f in user_files[uid]:
        try:
            os.remove(f)
            removed += 1
        except:
            pass

    del user_files[uid]

    bot.reply_to(
        message,
        f"🧹 تم حذف {removed} ملف\n📁 أرسل ملفات جديدة للبحث"
    )

# ========= تشغيل =========
print("🤖 BOT RUNNING ...")
bot.infinity_polling(none_stop=True)
