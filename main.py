import telebot, re, json, string, threading
from telebot import types
from datetime import datetime, timedelta
from gatet import *
from file import *
import logging
import secrets
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from telebot import types
import time
import requests
from colorama import Fore
from datetime import datetime, timedelta

from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)

USERS_FILE="users.json"
SUBSCRIPTION_FILE = 'subscriptions.json'
DEVELOPER_USERNAME = "@o21211"
DEVELOPER_NAME = "Rashed"
DEVELOPER_URL = "https://t.me/o21211"
CHANNEL_URL = "https://t.me/givtestars"
logging.basicConfig(level=logging.INFO, filename='bot.log', format='%(asctime)s - %(levelname)s - %(message)s')

ADMIN_ID = 8163245201
CHANNEL ="@givtestars"
token = "7955465674:AAHDr8dJm1BMTj5Jw3rqI1ApvAYsyk0Zhqc"
bot = telebot.TeleBot(token, parse_mode="HTML")
command_usage = {}
run_events = {}



executor = ThreadPoolExecutor(max_workers=5)  
#ppcex = ThreadPoolExecutor(max_workers=1)  
stop_flags = {}
def reset_command_usage():
	for user_id in command_usage:
		command_usage[user_id] = {'count': 0, 'last_time': None}

# تحميل المستخدمين
def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def get_bin_info(bin_number):
    try:
        url = f"https://lookup.binlist.net/{bin_number}"
        headers = {"Accept-Version": "3"}
        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            return None

        data = r.json()
        return {
            "scheme": data.get("scheme", "Unknown"),
            "brand": data.get("brand", "Unknown"),
            "card_type": data.get("type", "Unknown"),
            "bank": data.get("bank", {}).get("name", "Unknown"),
            "country": data.get("country", {}).get("name", "Unknown"),
            "country_flag": data.get("country", {}).get("emoji", "")
        }

    except:
        return None

def extract_digits(text):
    return "".join(re.findall(r"\d+", str(text)))



from telebot import types
import json
import logging
from datetime import datetime, timedelta


# ---------------- LOAD / SAVE ---------------- #

def load_json_file(file_path):
    try:
        with open(file_path, 'r') as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from {file_path}: {str(e)}")
        return {}


def save_json_file(file_path, data):
    try:
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Error saving JSON to {file_path}: {str(e)}")


# ---------------- UTILITIES ---------------- #

def update_user_status():
    """يحوّل أي اشتراك منتهي إلى FREE تلقائياً."""
    data = load_json_file(SUBSCRIPTION_FILE)
    changed = False
    now = datetime.now()

    for key, value in data.items():
        if isinstance(value, dict) and "plan" in value and "timer" in value:
            if value["plan"] != "𝗙𝗥𝗘𝗘":
                if value["timer"] != "none":
                    try:
                        expire = datetime.strptime(value["timer"], "%Y-%m-%d %H:%M")
                        if now >= expire:
                            value["plan"] = "𝗙𝗥𝗘𝗘"
                            value["timer"] = "none"
                            changed = True
                    except:
                        continue

    if changed:
        save_json_file(SUBSCRIPTION_FILE, data)


def get_user_plan(uid):
    """الحصول على خطة المستخدم الحالية (بعد التحقق من انتهاء الاشتراك)."""
    update_user_status()
    data = load_json_file(SUBSCRIPTION_FILE)
    return data.get(str(uid), {}).get("plan", "𝗙𝗥𝗘𝗘")


def get_user_expire(uid):
    """كم الوقت المتبقي."""
    data = load_json_file(SUBSCRIPTION_FILE)
    raw = data.get(str(uid), {})
    timer = raw.get("timer", "none")
    if timer == "none":
        return 0

    try:
        expire = datetime.strptime(timer, "%Y-%m-%d %H:%M")
        remaining = expire - datetime.now()
        return max(0, int(remaining.total_seconds()))
    except:
        return 0


# ------------------------------
# تحميل وحفظ المستخدمين
# ------------------------------
def is_banned(user_id):
    users = load_users()
    return users.get(str(user_id), {}).get("banned", False)



# ------------------------------
# /add user_id days
# ------------------------------
import random
import string

def generate_random_code(length=8):
    """انشاء كود عشوائي"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@bot.message_handler(commands=['add'])
def add_user(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ هذه الأوامر للمسؤول فقط.")
        return

    try:
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "❌ الاستخدام الصحيح:\n/add user_id hours")
            return

        user_id = args[1]
        hours = int(args[2])

        # حساب وقت الانتهاء
        expire = datetime.now() + timedelta(hours=hours)
        expire_str = expire.strftime("%Y-%m-%d %H:%M")

        # تحميل الملف
        db = load_json_file(SUBSCRIPTION_FILE)

        # إنشاء كود عشوائي
        code = generate_random_code()

        # حفظ الاشتراك بالشكل المطلوب
        db[user_id] = {
            "plan": "VIP",
            "timer": expire_str
        }

        # إضافة الكود عشوائي في حالة أردنا used_by لاحقًا
        db[code] = {
            "used_by": [user_id],
            "user_limit": 1,
            "plan": "VIP",
            "time": expire_str
        }

        save_json_file(SUBSCRIPTION_FILE, db)

        # رسالة تأكيد
        bot.reply_to(
            message,
            f"🎉 تم إضافة مستخدم جديد:\n"
            f"🆔 ايدي: `{user_id}`\n"
            f"⏳ الوقت: {hours} ساعة\n"
            f"📅 ينتهي: {expire_str}\n"
            f"🔑 الكود: `{code}`",
            parse_mode="Markdown"
        )

    except Exception as e:
        logging.error(f"Error in /add: {str(e)}")
        bot.reply_to(message, "❌ حدث خطأ أثناء إضافة المستخدم.")




@bot.message_handler(commands=['remove'])
def remove_user(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ هذه الأوامر للمسؤول فقط.")
        return

    users = load_users()
    user_id = None
    username = None

    # التحقق إذا كان الرد على رسالة
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        user_id = str(user.id)
        username = user.username
    else:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ الاستخدام الصحيح:\n/remove user_id_or_username\nأو بالرد على رسالة المستخدم")
            return
        user_input = args[1]
        if user_input.startswith("@"):
            username = user_input[1:]
            user_id = username
        else:
            user_id = user_input

    if user_id in users:
        users[user_id]["role"] = "free"
        users[user_id]["expire"] = 0
        # حفظ الاسم/username إذا موجود
        if username:
            users[user_id]["username"] = username
        save_users(users)

        if username:
            user_link = f"https://t.me/{username}"
            display_name = username
        else:
            user_link = f"tg://openmessage?user_id={user_id}"
            display_name = user_id

        bot.reply_to(message, f"✔️ تم إزالة VIP عن [{display_name}]({user_link})", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ المستخدم غير موجود")





# ------------------------------
# /ban - حظر مستخدم
# ------------------------------
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ هذه الأوامر للمسؤول فقط.")
        return

    users = load_users()
    user_id = None
    username = None

    # التحقق إذا كان الرد على رسالة
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        user_id = str(user.id)
        username = user.username
    else:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ الاستخدام الصحيح:\n/ban user_id_or_username\nأو بالرد على رسالة المستخدم")
            return
        user_input = args[1]
        if user_input.startswith("@"):
            username = user_input[1:]
            user_id = username
        else:
            user_id = user_input

    if user_id not in users:
        users[user_id] = {"username": username or "don't have username"}

    if users[user_id].get("banned", False):
        bot.reply_to(message, f"⚠ المستخدم [{user_id}] محظور سابقًا.")
    else:
        users[user_id]["banned"] = True
        users[user_id]["username"] = username or users[user_id].get("username", "don't have username")
        save_users(users)

        if username:
            user_link = f"https://t.me/{username}"
            display_name = username
        else:
            user_link = f"tg://openmessage?user_id={user_id}"
            display_name = user_id

        bot.reply_to(message, f"⛔ تم حظر [{display_name}]({user_link})", parse_mode="Markdown")

# ------------------------------
# /unban - فك الحظر
# ------------------------------
@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ هذه الأوامر للمسؤول فقط.")
        return

    users = load_users()
    user_id = None
    username = None

    if message.reply_to_message:
        user = message.reply_to_message.from_user
        user_id = str(user.id)
        username = user.username
    else:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ الاستخدام الصحيح:\n/unban user_id_or_username\nأو بالرد على رسالة المستخدم")
            return
        user_input = args[1]
        if user_input.startswith("@"):
            username = user_input[1:]
            user_id = username
        else:
            user_id = user_input

    if user_id not in users:
        users[user_id] = {"username": username or "don't have username"}

    if not users[user_id].get("banned", False):
        bot.reply_to(message, f"⚠ المستخدم [{user_id}] غير محظور.")
    else:
        users[user_id]["banned"] = False
        users[user_id]["username"] = username or users[user_id].get("username", "don't have username")
        save_users(users)

        if username:
            user_link = f"https://t.me/{username}"
            display_name = username
        else:
            user_link = f"tg://openmessage?user_id={user_id}"
            display_name = user_id

        bot.reply_to(message, f"✅ تم فك الحظر عن [{display_name}]({user_link})", parse_mode="Markdown")

# ------------------------------
# /banned - قائمة المحظورين
# ------------------------------
@bot.message_handler(commands=['banned'])
def list_banned(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ هذه الأوامر للمسؤول فقط.")
        return

    users = load_users()
    banned_users = {uid: info for uid, info in users.items() if info.get("banned", False)}

    if not banned_users:
        bot.reply_to(message, "لا يوجد مستخدمون محظورون حالياً.")
        return

    msg_lines = ["📛 قائمة المستخدمين المحظورين:\n"]
    for idx, (uid, info) in enumerate(banned_users.items(), start=1):
        username = info.get("username")
        display_name = username if username and username != "don't have username" else f"ID: {uid}"
        if username and username != "don't have username":
            link = f"https://t.me/{username}"
        else:
            link = f"tg://openmessage?user_id={uid}"
        msg_lines.append(f"{idx}- [{display_name}]({link})")

    msg_text = "\n".join(msg_lines)
    bot.send_message(message.chat.id, msg_text, parse_mode="Markdown")

    # هنا تابع منطق الأمر


# ------------------------------
# /id — معلومات المستخدم
# ------------------------------
@bot.message_handler(commands=['id'])
def user_info(message):
    user = message.from_user

    msg = (
        f"🆔 **ID:** `{user.id}`\n"
        f"👤 **Username:** @{user.username}\n"
        f"📛 **Name:** {user.first_name}\n"
    )

    bot.reply_to(message, msg, parse_mode="Markdown")

# ======================
#       START
# ======================
@bot.message_handler(commands=["start"])
def back_to_star(message):
    us = message.from_user.id
    if is_banned(us):
    	bot.reply_to(message, "⚠ انت محظور من استخدام البوت")
    	return
    def check_join(user_id):
        try:
            member = bot.get_chat_member(CHANNEL, user_id)
            return member.status in ["member", "administrator", "creator"]
        except:
            return False

    def get_user_plan(user_id):
        user_id = int(user_id)
        try:
            with open("subscriptions.json", "r") as f:
                data = json.load(f)
        except:
            return ("𝗙𝗥𝗘𝗘", None)

        for code, info in data.items():
            used_by = info.get("used_by", [])
            if user_id in used_by:
                return (info.get("plan", "𝗙𝗥𝗘𝗘"), info.get("time", None))

        return ("𝗙𝗥𝗘𝗘", None)

    def my_function():
        uid = message.from_user.id
        plan, end_time = get_user_plan(uid)

        if not check_join(uid):
            bot.send_message(uid, f"🚫 يجب عليك الاشتراك أولاً في القناة:\n{CHANNEL}")
            return

        # FREE USER
        if plan == "𝗙𝗥𝗘𝗘":
            try:
                with open("subscriptions.json", "r") as f:
                    data = json.load(f)
            except:
                data = {}

            data[str(uid)] = {"plan": "𝗙𝗥𝗘𝗘", "timer": "none"}

            with open("subscriptions.json", "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            keyboard = types.InlineKeyboardMarkup()
            cmds_button = types.InlineKeyboardButton("🧩 Commands", callback_data="open_cmds_from_start")
            owner_button = types.InlineKeyboardButton("✨ 𝗢𝗪𝗡𝗘𝗥 ✨", url="https://t.me/O21211")

            keyboard.add(cmds_button)
            keyboard.add(owner_button)

            with open("f.jpg", "rb") as photo:
                bot.send_photo(
                    chat_id=message.chat.id,
                    photo=photo,
                    caption=(
                        "<b>🤖 𝗕𝗼𝘁 𝗦𝘁𝗮𝘁𝘂𝘀: 𝗔𝗰𝘁𝗶𝘃𝗲 ✅\n"
                        "Join <a href='https://t.me/O77131'>Here</a> to get updates and keys.\n"
                        "Press the button below to open commands.</b>"
                    ),
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            return

        # VIP USER
        keyboard = types.InlineKeyboardMarkup()
        cmds_button = types.InlineKeyboardButton("🧩 Commands", callback_data="open_cmds_from_start")
        join_button = types.InlineKeyboardButton("⚠ Dev Bot ⚠", url="https://t.me/O21211")

        keyboard.add(cmds_button)
        keyboard.add(join_button)

        with open("f.jpg", "rb") as photo:
            bot.send_photo(
                chat_id=message.chat.id,
                photo=photo,
                caption=(
                    "𝗡𝗼𝘄 𝗦𝗲𝗻𝗱 𝗧𝗵𝗲 /cmds 𝗖𝗼𝗺𝗺𝗮𝗻𝗱\n\n"
                    "𝗢𝗿 𝗝𝘂𝘀𝘁 𝗣𝗿𝗲𝘀𝘀 𝗧𝗵𝗲 𝗕𝘂𝘁𝘁𝗼𝗻 𝗕𝗲𝗹𝗼𝘄 👇\n\n"
                    "<b>love from <a href='https://t.me/O21211'>Rashed</a></b>"
                ),
                parse_mode="HTML",
                reply_markup=keyboard
            )

    threading.Thread(target=my_function).start()

# ======================
#   KEYBOARDS
# ======================
def main_menu_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("Gate Auth ✅", callback_data="gate_auth"),
        types.InlineKeyboardButton("Gate Charge 🔥", callback_data="gate_charge"),
        types.InlineKeyboardButton("Gate lookup ✅", callback_data="gate_lookup"),
    )
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start"))
    return kb

def back_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="main_menu"))
    return kb

# ======================
#      /cmds COMMAND
# ======================
@bot.message_handler(commands=["cmds"])
def cmds(message):
    us = message.from_user.id
    if is_banned(us):
    	bot.reply_to(message, "⚠ انت محظور من استخدام البوت")
    	return
    try:
        with open('subscriptions.json', 'r') as file:
            json_data = json.load(file)
    except:
        json_data = {}

    uid = str(message.from_user.id)
    BL = "𝗙𝗥𝗘𝗘"

    for sub_key, info in json_data.items():
        used_by = info.get("used_by", [])
        plan = info.get("plan", "𝗙𝗥𝗘𝗘")
        if uid in map(str, used_by):
            BL = plan

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("commands ⚙️", callback_data="main_menu"),
        types.InlineKeyboardButton("✨ Dev ✨", url="https://t.me/o21211")
    )

    photo = open("g.jpg", "rb")
    bot.send_photo(
        chat_id=message.chat.id,
        photo=photo,
        caption=f"<b>Welcome <a href='https://t.me/{message.from_user.username}'>{message.from_user.first_name}</a>: {BL}</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )

# ======================
#     CALLBACK SYSTEM
# ======================


@bot.callback_query_handler(func=lambda call: call.data == "go_cmds")
def callback_gate_charge(call):
    us = call.from_user.id
    if is_banned(us):
    	bot.reply_to(call.message, "⚠ انت محظور من استخدام البوت")
    	return
    try:
        photo = open("b.jpg", "rb")

        bot.edit_message_media(
            media=InputMediaPhoto(photo, caption="🔥 <b>Welcome in commands page</b>"),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=main_menu_keyboard()
        )

    except Exception as e:
        print(e)
@bot.message_handler(content_types=["document"])
def main(message):
    user_id = message.from_user.id
    user_id_str = str(user_id)
    if is_banned(user_id):
    	bot.reply_to(message, "⚠ انت محظور من استخدام البوت")
    	return
    # ------------------------ CHECK JOIN ------------------------
    def check_join(uid):
        try:
            member = bot.get_chat_member(CHANNEL, uid)
            return member.status in ["member", "administrator", "creator"]
        except:
            return False

    if not check_join(user_id):
        bot.send_message(
            user_id,
            f"🚫 يجب عليك الاشتراك أولاً في القناة:\n{CHANNEL}"
        )
        return

    # ------------------------ LOAD JSON ------------------------
    try:
        with open('subscriptions.json', 'r') as f:
            data = json.load(f)
    except:
        data = {}

    # ------------------------ DETECT USER PLAN ------------------------
    plan = "𝗙𝗥𝗘𝗘"
    used_code = None  # ← نحتاجه لاحقاً لقراءة الوقت

    # البحث داخل الأكواد لمعرفة هل هذا المستخدم VIP
    for code, info in data.items():
        used_by = info.get("used_by", [])
        if user_id in used_by:
            plan = info.get("plan", "𝗙𝗥𝗘𝗘")
            used_code = code
            break

    # ------------------------ IF FREE → REGISTER SIMPLE ENTRY ------------------------
    if plan == "𝗙𝗥𝗘𝗘":
        # إضافة المستخدم في النظام إذا لم يكن موجود
        if user_id_str not in data:
            data[user_id_str] = {"plan": "𝗙𝗥𝗘𝗘", "timer": "none"}
            with open("subscriptions.json", "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

        keyboard = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton(
            text="✨ 𝗢𝗪𝗡𝗘𝗥 ✨",
            url="https://t.me/O21211"
        )
        keyboard.add(contact_button)

        bot.send_message(
            chat_id=message.chat.id,
            text=f'''<b>🤖 𝗕𝗼𝘁 𝗦𝘁𝗮𝘁𝘂𝘀: 𝗔𝗰𝘁𝗶𝘃𝗲 ✅
Text: وقتك انتهى حبي جدد اشتراك 
Join <a href="t.me/O77131">Here</a> to get updates and keys.
Send /cmds by <a href="t.me/O21211">Rashed</a>.</b>''',
            reply_markup=keyboard,disable_web_page_preview=True,
        )
        return

    # ------------------------ VIP USER → CHECK TIME ------------------------
    if used_code:  
        vip_info = data.get(used_code)

        exp_time = vip_info.get("time", None)

        if exp_time:
            try:
                date_str = exp_time.split('.')[0]   # تنظيف ميلي ثانية إن وجدت
                expire_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            except:
                # وقت فاسد أو غير صحيح
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("✨ 𝗢𝗪𝗡𝗘𝗥 ✨", url="https://t.me/O21211"))
                bot.send_message(message.chat.id, "<b>❌ وقتك انتهى حبي جدد اشتراك.</b>", reply_markup=kb)
                return

            # مقارنة الوقت
            if datetime.now() > expire_date:
                # اشتراك منتهي → رجع FREE
                data[user_id_str] = {"plan": "𝗙𝗥𝗘𝗘", "timer": "none"}
                with open("subscriptions.json", "w") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("✨ 𝗢𝗪𝗡𝗘𝗥 ✨", url="https://t.me/O21211"))
                bot.send_message(message.chat.id, "<b>Your subscription expired ❌</b>", reply_markup=kb)
                return

    # ------------------------ USER IS VIP → SEND GATE BUTTONS ------------------------
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("Strip Auth 🎲", callback_data='sq'),
        types.InlineKeyboardButton("PayPal 🎲", callback_data='paypal'),
        types.InlineKeyboardButton("Braintree 🎲", callback_data='Braintree'),
        types.InlineKeyboardButton("strip_charge 🎲", callback_data='strip_charge'),
        types.InlineKeyboardButton("Passed 🎲", callback_data='passed'),
        types.InlineKeyboardButton("OTP 🎲", callback_data='OTP'),
        types.InlineKeyboardButton("PayPal Commerc 1$ 🎲", callback_data='paypalcom'),
        types.InlineKeyboardButton("ppc donate 1$ 🎲", callback_data='ppc'),
        types.InlineKeyboardButton("My PPC 1$ 🎲", callback_data='ppc001'),
        types.InlineKeyboardButton("PPC donate 1$ New ",callback_data='nppc')
    )

    bot.reply_to(message, "Choose The Gateway You Want To Use", reply_markup=keyboard)

    # ------------------------ SAVE FILE ------------------------
    fdata = bot.download_file(bot.get_file(message.document.file_id).file_path)
    with open(f"combo{user_id}.txt", "wb") as w:
        w.write(fdata)



#رسائل
def safe_edit_message(chat_id, message_id, text, reply_markup=None, retries=3, delay=1.0):
    for attempt in range(retries):
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup
            )
            return True
        except Exception as e:
            print(f"[safe_edit_message] attempt {attempt+1} failed: {e}")
            time.sleep(delay)
    print("[safe_edit_message] all retries failed, continuing.")
    return False
    
# بوابات
#تشغيل
@bot.callback_query_handler(func=lambda call: call.data =='paypal' or call.data == 'passed' or call.data =='stop' or call.data == 'OTP' or call.data =='Braintree' or call.data =='sq' or call.data =='strip_charge' or call.data=='paypalcom' or call.data=='ppc' or call.data=='ppc001' or call.data=='nppc')
def menu_callback(call):
    user_id = call.from_user.id
    if is_banned(user_id):
    	bot.reply_to(call.from_user.id, "⚠ انت محظور من استخدام البوت")
    	return
#strip
    def my_stripe(call):
	    user_id = call.from_user.id
	    gate = 'Strip Auth'
	    dd ,live,otp,ee= 0,0,0,0
	    
	    if user_id not in stop_flags:
	        stop_flags[user_id] = threading.Event()
	
	    stop_flags[user_id].clear()
	    bot.edit_message_text(
	        chat_id=call.message.chat.id,
	        message_id=call.message.message_id,
	        text="Checking Stripe Card...⌛️"
	    )
	
	    try:
	        with open(f"combo{user_id}.txt", "r") as file:
	            cards = file.readlines()
	            total = len(cards)
	            for cc in cards:
	                if stop_flags[user_id].is_set():
	                    bot.edit_message_text(
	                        chat_id=call.message.chat.id,
	                        message_id=call.message.message_id,
	                        text="STOPPED ⛔"
	                    )
	                    cleanup_user(user_id)
	                    return
	
	                start_time = time.time()
	                try:
	                	last = str(strip_auth(cc))
	                except Exception as e:
	                   	print(e)
	                   	last = "Error in gateway"
	                mes = types.InlineKeyboardMarkup(row_width=1)
	                cm1 = types.InlineKeyboardButton(f"• {cc.strip()} •", callback_data='u8')
	                status = types.InlineKeyboardButton(f"• 𝙎𝙏𝘼𝙏𝙐𝙎 ➜ {last} ", callback_data='u8')
	                cm3 = types.InlineKeyboardButton(f"• Approved ✅➜ {live} •", callback_data='x')
	                cm4 = types.InlineKeyboardButton(f"• Declined ❌ ➜ {dd} ", callback_data='x')
	                cm5 = types.InlineKeyboardButton(f"• OTP ⚠ ➜ {dd} ", callback_data='x')
	                cm7 = types.InlineKeyboardButton(f"• Error ⚠ ➜ {ee} ", callback_data='x')
	                cm6 = types.InlineKeyboardButton(f"• 𝙏𝙊𝙏𝘼𝙇 ➜ {total} ", callback_data='x')
	                stop = types.InlineKeyboardButton("𝙎𝙏𝙊𝙋", callback_data='stop')
	                mes.add(cm1, status, cm3, cm4,cm5, cm6, cm7,stop)
	                end_time = time.time()
	                execution_time = end_time - start_time
	                bot.edit_message_text(
							chat_id=call.message.chat.id,
							message_id=call.message.message_id,
							text=f"Checking cards file... To stop, press Stop button.",
							reply_markup=mes
						)
	                
	                if 'added' in last:
	                	live += 1
	                	try:
	                		data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
	                	except:
	                		data = {}
	                	bank = data.get('bank', {}).get('name', 'unknown')
	                	country_flag = data.get('country', {}).get('emoji', 'unknown')
	                	country = data.get('country', {}).get('name', 'unknown')
	                	brand = data.get('scheme', 'unknown')
	                	card_type = data.get('type', 'unknown')
	                	msg = f'''<b>#Strip_Auth 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
[↯] Card : <code>{cc}</code>
[↯] Gate :{gate}
[↯] Status :  {last} ✅
[↯] Response :  Payment method successfully added ✅
	- - - - - - - - - - - - - - - - - - - - - -
[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
[↯] Bank : {bank}
[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
[↯] Time : {"{:.1f}".format(execution_time)} sec.
[↯] Check By : <a href='https://t.me/{call.from_user.username}'>{call.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
[↯] Dev : <a href='https://t.me/O21211'> R E S H E D</a></b>'''
	                	bot.send_message(call.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
	                elif 'Failed_to_add_3DS' in last:
	                	otp+=1
	                elif 'ERROR_IN_CARD' in last:
	                   dd+=1
	                elif 'ERROR_TOKEN_LOGIN' in last:
	                   ee+=1
	                   fie=f'''
اسف ماكدرت افحص البطاقه بسبب عدم وصولي للمتغيرات ،
خذ البطاقه .
\n
<code>{cc}</code>
	                   '''
	                   bot.send_message(call.from_user.id, fie,parse_mode="html")
	                if 'Error in gateway' in last:
	                  	ee+=1
	                else:
	                	dd += 1
	
	    except Exception as e:
	    	ee+=1
	    	print(e)
	
	
	    bot.edit_message_text(
	        chat_id=call.message.chat.id,
	        message_id=call.message.message_id,
	        text="FINISHED ✅"
	    )
	
	    cleanup_user(user_id)
	

	

#paypal
    def my_paypal(call):
        user_id = call.from_user.id
        gate = 'PayPal Charge'
        dd,live,otp,charg,ccn=0,0,0,0,0
        if user_id not in stop_flags:
        	stop_flags[user_id] = threading.Event()
	
        stop_flags[user_id].clear()
        bot.edit_message_text(
	        chat_id=call.message.chat.id,
	        message_id=call.message.message_id,
	        text="Checking PayPal Card...⌛️"
	    )
	
        try:
             with open(f"combo{user_id}.txt", "r") as file:
                cards = file.readlines()
                total = len(cards)
                for cc in cards:
                     if stop_flags[user_id].is_set():
                         bot.edit_message_text(chat_id=call.message.chat.id,message_id=call.message.message_id,text="STOPPED ⛔")
                         cleanup_user(user_id)
                         return
	
                     try:
                     	data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
                     except:
                     	data = {}

                     bank = data.get('bank', {}).get('name', 'unknown')
                     country_flag = data.get('country', {}).get('emoji', 'unknown')
                     country = data.get('country', {}).get('name', 'unknown')
                     brand = data.get('scheme', 'unknown')
                     card_type = data.get('type', 'unknown')
                     start_time = time.time()
                     try:
                     	last = str(paypal(cc))
                     except Exception as e:
                     	print(e)
                     	last = "ERROR in gateway"
                     mes = types.InlineKeyboardMarkup(row_width=1)
                     cm1 = types.InlineKeyboardButton(f"• {cc.strip()} •", callback_data='u8')
                     status = types.InlineKeyboardButton(f"• 𝙎𝙏𝘼𝙏𝙐𝙎 ➜ {last} ", callback_data='u8')
                     cm7 = types.InlineKeyboardButton(f"• Charge 🔥: {charg} •", callback_data='x')
                     cm3 = types.InlineKeyboardButton(f"• Approved ✅: {live} •", callback_data='x')
                     cm8 = types.InlineKeyboardButton(f"• CCN 🎲 : {ccn}  •", callback_data='x')
                     cm4 = types.InlineKeyboardButton(f"• Declined ❌ : {dd} •", callback_data='x')
                     cm5 = types.InlineKeyboardButton(f"• OTP ⚠ ➜ {otp} •", callback_data='x')
                     cm6 = types.InlineKeyboardButton(f"• 𝙏𝙊𝙏𝘼𝙇 ➜ {total} ", callback_data='x')
                     stop = types.InlineKeyboardButton("𝙎𝙏𝙊𝙋", callback_data='stop')
                     mes.add(cm1, status, cm7,cm3,cm8 ,cm4, cm5, cm6,stop)
                     end_time = time.time()
                     execution_time = end_time - start_time
                     bot.edit_message_text(
							chat_id=call.message.chat.id,
							message_id=call.message.message_id,
							text=f"Checking cards file... To stop, press Stop button.",
							reply_markup=mes
						)
                     msg = f'''<b>#PayPal_Charge 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
[↯] Card : <code>{cc}</code>
[↯] Gate :{gate}
[↯] Status :  {last}
[↯] Response :  {last}
	- - - - - - - - - - - - - - - - - - - - - -
[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
[↯] Bank : {bank}
[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
[↯] Time : {"{:.1f}".format(execution_time)} sec.
[↯] Check By : <a href='https://t.me/{call.from_user.username}'>{call.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
[↯] Dev : @O21211</b>'''
                     if "approved" in last.lower():
                     	live += 1
                     	bot.send_message(call.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
                     if 'INVALID_BILLING_ADDRESS' in last.lower():
                     	live+=1
                     	bot.send_message(call.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
                     elif "otp" in last.lower():
                     	otp += 1
                     elif "'ccn'" in last.lower():
                     	ccn+=1
                     	bot.send_message(call.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
                     elif 'charge'  in last.lower():
                     	charg+=1
                     	bot.send_message(call.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
                     else:
                     	dd += 1
	
        except Exception as e:
        	print(e)
	
	
        bot.edit_message_text(
	        chat_id=call.message.chat.id,
	        message_id=call.message.message_id,
	        text="FINISHED ✅"
	    )
	
        cleanup_user(user_id)



#strip
    #def my_stripe_charge(call):
	
    def my_stripe_charge(call):
	    user_id = call.from_user.id
	    gate = 'Strip_Charge 1€'
	    dd ,charge ,ee = 0,0,0
	
	    if user_id not in stop_flags:
	        stop_flags[user_id] = threading.Event()
	    stop_flags[user_id].clear()
	
	    bot.edit_message_text(
	        chat_id=call.message.chat.id,
	        message_id=call.message.message_id,
	        text="Checking Stripe Charge Card...⌛️"
	    )
	
	    try:
	        with open(f"combo{user_id}.txt", "r") as file:
	            cards = [c.strip() for c in file.readlines()]
	            total = len(cards)
	            futures = {executor.submit(strip_charge, cc): cc for cc in cards}
	
	            for fut in as_completed(futures):
	                cc = futures[fut]
	                if stop_flags[user_id].is_set():
	                    bot.edit_message_text(
	                        chat_id=call.message.chat.id,
	                        message_id=call.message.message_id,
	                        text="STOPPED ⛔"
	                    )
	                    cleanup_user(user_id)
	                    return
	
	                start_time = time.time()
	                try:
	                    last = str(fut.result())
	                except Exception as e:
	                    print(e)
	                    last = "ERROR in gateway"
	
	                # جلب بيانات البطاقة من binlist
	                try:
	                    data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
	                except:
	                    data = {}
	
	                bank = data.get('bank', {}).get('name', 'unknown')
	                country_flag = data.get('country', {}).get('emoji', 'unknown')
	                country = data.get('country', {}).get('name', 'unknown')
	                brand = data.get('scheme', 'unknown')
	                card_type = data.get('type', 'unknown')
	
	                execution_time = time.time() - start_time
	
	                # تحديث Inline Keyboard
	                mes = types.InlineKeyboardMarkup(row_width=1)
	                mes.add(
	                    types.InlineKeyboardButton(f"• {cc} •", callback_data='u8'),
	                    types.InlineKeyboardButton(f"• STATUS ➜ {last}", callback_data='u8'),
	                    types.InlineKeyboardButton(f"• Charge 🎲 : {charge}", callback_data='x'),
	                    types.InlineKeyboardButton(f"• Declined ❌ : {dd}", callback_data='x'),
	                    types.InlineKeyboardButton(f"• Error ⚠ : {ee}", callback_data='x'),
	                    types.InlineKeyboardButton(f"• TOTAL ➜ {total}", callback_data='x'),
	                    types.InlineKeyboardButton("STOP", callback_data='stop')
	                )
	
	                bot.edit_message_text(
	                    chat_id=call.message.chat.id,
	                    message_id=call.message.message_id,
	                    text="Strip Charge 1€",
	                    reply_markup=mes
	                )
	                msg = f'''<b>#Strip_Charge 1€ 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
[↯] Card : <code>{cc}</code>
[↯] Gate :{gate}
[↯] Status :  {last}
	- - - - - - - - - - - - - - - - - - - - - -
[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
[↯] Bank : {bank}
[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
[↯] Check By : <a href='https://t.me/{call.from_user.username}'>{call.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
[↯] Dev : @O21211</b>'''
	                if 'card was declined' in last:
	                    dd += 1
	                elif 'charge' in last:
	                    charge += 1
	                    bot.send_message(call.from_user.id,msg, parse_mode="html", disable_web_page_preview=True)
	                elif 'card number is incorrect.' in last:
	                    dd += 1
	                elif 'ERROR in gateway' in last:
	                    ee += 1
	                else:
	                    ee += 1
	                    print(last)
	
	    except Exception as e:
	        print(e)
	        ee += 1
	
	    bot.edit_message_text(
	        chat_id=call.message.chat.id,
	        message_id=call.message.message_id,
	        text="FINISHED ✅"
	    )
	
	    cleanup_user(user_id)
	





#braintree 10$
    def my_braintree10(call):
        user_id = call.from_user.id
        gate = 'Braintree'
        dd,live,charg,err=0,0,0,0
        if user_id not in stop_flags:
        	stop_flags[user_id] = threading.Event()
	
        stop_flags[user_id].clear()
        bot.edit_message_text(
	        chat_id=call.message.chat.id,
	        message_id=call.message.message_id,
	        text="Checking Braintree Card...⌛️"
	    )
	
        try:
             with open(f"combo{user_id}.txt", "r") as file:
                cards = file.readlines()
                total = len(cards)
                for cc in cards:
                     if stop_flags[user_id].is_set():
                         bot.edit_message_text(chat_id=call.message.chat.id,message_id=call.message.message_id,text="STOPPED ⛔")
                         cleanup_user(user_id)
                         return
	
                     try:
                     	data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
                     except:
                     	data = {}

                     bank = data.get('bank', {}).get('name', 'unknown')
                     country_flag = data.get('country', {}).get('emoji', 'unknown')
                     country = data.get('country', {}).get('name', 'unknown')
                     brand = data.get('scheme', 'unknown')
                     card_type = data.get('type', 'unknown')
                     start_time = time.time()
                     try:
                     	last = str(brintree10(cc))
                     except Exception as e:
                     	print(e)
                     	last = "ERROR in gateway"
                     mes = types.InlineKeyboardMarkup(row_width=1)
                     cm1 = types.InlineKeyboardButton(f"• {cc.strip()} •", callback_data='u8')
                     status = types.InlineKeyboardButton(f"• 𝙎𝙏𝘼𝙏𝙐𝙎 ➜ {last} ", callback_data='u8')
                     cm2 = types.InlineKeyboardButton(f"• Charge 🔥: {charg} •", callback_data='x')
                     cm3 = types.InlineKeyboardButton(f"• Insufficient Funds ✅: {live} •", callback_data='x')
                     cm4 = types.InlineKeyboardButton(f"• Declined ❌ : {dd} •", callback_data='x')
                     cm6= types.InlineKeyboardButton(f"• Error ⚠ : {err} •", callback_data='x')
                     cm5= types.InlineKeyboardButton(f"• 𝙏𝙊𝙏𝘼𝙇 ➜ {total} ", callback_data='x')
                     stop = types.InlineKeyboardButton("𝙎𝙏𝙊𝙋", callback_data='stop')
                     mes.add(cm1, status, cm2,cm3 ,cm4, cm5, cm6,stop)
                     end_time = time.time()
                     execution_time = end_time - start_time
                     bot.edit_message_text(
							chat_id=call.message.chat.id,
							message_id=call.message.message_id,
							text=f"Checking cards file... To stop, press Stop button.",
							reply_markup=mes
						)
                     msg = f'''<b>#Braintree_Charge 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
[↯] Card : <code>{cc}</code>
[↯] Gate :{gate}
[↯] Status :  {last}
[↯] Response :  {last}
	- - - - - - - - - - - - - - - - - - - - - -
[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
[↯] Bank : {bank}
[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
[↯] Time : {"{:.1f}".format(execution_time)} sec.
[↯] Check By : <a href='https://t.me/{call.from_user.username}'>{call.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
[↯] Dev : @O21211</b>'''
                     if 'Insufficient Funds' in last:
                     	live += 1
                     	bot.send_message(call.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
                     elif 'gateway_rejected'  in last:
                     	dd+=1
                     elif 'processor_declined' in last:
                     	dd+=1
                     elif 'ERROR in gateway' in last:
                     	err+=1
                     else:
                     	charg += 1
                     	bot.send_message(call.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
	
        except Exception as e:
        	print(e)
	
	
        bot.edit_message_text(
	        chat_id=call.message.chat.id,
	        message_id=call.message.message_id,
	        text="FINISHED ✅"
	    )
	
        cleanup_user(user_id)



#passed
    def my_passed(call):
        user_id = call.from_user.id
        gate = 'Braintree lookup '
        dd,passed,err,otp=0,0,0,0
        if user_id not in stop_flags:
        	stop_flags[user_id] = threading.Event()
	
        stop_flags[user_id].clear()
        bot.edit_message_text(
	        chat_id=call.message.chat.id,
	        message_id=call.message.message_id,
	        text="Checking Braintree Passed...⌛️"
	    )
	
        try:
             with open(f"combo{user_id}.txt", "r") as file:
                cards = file.readlines()
                total = len(cards)
                for cc in cards:
                     if stop_flags[user_id].is_set():
                         bot.edit_message_text(chat_id=call.message.chat.id,message_id=call.message.message_id,text="STOPPED ⛔")
                         cleanup_user(user_id)
                         return
	
                     try:
                     	data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
                     except:
                     	data = {}

                     bank = data.get('bank', {}).get('name', 'unknown')
                     country_flag = data.get('country', {}).get('emoji', 'unknown')
                     country = data.get('country', {}).get('name', 'unknown')
                     brand = data.get('scheme', 'unknown')
                     card_type = data.get('type', 'unknown')
                     start_time = time.time()
                     try:
                     	last = str(lookups(cc))
                     except Exception as e:
                     	print(e)
                     	last = "ERROR in gateway"
                     mes = types.InlineKeyboardMarkup(row_width=1)
                     cm1 = types.InlineKeyboardButton(f"• {cc.strip()} •", callback_data='u8')
                     status = types.InlineKeyboardButton(f"• 𝙎𝙏𝘼𝙏𝙐𝙎 ➜ {last} ", callback_data='u8')
                     cm2 = types.InlineKeyboardButton(f"• Passex ✅: {passed} •", callback_data='x')
                     cm3 = types.InlineKeyboardButton(f"• OTP 🎲 : {otp} •", callback_data='x')
                     cm4= types.InlineKeyboardButton(f"• Rejection ❌ : {dd} •", callback_data='x')
                     cm6= types.InlineKeyboardButton(f"• Error ⚠ : {err} •", callback_data='x')
                     cm5= types.InlineKeyboardButton(f"• 𝙏𝙊𝙏𝘼𝙇 ➜ {total} ", callback_data='x')
                     stop = types.InlineKeyboardButton("𝙎𝙏𝙊𝙋", callback_data='stop')
                     mes.add(cm1, status, cm2,cm3 ,cm4, cm5, cm6,stop)
                     end_time = time.time()
                     execution_time = end_time - start_time
                     bot.edit_message_text(
							chat_id=call.message.chat.id,
							message_id=call.message.message_id,
							text=f"Checking cards file... To stop, press Stop button.",
							reply_markup=mes
						)
                     passeds = f'''<b>#Braintree_Passed 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
	[↯] Card : <code>{cc}</code>
	[↯] Gate :{gate}
	[↯] Status :  {last} 🎲.
	[↯] Response :  Passed ✅
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
	[↯] Bank : {bank}
	[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Time : {"{:.1f}".format(execution_time)} sec.
	[↯] Check By : <a href='https://t.me/{call.from_user.username}'>{call.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Dev : @O21211 </b>'''
                     if 'authenticate_attempt_successful' in last:
                     	passed += 1
                     	bot.send_message(call.from_user.id, passeds,parse_mode="html",disable_web_page_preview=True)
                     elif 'gateway_rejected'  in last:
                     	err+=1
                     elif 'challenge_required' in last:
                     	otp+=1
                     elif 'ERROR in gateway' in last:
                     	err+=1
                     else:
                     	dd +=1
	
        except Exception as e:
        	print(e)
	
	
        bot.edit_message_text(
	        chat_id=call.message.chat.id,
	        message_id=call.message.message_id,
	        text="FINISHED ✅"
	    )
	
        cleanup_user(user_id)


#otp
    def my_otp(call):
        user_id = call.from_user.id
        gate = 'Braintree lookup '
        dd,passed,err,otp=0,0,0,0
        if user_id not in stop_flags:
        	stop_flags[user_id] = threading.Event()
	
        stop_flags[user_id].clear()
        bot.edit_message_text(
	        chat_id=call.message.chat.id,
	        message_id=call.message.message_id,
	        text="Checking Braintree OTP...⌛️"
	    )
	
        try:
             with open(f"combo{user_id}.txt", "r") as file:
                cards = file.readlines()
                total = len(cards)
                for cc in cards:
                     if stop_flags[user_id].is_set():
                         bot.edit_message_text(chat_id=call.message.chat.id,message_id=call.message.message_id,text="STOPPED ⛔")
                         cleanup_user(user_id)
                         return
	
                     try:
                     	data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
                     except:
                     	data = {}

                     bank = data.get('bank', {}).get('name', 'unknown')
                     country_flag = data.get('country', {}).get('emoji', 'unknown')
                     country = data.get('country', {}).get('name', 'unknown')
                     brand = data.get('scheme', 'unknown')
                     card_type = data.get('type', 'unknown')
                     start_time = time.time()
                     try:
                     	last = str(lookups(cc))
                     except Exception as e:
                     	print(e)
                     	last = "ERROR in gateway"
                     mes = types.InlineKeyboardMarkup(row_width=1)
                     cm1 = types.InlineKeyboardButton(f"• {cc.strip()} •", callback_data='u8')
                     status = types.InlineKeyboardButton(f"• 𝙎𝙏𝘼𝙏𝙐𝙎 ➜ {last} ", callback_data='u8')
                     cm2 =types.InlineKeyboardButton(f"• OTP 🎲 : {otp} •", callback_data='x')
                     cm3 = types.InlineKeyboardButton(f"• Passex ✅: {passed} •", callback_data='x')
                     cm4= types.InlineKeyboardButton(f"• Rejection ❌ : {dd} •", callback_data='x')
                     cm6= types.InlineKeyboardButton(f"• Error ⚠ : {err} •", callback_data='x')
                     cm5= types.InlineKeyboardButton(f"• 𝙏𝙊𝙏𝘼𝙇 ➜ {total} ", callback_data='x')
                     stop = types.InlineKeyboardButton("𝙎𝙏𝙊𝙋", callback_data='stop')
                     mes.add(cm1, status, cm2,cm3 ,cm4, cm5, cm6,stop)
                     end_time = time.time()
                     execution_time = end_time - start_time
                     bot.edit_message_text(
							chat_id=call.message.chat.id,
							message_id=call.message.message_id,
							text=f"Checking cards file... To stop, press Stop button.",
							reply_markup=mes
						)
                     Otps = f'''<b>#Braintree_OTP 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
	[↯] Card : <code>{cc}</code>
	[↯] Gate :{gate}
	[↯] Status :  {last} 🎲.
	[↯] Response :  OTP ✅
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
	[↯] Bank : {bank}
	[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Time : {"{:.1f}".format(execution_time)} sec.
	[↯] Check By : <a href='https://t.me/{call.from_user.username}'>{call.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Dev : @O21211 </b>'''
                     if 'authenticate_attempt_successful' in last:
                     	passed += 1
                     elif 'gateway_rejected'  in last:
                     	err+=1
                     elif 'challenge_required' in last:
                     	otp+=1
                     	bot.send_message(call.from_user.id, Otps,parse_mode="html",disable_web_page_preview=True)
                     elif 'ERROR in gateway' in last:
                     	err+=1
                     else:
                     	dd +=1
	
        except Exception as e:
        	print(e)
	
	
        bot.edit_message_text(
	        chat_id=call.message.chat.id,
	        message_id=call.message.message_id,
	        text="FINISHED ✅"
	    )
	
        cleanup_user(user_id)





	

	
    def my_PayPal_Commerce(call):
	    user_id = call.from_user.id
	    gate = 'PayPal-Commerce'
	    dd, err, charge = 0, 0, 0
	
	    if user_id not in stop_flags:
	        stop_flags[user_id] = threading.Event()
	    stop_flags[user_id].clear()
	
	    bot.edit_message_text(
	        chat_id=call.message.chat.id,
	        message_id=call.message.message_id,
	        text="Checking PayPal-Commerce...⌛️"
	    )
	
	    try:
	        with open(f"combo{user_id}.txt", "r") as file:
	            cards = [c.strip() for c in file.readlines()]
	            total = len(cards)
	            futures = {executor.submit(paypal_Five, cc): cc for cc in cards}
	
	            for fut in as_completed(futures):
	                cc = futures[fut]
	                if stop_flags[user_id].is_set():
	                    bot.edit_message_text(
	                        chat_id=call.message.chat.id,
	                        message_id=call.message.message_id,
	                        text="STOPPED ⛔"
	                    )
	                    cleanup_user(user_id)
	                    return
	
	                start_time = time.time()
	                try:
	                    last = str(fut.result())
	                except Exception as e:
	                    print(e)
	                    last = "ERROR in gateway"
	
	                # جلب بيانات البطاقة من binlist
	                try:
	                    data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
	                except:
	                    data = {}
	
	                bank = data.get('bank', {}).get('name', 'unknown')
	                country_flag = data.get('country', {}).get('emoji', 'unknown')
	                country = data.get('country', {}).get('name', 'unknown')
	                brand = data.get('scheme', 'unknown')
	                card_type = data.get('type', 'unknown')
	
	                execution_time = time.time() - start_time
	
	                # تحديث Inline Keyboard
	                mes = types.InlineKeyboardMarkup(row_width=1)
	                mes.add(
	                    types.InlineKeyboardButton(f"• {cc} •", callback_data='u8'),
	                    types.InlineKeyboardButton(f"• STATUS ➜ {last}", callback_data='u8'),
	                    types.InlineKeyboardButton(f"• Charge 🎲 : {charge}", callback_data='x'),
	                    types.InlineKeyboardButton(f"• Declined ❌ : {dd}", callback_data='x'),
	                    types.InlineKeyboardButton(f"• Error ⚠ : {err}", callback_data='x'),
	                    types.InlineKeyboardButton(f"• TOTAL ➜ {total}", callback_data='x'),
	                    types.InlineKeyboardButton("STOP", callback_data='stop')
	                )
	
	                bot.edit_message_text(
	                    chat_id=call.message.chat.id,
	                    message_id=call.message.message_id,
	                    text="Checking cards file... To stop, press Stop button.",
	                    reply_markup=mes
	                )
	
	                if 'declined_by_processor' in last:
	                    dd += 1
	                elif 'new' in last:
	                    charge += 1
	                    bot.send_message(call.from_user.id, f"Card: {cc} ✅", parse_mode="html", disable_web_page_preview=True)
	                elif 'unknown' in last:
	                    dd += 1
	                elif 'ERROR in gateway' in last:
	                    err += 1
	                else:
	                    dd += 1
	
	    except Exception as e:
	        print(e)
	        err += 1
	
	    bot.edit_message_text(
	        chat_id=call.message.chat.id,
	        message_id=call.message.message_id,
	        text="FINISHED ✅"
	    )
	
	    cleanup_user(user_id)
	

	
#ppc
    def my_ppc(call):
	    user_id = call.from_user.id
	    gate= 'PPC_DONATE 5$'
	    dd, err, charge,CVV,funds = 0, 0, 0,0,0
	    
	    if user_id not in stop_flags:
	        stop_flags[user_id] = threading.Event()
	
	    stop_flags[user_id].clear()
	    bot.edit_message_text(
	        chat_id=call.message.chat.id,
	        message_id=call.message.message_id,
	        text="Checking ppc donate 5$!...⌛️"
	    )
	
	    try:
	        with open(f"combo{user_id}.txt", "r") as file:
	            cards = file.readlines()
	            total = len(cards)
	            for cc in cards:
	                if stop_flags[user_id].is_set():
	                    safe_edit_message(call.message.chat.id, call.message.message_id,
	                        text="STOPPED ⛔"
	                    )
	                    cleanup_user(user_id)
	                    return
	                start_time = time.time()
	                try:
	                	last = str(ppc(cc))
	                except Exception as ees:
	                   	print(ees)
	                execution_time = time.time() - start_time

	                # تحديث Inline Keyboard
	                mes = types.InlineKeyboardMarkup(row_width=1)
	                mes.add(
	                    types.InlineKeyboardButton(f"• {cc} •", callback_data='u8'),
	                    types.InlineKeyboardButton(f"• STATUS ➜ {last}", callback_data='u8'),
	                    types.InlineKeyboardButton(f"• Charge 🎲 : {charge}", callback_data='x'),
	                    types.InlineKeyboardButton(f"• Funds 🎲 : {funds}", callback_data='x'),
	                    types.InlineKeyboardButton(f"• CVV 🎲 : {CVV}", callback_data='x'),
	                    types.InlineKeyboardButton(f"• Declined ❌ : {dd}", callback_data='x'),
	                    types.InlineKeyboardButton(f"• Error ⚠ : {err}", callback_data='x'),
	                    types.InlineKeyboardButton(f"• TOTAL ➜ {total}", callback_data='x'),
	                    types.InlineKeyboardButton("STOP", callback_data='stop')
	                )
	
	                safe_edit_message(call.message.chat.id, call.message.message_id,
                      "Start #ppc_donate 1$ ", reply_markup=mes)
	                blockedbin=f'''
🔹 Blocked bin !!!.
🔹 BIN: {cc[0:6]}
🔹 Info: CREDIT - CLASSIC
🔹 Issuer: BOC CREDIT CARD (INTERNATIONAL), LTD.
🔹 Country: HONG KONG 🇭🇰
🔹 Other: VISA
	                '''
	                msg = f'''<b>#ppc_donate_1$ 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
[↯] Card : <code>{cc}</code>
[↯] Gate :{gate}
[↯] Status :  {last} 🎲.
	- - - - - - - - - - - - - - - - - - - - - -
[↯] Time : {"{:.1f}".format(execution_time)} sec.
[↯] Check By : <a href='https://t.me/{call.from_user.username}'>{call.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Dev : @O21211 </b>'''
	                if 'PAYER_CANNOT_PAY' in last:
	                    dd += 1
	                elif 'DECLINED' in last:
	                    dd+=1
	                elif 'ACCESS_DENIED' in last:
	                	dd+=1 
	                elif 'DECLINED_DUE_TO_UPDATED_ACCOUNT.' in last:
	                	dd+=1
	                elif 'blocked' in last:
	                	err+=1
	                	bot.send_message(call.from_user.id, blockedbin,parse_mode="html",disable_web_page_preview=True)
	                	bot.send_message(ADMIN_ID, f"Fkn info:\nuser: @{call.from_user.username or None}\nid:{call.from_user.id}\n------------------\n{blockedbin}",parse_mode="html",disable_web_page_preview=True)
	                elif 'AMOUNT_EXCEEDED.' in last:
	                	dd+=1
	                elif 'TRANSACTION_NOT_PERMITTED.' in last:
	                	dd+=1
	                elif 'CVV2/CSC does not match.' in last:
	                	dd+=1
	                elif 'TRANSACTION_CANNOT_BE_COMPLETED.' in last:
	                	dd+=1
	                elif "Charge !" in last:
	                	charge+=1
	                	try:
	                		data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
	                	except:
	                		data = {}
	                	bank = data.get('bank', {}).get('name', 'unknown')
	                	country_flag = data.get('country', {}).get('emoji', 'unknown')
	                	country = data.get('country', {}).get('name', 'unknown')
	                	brand = data.get('scheme', 'unknown')
	                	card_type = data.get('type','unknown')
	                	chr = f'''<b>#ppc_donate_5$ 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
[↯] Card : <code>{cc}</code>
[↯] Gate :{gate}
[↯] Status :  {last} 🎲.
	- - - - - - - - - - - - - - - - - - - - - -
[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
[↯] Bank : {bank}
[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
[↯] Time : {"{:.1f}".format(execution_time)} sec.
[↯] Check By : <a href='https://t.me/{call.from_user.username}'>{call.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Dev : @O21211 </b>'''
	                	bot.send_message(call.from_user.id, chr,parse_mode="html",disable_web_page_preview=True)
	                	print(f"{cc} \n {last}")
	                elif 'INSTRUMENT_DECLINED' in last:
	                	dd+=1
	                elif 'AUTHENTICATION_FAILURE' in last:
	                	dd+=1
	                elif 'RATE_LIMIT_REACHED' in last:
	                	dd+=1
	                elif 'RESTRICTED_OR_INACTIVE_ACCOUNT.' in last:
	                	dd+=1
	                elif 'INVALID_OR_RESTRICTED_CARD' in last:
	                	dd+=1
	                elif 'DECLINED_PLEASE_RETRY.' in last:
	                	dd+=1
	                elif 'SUSPECTED_FRAUD.' in last:
	                	dd+=1
	                elif 'ACCOUNT_BLOCKED_BY_ISSUER.' in last:
	                	dd+=1
	                elif 'GENERIC_DECLINE.' in last:
	                	dd+=1
	                elif 'SECURITY_VIOLATION' in last:
	                	dd+=1
	                elif 'INSUFFICIENT_FUNDS.' in last:
	                	funds+=1
	                	try:
	                		data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
	                	except:
	                		data = {}
	                	bank = data.get('bank', {}).get('name', 'unknown')
	                	country_flag = data.get('country', {}).get('emoji', 'unknown')
	                	country = data.get('country', {}).get('name', 'unknown')
	                	brand = data.get('scheme', 'unknown')
	                	card_type = data.get('type','unknown')
	                	fndse = f'''<b>#ppc_donate_5$ 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
[↯] Card : <code>{cc}</code>
[↯] Gate :{gate}
[↯] Status :  {last} 🎲.
	- - - - - - - - - - - - - - - - - - - - - -
[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
[↯] Bank : {bank}
[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
[↯] Time : {"{:.1f}".format(execution_time)} sec.
[↯] Check By : <a href='https://t.me/{call.from_user.username}'>{call.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Dev : @O21211 </b>'''
	                	bot.send_message(call.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
	                elif 'REATTEMPT_NOT_PERMITTED.'  in last:
	                	dd+=1
	                elif 'INVALID_ACCOUNT.'  in last:
	                	dd+=1
	                elif 'ACCOUNT_CLOSED.' in last:
	                	dd+=1
	                elif 'INVALID_TRANSACTION_CARD_ISSUER_ACQUIRER.' in last:
	                	dd+=1
	                elif 'CVV2_FAILURE.' in last:
	                	#send
	                	CVV+=1
	                	bot.send_message(call.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
	                elif 'DO_NOT_HONOR.' in last:
	                	dd+=1
	                elif 'ACCOUNT_NOT_FOUND.' in last:
	                	dd+=1
	                elif 'PAYER_ACTION_REQUIRED' in last:
	                	dd+=1
	                elif 'PICKUP_CARD_SPECIAL_CONDITIONS.' in last:
	                	dd+=1
	                elif 'LOST_OR_STOLEN.' in last:
	                	dd+=1
	                elif 'INVALID_MERCHANT.' in last:
	                	dd+=1
	                elif 'PAYER_ACTION_REQUIRED' in last:
	                	dd+=1
	                elif 'unknown' in last:
	                    dd += 1
	                   
	                elif 'ERROR in gateway' in last:
	                    err += 1
	                else:
	                    dd += 1
	                    

	
	    except Exception as e:
	        print(e)
	        err += 1
	
	    bot.edit_message_text(
	        chat_id=call.message.chat.id,
	        message_id=call.message.message_id,
	        text="FINISHED ✅"
	    )
	
	    cleanup_user(user_id)

#ppc001
    def my_ppc001(call):
	    user_id = call.from_user.id
	    gate = 'PPC_DONATE 5$'
	    dd, err, charge, CVV, funds = 0, 0, 0, 0, 0
	
	    # تأكد من وجود stop flag لكل مستخدم
	    if user_id not in stop_flags:
	        stop_flags[user_id] = threading.Event()
	    stop_flags[user_id].clear()
	
	    # طلب الكمية من المستخدم
	    #bot.send_message(user_id, "دخل السعر الي تريد تفحص علي تذكر لو 0.01 واكبر ليس اقل خوش ؟ ")
	
	    # وظيفة لمعالجة إدخال المستخدم
	    #def process_amount(message):
	        #nonlocal dd, err, charge, CVV, funds  # استخدام نفس المتغيرات داخل الدالة
	       # try:
	            #amount = float(message.text)
	        #except ValueError:
	            #bot.send_message(user_id, "❌ قيمة غير صحيحة. حاول مرة أخرى.")
	           # return bot.register_next_step_handler(message, process_amount)
	
	        # حفظ الكمية في ملف game خاص بالمستخدم
	        #with open(f"game{user_id}.txt", "w") as f:
	            #f.write(str(amount))
	
	        #bot.send_message(user_id, f"تم حفظ الكمية جاري الفحص ✅")
	
	        # قراءة ملف الكروت الخاص بالمستخدم
	    try:
	    	with open(f"combo{user_id}.txt", "r") as file:
	    		cards = file.readlines()
	    		total = len(cards)
	    		for cc in cards:
	    			if stop_flags[user_id].is_set():
	    				bot.edit_message_text(chat_id=call.message.chat.id,message_id=call.message.message_id,text="STOPPED ⛔")
	    				cleanup_user(user_id)
	    				return
	
	    			start_time = time.time()
	    			try:
	    				last = str(ppc001(cc.strip(), ))#str(amount)))
	    			except Exception as ees:
	    				print(ees)
	    				last = "ERROR"
	    				err += 1
	    			execution_time = time.time() - start_time
	    			mes = types.InlineKeyboardMarkup(row_width=1)
	    			mes.add(
	                        types.InlineKeyboardButton(f"• {cc.strip()} •", callback_data='u8'),
	                        types.InlineKeyboardButton(f"• STATUS ➜ {last}", callback_data='u8'),
	                        types.InlineKeyboardButton(f"• Charge 🎲 : {charge}", callback_data='x'),
	                        types.InlineKeyboardButton(f"• Declined ❌ : {dd}", callback_data='x'),
#	                        types.InlineKeyboardButton(f"• Custom  : {amount}", callback_data='x'),
	                        types.InlineKeyboardButton(f"• Error ⚠ : {err}", callback_data='x'),
	                        types.InlineKeyboardButton(f"• TOTAL ➜ {total}", callback_data='x'),
	                        types.InlineKeyboardButton("STOP", callback_data='stop')
	                    )
	
	    			safe_edit_message(call.message.chat.id, call.message.message_id,
	                                      f"Start #ppc_donate", reply_markup=mes)
	
	                    # التعامل مع النتائج
	    			blockedbin = f'''
	🔹 Blocked bin !!!.
	🔹 BIN: {cc[:6]}
	🔹 Info: CREDIT - CLASSIC
	🔹 Issuer: BOC CREDIT CARD (INTERNATIONAL), LTD.
	🔹 Country: HONG KONG 🇭🇰
	🔹 Other: VISA
	                    '''
	    			if '3D_SECURE_REQUIRED' in last:
	    				dd += 1
	    			elif 'Declined by payment processor' in last:
	    				dd += 1
	    			elif 'blocked' in last:
	    				err += 1
	    				bot.send_message(user_id, blockedbin, parse_mode="html", disable_web_page_preview=True)
	    				bot.send_message(ADMIN_ID,
	                                         f"Fkn info:\nuser: @{call.from_user.username or None}\nid:{user_id}\n------------------\n{blockedbin}",parse_mode="html", disable_web_page_preview=True)
	    			elif 'CAPTURE_ORDER_ERROR' in last:
	    				dd += 1
	    			elif 'charge!' in last:
	    				charge += 1
	    				try:
	    					data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
	    				except:
	    					data = {}
	    				bank = data.get('bank', {}).get('name', 'unknown')
	    				country_flag = data.get('country', {}).get('emoji', 'unknown')
	    				country = data.get('country', {}).get('name', 'unknown')
	    				brand = data.get('scheme', 'unknown')
	    				card_type = data.get('type','unknown')
	    				chr_msg = f'''<b>#ppc_donate 🎲
	[↯] Card : <code>{cc}</code>
	[↯] Gate : {gate}
	[↯] Status : {last} 🎲
	[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
	[↯] Bank : {bank}
	[↯] Country : {country} - {country_flag}
	[↯] Time : {"{:.1f}".format(execution_time)} sec.
	[↯] Check By : <a href='https://t.me/{call.from_user.username}'>{call.from_user.username}</a>
	[↯] Dev : @O21211 </b>'''
	    				print(Fore.GREEN+f"{chr_msg}")
	    				bot.send_message(user_id, chr_msg, parse_mode="html", disable_web_page_preview=True)
	    			elif 'ERROR in gateway' in last:
	    				err += 1
	    			elif "No_Accsess_Token" in last:
	    				err+=1
	    			else:
	    				dd += 1
	    				
	    except Exception as e:
	    	print(e)
	    	err += 1
	    	bot.send_message(user_id, "❌ حدث خطأ أثناء قراءة الكروت.")
	
	        # بعد الانتهاء
	    bot.edit_message_text(
	            chat_id=call.message.chat.id,
	            message_id=call.message.message_id,
	            text="FINISHED ✅"
	        )
	    cleanup_user(user_id)
	
	    # تسجيل الخطوة التالية للمستخدم فقط
	    #bot.register_next_step_handler_by_chat_id(user_id, process_amount)

#new ppc

    def my_nppc(call):
	    user_id = call.from_user.id
	    gate = 'PPC_DONATE 1$'
	    dd, err, charge = 0, 0, 0
	    if user_id not in stop_flags:
	        stop_flags[user_id] = threading.Event()
	    stop_flags[user_id].clear()
	    try:
	    	with open(f"combo{user_id}.txt", "r") as file:
	    		cards = file.readlines()
	    		total = len(cards)
	    		for cc in cards:
	    			if stop_flags[user_id].is_set():
	    				bot.edit_message_text(chat_id=call.message.chat.id,message_id=call.message.message_id,text="STOPPED ⛔")
	    				cleanup_user(user_id)
	    				return
	
	    			start_time = time.time()
	    			try:
	    				last = str(ppc2(cc.strip(), ))#str(amount)))
	    			except Exception as ees:
	    				print(ees)
	    				last = "ERROR"
	    				err += 1
	    			execution_time = time.time() - start_time
	    			mes = types.InlineKeyboardMarkup(row_width=1)
	    			mes.add(
	                        types.InlineKeyboardButton(f"• {cc.strip()} •", callback_data='u8'),
	                        types.InlineKeyboardButton(f"• STATUS ➜ {last}", callback_data='u8'),
	                        types.InlineKeyboardButton(f"• Charge 🎲 : {charge}", callback_data='x'),
	                        types.InlineKeyboardButton(f"• Declined ❌ : {dd}", callback_data='x'),
#	                        types.InlineKeyboardButton(f"• Custom  : {amount}", callback_data='x'),
	                        types.InlineKeyboardButton(f"• Error ⚠ : {err}", callback_data='x'),
	                        types.InlineKeyboardButton(f"• TOTAL ➜ {total}", callback_data='x'),
	                        types.InlineKeyboardButton("STOP", callback_data='stop')
	                    )
	
	    			safe_edit_message(call.message.chat.id, call.message.message_id,
	                                      f"Start #ppc_donate", reply_markup=mes)
	
	                    # التعامل مع النتائج
	    			blockedbin = f'''
	🔹 Blocked bin !!!.
	🔹 BIN: {cc[:6]}
	🔹 Info: CREDIT - CLASSIC
	🔹 Issuer: BOC CREDIT CARD (INTERNATIONAL), LTD.
	🔹 Country: HONG KONG 🇭🇰
	🔹 Other: VISA
	                    '''
	    			if '3D_SECURE_REQUIRED' in last:
	    				dd += 1
	    			elif 'blocked' in last:
	    				err += 1
	    				bot.send_message(user_id, blockedbin, parse_mode="html", disable_web_page_preview=True)
	    				bot.send_message(ADMIN_ID,
	                                         f"Fkn info:\nuser: @{call.from_user.username or None}\nid:{user_id}\n------------------\n{blockedbin}",parse_mode="html", disable_web_page_preview=True)
	    			elif 'charge!' in last:
	    				charge += 1
	    				try:
	    					data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
	    				except:
	    					data = {}
	    				bank = data.get('bank', {}).get('name', 'unknown')
	    				country_flag = data.get('country', {}).get('emoji', 'unknown')
	    				country = data.get('country', {}).get('name', 'unknown')
	    				brand = data.get('scheme', 'unknown')
	    				card_type = data.get('type','unknown')
	    				chr_msg = f'''<b>#ppc_donate 🎲
	[↯] Card : <code>{cc}</code>
	[↯] Gate : {gate}
	[↯] Status : {last} 🎲
	[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
	[↯] Bank : {bank}
	[↯] Country : {country} - {country_flag}
	[↯] Time : {"{:.1f}".format(execution_time)} sec.
	[↯] Check By : <a href='https://t.me/{call.from_user.username}'>{call.from_user.username}</a>
	[↯] Dev : @O21211 </b>'''
	    				bot.send_message(user_id, chr_msg, parse_mode="html", disable_web_page_preview=True)
	    			elif 'ERROR in gateway' in last:
	    				err += 1
	    				dd+=1
	    			elif 'Not_Approved' in last:
	    				dd+=1
	    			elif 'Card_Issus' in last:
	    				dd+=1
	    			elif "Not_Charge" in last:
	    				dd+=1
	    			else:
	    				dd += 1
	
	    except Exception as e:
	    	print(e)
	    	err += 1
	    	bot.send_message(user_id, "❌ حدث خطأ أثناء قراءة الكروت.")
	
	        # بعد الانتهاء
	    bot.edit_message_text(
	            chat_id=call.message.chat.id,
	            message_id=call.message.message_id,
	            text="FINISHED ✅"
	        )
	    cleanup_user(user_id)

#system stops and run
    def cleanup_user(user_id):
         if user_id in run_events:
         	run_events[user_id].clear()
         if user_id in stop_flags:
         	stop_flags[user_id].clear()
	
	
	
    if call.data == "paypal":
    	user_id = call.from_user.id
    	if user_id not in run_events:
    		run_events[user_id] = threading.Event()
    	if not run_events[user_id].is_set():
    	    run_events[user_id].set()
    	    stop_flags[user_id] = threading.Event()
    	    threading.Thread(target=my_paypal, args=(call,)).start()
    	    bot.answer_callback_query(call.id, "🚀 PayPal Started")
    	else:
    		bot.answer_callback_query(call.id, "⚠️ شغال بالفعل")

    elif call.data == "strip_charge":
    	user_id = call.from_user.id
    	if user_id not in run_events:
    		run_events[user_id] = threading.Event()
    	if not run_events[user_id].is_set():
    	    run_events[user_id].set()
    	    stop_flags[user_id] = threading.Event()
    	    threading.Thread(target=my_stripe_charge, args=(call,)).start()
    	    bot.answer_callback_query(call.id, "🚀 strip charge Started")
    	else:
    		bot.answer_callback_query(call.id, "⚠️ شغال بالفعل")
    elif call.data == "nppc":
    	user_id = call.from_user.id
    	if user_id not in run_events:
    		run_events[user_id] = threading.Event()
    	if not run_events[user_id].is_set():
    	    run_events[user_id].set()
    	    stop_flags[user_id] = threading.Event()
    	    threading.Thread(target=my_nppc, args=(call,)).start()
    	    bot.answer_callback_query(call.id, "🚀 ppc 1$ Started")
    	else:
    		bot.answer_callback_query(call.id, "⚠️ شغال بالفعل")
    elif call.data == "sq":
    	user_id = call.from_user.id
    	if user_id not in run_events:
    		run_events[user_id] = threading.Event()
    	if not run_events[user_id].is_set():
    	    run_events[user_id].set()
    	    stop_flags[user_id] = threading.Event()
    	    threading.Thread(target=my_stripe, args=(call,)).start()
    	    bot.answer_callback_query(call.id, "🚀 Stripe Started")
    	else:
    		bot.answer_callback_query(call.id, "⚠️ شغال بالفعل")

    elif call.data == "Braintree":
    	user_id = call.from_user.id
    	if user_id not in run_events:
    		run_events[user_id] = threading.Event()
    	if not run_events[user_id].is_set():
    	    run_events[user_id].set()
    	    stop_flags[user_id] = threading.Event()
    	    threading.Thread(target=my_braintree10, args=(call,)).start()
    	    bot.answer_callback_query(call.id, "🚀 Braintree 10$ Started")
    	else:
    		bot.answer_callback_query(call.id, "⚠️ شغال بالفعل")


    elif call.data == "passed":
    	user_id = call.from_user.id
    	if user_id not in run_events:
    		run_events[user_id] = threading.Event()
    	if not run_events[user_id].is_set():
    	    run_events[user_id].set()
    	    stop_flags[user_id] = threading.Event()
    	    threading.Thread(target=my_passed, args=(call,)).start()
    	    bot.answer_callback_query(call.id, "🚀 Braintree Passed Started")
    	else:
    		bot.answer_callback_query(call.id, "⚠️ شغال بالفعل")
    elif call.data == "ppc":
    	user_id = call.from_user.id
    	if user_id not in run_events:
    		run_events[user_id] = threading.Event()
    	if not run_events[user_id].is_set():
    	    run_events[user_id].set()
    	    stop_flags[user_id] = threading.Event()
    	    threading.Thread(target=my_ppc, args=(call,)).start()

    	    bot.answer_callback_query(call.id, "🚀 ppc donate 1$ Started")
    	else:
    		bot.answer_callback_query(call.id, "⚠️ شغال بالفعل")


    elif call.data == "ppc001":
    	user_id = call.from_user.id
    	if user_id not in run_events:
    		run_events[user_id] = threading.Event()
    	if not run_events[user_id].is_set():
    	    run_events[user_id].set()
    	    stop_flags[user_id] = threading.Event()
    	    threading.Thread(target=my_ppc001, args=(call,)).start()

    	    bot.answer_callback_query(call.id, "🚀 ppc donate 1$ Started")
    	else:
    		bot.answer_callback_query(call.id, "⚠️ شغال بالفعل")
    elif call.data == "OTP":
    	user_id = call.from_user.id
    	if user_id not in run_events:
    		run_events[user_id] = threading.Event()
    	if not run_events[user_id].is_set():
    	    run_events[user_id].set()
    	    stop_flags[user_id] = threading.Event()
    	    threading.Thread(target=my_otp, args=(call,)).start()
    	    bot.answer_callback_query(call.id, "🚀 Braintree OTP Started")
    	else:
    		bot.answer_callback_query(call.id, "⚠️ شغال بالفعل")


    elif call.data =="'paypalcom'":
    	user_id = call.from_user.id
    	if user_id not in run_events:
    		run_events[user_id] = threading.Event()
    	if not run_events[user_id].is_set():
    	    run_events[user_id].set()
    	    stop_flags[user_id] = threading.Event()
    	    threading.Thread(target=my_PayPal_Commerce, args=(call,)).start()
    	    bot.answer_callback_query(call.id, "🚀 PayPal Commerce Started")
    	else:
    		bot.answer_callback_query(call.id, "⚠️ شغال بالفعل")
    elif call.data == "stop":
    	user_id = call.from_user.id
    	if user_id in stop_flags:
    	    stop_flags[user_id].set()
    	    bot.answer_callback_query(call.id, "⛔ تم إيقاف العملية")
    	if user_id in run_events:
    		run_events[user_id].clear()



#نهايه البوابات

#زرزر
@bot.callback_query_handler(func=lambda call: call.data == "back_to_start")
def callback(call):
    us = call.from_user.id
    if is_banned(us):
    	bot.reply_to(call.message, "⚠ انت محظور من استخدام البوت")
    	return
    # زر الرجوع للبداية
    if call.data == "back_to_start":
	    def check_join(user_id=call.from_user.id):
	        try:
	            member = bot.get_chat_member(CHANNEL, user_id)
	            return member.status in ["member", "administrator", "creator"]
	        except:
	            return False
	
	    def get_user_plan(user_id):
	        user_id = int(user_id)
	        try:
	            with open("subscriptions.json", "r") as f:
	                data = json.load(f)
	        except:
	            return ("𝗙𝗥𝗘𝗘", None)
	
	        for code, info in data.items():
	            used_by = info.get("used_by", [])
	            if user_id in used_by:
	                return (info.get("plan", "𝗙𝗥𝗘𝗘"), info.get("time", None))
	
	        return ("𝗙𝗥𝗘𝗘", None)
	
	    def joinmaste():
	        uid = call.from_user.id
	        plan, end_time = get_user_plan(uid)
	
	        if not check_join(uid):
	            bot.send_message(uid, f"🚫 يجب عليك الاشتراك أولاً في القناة:\n{CHANNEL}")
	            return
	
	        # FREE USER
	        if plan == "𝗙𝗥𝗘𝗘":
	            try:
	                with open("subscriptions.json", "r") as f:
	                    data = json.load(f)
	            except:
	                data = {}
	
	            data[str(uid)] = {"plan": "𝗙𝗥𝗘𝗘", "timer": "none"}
	
	            with open("subscriptions.json", "w") as f:
	                json.dump(data, f, ensure_ascii=False, indent=4)
	
	            keyboard = types.InlineKeyboardMarkup()
	            cmds_button = types.InlineKeyboardButton("🧩 Commands", callback_data="open_cmds_from_start")
	            owner_button = types.InlineKeyboardButton("✨ 𝗢𝗪𝗡𝗘𝗥 ✨", url="https://t.me/O21211")
	
	            keyboard.add(cmds_button)
	            keyboard.add(owner_button)
	
	            img = open("f.jpg", "rb")
	            media = types.InputMediaPhoto(
	            img,
	            caption=f"Welcome again Mr/Ms <a href='https://t.me/{call.from_user.username}'>{call.from_user.first_name}</a>",
	            parse_mode="HTML"
        )
	            bot.edit_message_media(
                media=media,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
            )

	            return
	
	        # VIP USER
	        keyboard = types.InlineKeyboardMarkup()
	        cmds_button = types.InlineKeyboardButton("🧩 Commands", callback_data="open_cmds_from_start")
	        join_button = types.InlineKeyboardButton("⚠ Dev Bot ⚠", url="https://t.me/O21211")
	
	        keyboard.add(cmds_button)
	        keyboard.add(join_button)
	        img = open("b.jpg", "rb")
	        media = types.InputMediaPhoto(
	            img,
	            caption="Send /cmds To show gate \n or send /cmd to show all comands"
	                    "<b>love from <a href='https://t.me/O21211'>Rashed</a></b>",
	            parse_mode="HTML"
        )
	        bot.edit_message_media(
                media=media,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,reply_markup=keyboard
            )

	
	    threading.Thread(target=joinmaste).start()


@bot.message_handler(commands=['cmd'])
def admin_panel(message):
    user_id = message.from_user.id
    us = message.from_user.id
    if is_banned(us):
        bot.reply_to(message, "⚠ انت محظور من استخدام البوت")
        return

    if user_id == ADMIN_ID:
        msg = f"""
🔐 **لوحة تحكم الأدمن**
** اوامر الادمن **
/add - إضافة مستخدم بالوقت
/remove - إزالة مستخدم وإرجاعه إلى FREE
/ban - حظر مستخدم
/unban - فك الحظر
/redeem - تفعيل كود الاشتراك
/id  معلوماتك

---------------------------------------

** اوامر الدفع **
/sa Strip auth
/bc braintree charge 
/sc strip charge 
/p ppc charge 1$
/pay paypal charge
/chk OTP/PASSED
"""
        bot.reply_to(message, msg, parse_mode="Markdown")
    else:
        freeid = """
** 🎲 Commands 🎲 **
/sa Strip auth
/bc braintree charge 
/sc strip charge 
/p ppc charge 1$
/pay paypal charge
/chk OTP/PASSED
/start بدايه البوت
/redeem - تفعيل كود الاشتراك
/id  معلوماتك
"""
        bot.reply_to(message, freeid, parse_mode="Markdown")



    
@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def callmainmenu(call):
        img = open("b.jpg", "rb")
        media = types.InputMediaPhoto(
            img,
            caption="<b>⚙️ اختر نوع البوابة:</b>",
            parse_mode="HTML"
        )

        try:
            bot.edit_message_media(
                media=media,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=main_menu_keyboard()
            )
        except Exception:
            bot.send_photo(chat_id=call.message.chat.id, photo=img,
                           caption="<b>⚙️ اختر نوع البوابة:</b>",
                           parse_mode="HTML", reply_markup=main_menu_keyboard())
        finally:
            img.close()
        return

@bot.callback_query_handler(func=lambda call: call.data == "open_cmds_from_start")
def callopen_cmds_from_start(call):
        try:
            with open('subscriptions.json', 'r') as file:
                json_data = json.load(file)
        except:
            json_data = {}

        uid = str(call.from_user.id)
        BL = "𝗙𝗥𝗘𝗘"

        for sub_key, info in json_data.items():
            used_by = info.get("used_by", [])
            plan = info.get("plan", "𝗙𝗥𝗘𝗘")
            if uid in map(str, used_by):
                BL = plan

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("commands ⚙️", callback_data="main_menu"),
            types.InlineKeyboardButton("✨ Dev ✨", url="https://t.me/o21211")
        )

        photo = open("g.jpg", "rb")

        try:
            bot.edit_message_media(
                media=types.InputMediaPhoto(
                    photo,
                    caption=f"<b>Welcome <a href='https://t.me/{call.from_user.username}'>{call.from_user.first_name}</a>: {BL}</b>",
                    parse_mode="HTML",
                ),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard
            )
        except Exception:
            bot.send_photo(chat_id=call.message.chat.id, photo=photo,
                           caption=f"<b>Welcome {call.from_user.first_name}: {BL}</b>",
                           parse_mode="HTML", reply_markup=keyboard)
        finally:
            photo.close()
        return

@bot.callback_query_handler(func=lambda call: call.data == "gate_auth")
def callgateauth(call):
        img = open("strip_auth.jpg", "rb")
        media = types.InputMediaPhoto(
            img,
            caption=(
                "\n----------------------------------\n[+] <b>Strip Auth</b>: /sa OR send file 🎲\nGate : On ✅\n----------------------------------"
            ),
            parse_mode="HTML"
        )

        try:
            bot.edit_message_media(
                media=media,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=back_keyboard()
            )
        except Exception:
            bot.send_photo(chat_id=call.message.chat.id, photo=img,
                           caption="[+] Strip Auth: /sa OR send file 🎲\nGate : On ✅",
                           parse_mode="HTML", reply_markup=back_keyboard())
        finally:
            img.close()
        return

@bot.callback_query_handler(func=lambda call: call.data == "gate_charge")
def callgate_charge(call):
        img = open("braintree_charge.jpg", "rb")
        media = types.InputMediaPhoto(
            img,
            caption=(
                "----------------------------------\n[+] <b>Braintree 10$</b>: /bc OR send file 🎲 .\nStatus: On ✅\n----------------------------------\n[+] <b>PayPal</b>: /pay OR send file 🎲 .\nStatus: On ✅\n----------------------------------\n<b>[+] Stripe Charge:</b> /sc OR send file  🎲.\nStatus: On ✅\n----------------------------------"
            ),
            parse_mode="HTML"
        )

        try:
            bot.edit_message_media(
                media=media,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=back_keyboard()
            )
        except Exception:
            bot.send_photo(chat_id=call.message.chat.id, photo=img,
                           caption="[+] Braintree 10$: /bc OR send file 🎲\nStatus: On ✅",
                           parse_mode="HTML", reply_markup=back_keyboard())
        finally:
            img.close()
        return

@bot.callback_query_handler(func=lambda call: call.data == "gate_lookup")
def callgate_lookup(call):
        img = open("lookup.jpg", "rb")
        media = types.InputMediaPhoto(
            img,
            caption=(
                "----------------------------------\n[+] <b>Passed: On ✅\n[+] OTP: On ✅\n[+] Commands :</b> /chk or send file 🎲.\n----------------------------------"
            ),
            parse_mode="HTML"
        )

        try:
            bot.edit_message_media(
                media=media,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=back_keyboard()
            )
        except Exception:
            bot.send_photo(chat_id=call.message.chat.id, photo=img,
                           caption="----------------------------------\n[+] <b>Passed: On ✅\n[+] OTP: On ✅\n[+] Commands :</b> /chk or send file 🎲.\n----------------------------------",parse_mode="HTML", reply_markup=back_keyboard())
        finally:
            img.close()
        return


#يدوي 
#p1$

@bot.message_handler(commands=['p1'])
def cmd_p1(message):
    us = message.from_user.id
    if is_banned(us):
    	bot.reply_to(message, "⚠ انت محظور من استخدام البوت")
    	return
    user_id =message.from_user.id
    if get_user_plan(user_id) == "𝗙𝗥𝗘𝗘":
    	bot.send_message(user_id, "❌ Your subscription is expired or not activated.")
    	return
    start_time = time.time()
    try:
    	cc = message.text.split(maxsplit=1)[1].strip()
    	sent = bot.reply_to(message,"لحظه افحصها")
    except:
    	bot.reply_to(message, "❌ يرجى إدخال البيانات.\nمثال:\n/sa 4512490900362670|09|21|123")
    	return

    gate = "ppc donate 1$"
    try :
    	last =str(ppc001(cc))

    except Exception as e:
    	last='Error in gateway'
    try:
    	data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
    except:
    	data = {}
    bank = data.get('bank', {}).get('name', 'unknown')
    country_flag = data.get('country', {}).get('emoji', 'unknown')
    country = data.get('country', {}).get('name', 'unknown')
    brand = data.get('scheme', 'unknown')
    card_type = data.get('type', 'unknown')
    end_time = time.time()
    execution_time = end_time - start_time
    fun=f'''<b>ppc donate gate 1$ 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
	[↯] Card : <code>{cc}</code>
	[↯] Gate :{gate}
	[↯] Status :  {last} 👇.
	[↯]  Response: limit or insufficient funds. Retry the transaction 72 hours.
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
	[↯] Bank : {bank}
	[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Time : {"{:.1f}".format(execution_time)} sec.
	[↯] Check By : <a href='https://t.me/{message.from_user.username}'>{message.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Dev : @O21211 </b>'''
    msg = f'''<b>ppc donate gate 1$ 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
	[↯] Card : <code>{cc}</code>
	[↯] Gate :{gate} 💸
	[↯] Status :  {last} 🎲.
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
	[↯] Bank : {bank}
	[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Time : {"{:.1f}".format(execution_time)} sec.
	[↯] Check By : <a href='https://t.me/{message.from_user.username}'>{message.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Dev : @O21211 </b>'''
    if "Charge !" in last:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    elif 'INSUFFICIENT_FUNDS.' in last:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, fun,parse_mode="html",disable_web_page_preview=True)
    	#sendx
    elif 'CVV2_FAILURE.' in last:
    	#send
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, fun,parse_mode="html",disable_web_page_preview=True)
    else:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)

#paypal_c

@bot.message_handler(commands=['p'])
def cmd_pay(message):
    us = message.from_user.id
    if is_banned(us):
    	bot.reply_to(message, "⚠ انت محظور من استخدام البوت")
    	return
    user_id =message.from_user.id
    if get_user_plan(user_id) == "𝗙𝗥𝗘𝗘":
    	bot.send_message(user_id, "❌ Your subscription is expired or not activated.")
    	return
    start_time = time.time()
    try:
    	cc = message.text.split(maxsplit=1)[1].strip()
    	sent = bot.reply_to(message,"لحظه افحصها")
    except:
    	bot.reply_to(message, "❌ يرجى إدخال البيانات.\nمثال:\n/sa 4512490900362670|09|21|123")
    	return

    gate = "ppc donate 5$"
    try :
    	last =str(ppc001(cc))

    except Exception as e:
    	last='Error in gateway'
    try:
    	data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
    except:
    	data = {}
    bank = data.get('bank', {}).get('name', 'unknown')
    country_flag = data.get('country', {}).get('emoji', 'unknown')
    country = data.get('country', {}).get('name', 'unknown')
    brand = data.get('scheme', 'unknown')
    card_type = data.get('type', 'unknown')
    end_time = time.time()
    execution_time = end_time - start_time
    fun=f'''<b>ppc donate gate 1$ 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
	[↯] Card : <code>{cc}</code>
	[↯] Gate :{gate}
	[↯] Status :  {last} 👇.
	[↯]  Response: limit or insufficient funds. Retry the transaction 72 hours.
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
	[↯] Bank : {bank}
	[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Time : {"{:.1f}".format(execution_time)} sec.
	[↯] Check By : <a href='https://t.me/{message.from_user.username}'>{message.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Dev : @O21211 </b>'''
    msg = f'''<b>ppc donate gate 1$ 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
	[↯] Card : <code>{cc}</code>
	[↯] Gate :{gate} 💸
	[↯] Status :  {last} 🎲.
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
	[↯] Bank : {bank}
	[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Time : {"{:.1f}".format(execution_time)} sec.
	[↯] Check By : <a href='https://t.me/{message.from_user.username}'>{message.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Dev : @O21211 </b>'''
    if "Charge !" in last:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    elif 'INSUFFICIENT_FUNDS.' in last:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, fun,parse_mode="html",disable_web_page_preview=True)
    	#sendx
    elif 'CVV2_FAILURE.' in last:
    	#send
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, fun,parse_mode="html",disable_web_page_preview=True)
    else:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)


@bot.message_handler(commands=['pay'])
def cmd_pay(message):
    us = message.from_user.id
    if is_banned(us):
    	bot.reply_to(message, "⚠ انت محظور من استخدام البوت")
    	return
    user_id =message.from_user.id
    if get_user_plan(user_id) == "𝗙𝗥𝗘𝗘":
    	bot.send_message(user_id, "❌ Your subscription is expired or not activated.")
    	return
    start_time = time.time()
    try:
    	cc = message.text.split(maxsplit=1)[1].strip()
    	sent = bot.reply_to(message,"لحظه افحصها")
    except:
    	bot.reply_to(message, "❌ يرجى إدخال البيانات.\nمثال:\n/sa 4512490900362670|09|21|123")
    	return

    gate = "PayPal Charge"
    try :
    	last =str(paypal(cc))

    except Exception as e:
    	last='Error in gateway'
    try:
    	data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
    except:
    	data = {}
    bank = data.get('bank', {}).get('name', 'unknown')
    country_flag = data.get('country', {}).get('emoji', 'unknown')
    country = data.get('country', {}).get('name', 'unknown')
    brand = data.get('scheme', 'unknown')
    card_type = data.get('type', 'unknown')
    end_time = time.time()
    execution_time = end_time - start_time
    msg = f'''<b>#PayPal 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
	[↯] Card : <code>{cc}</code>
	[↯] Gate :{gate}
	[↯] Status :  {last}
	[↯] Response :  {last}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
	[↯] Bank : {bank}
	[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Time : {"{:.1f}".format(execution_time)} sec.
	[↯] Check By : <a href='https://t.me/{message.from_user.username}'>{message.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Dev : @O21211 </b>'''

    if "approved" in last.lower():
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    if 'INVALID_BILLING_ADDRESS' in last.lower():
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    elif "otp" in last.lower():
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    elif "'ccn'" in last.lower():
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    elif 'charge'  in last.lower():
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    else:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)

@bot.message_handler(commands=['sa'])
def cmd_st(message):
    us = message.from_user.id
    if is_banned(us):
    	bot.reply_to(message, "⚠ انت محظور من استخدام البوت")
    	return
    user_id =message.from_user.id
    if get_user_plan(user_id) == "𝗙𝗥𝗘𝗘":
    	bot.send_message(user_id, "❌ Your subscription is expired or not activated.")
    	return

    start_time = time.time()
    try:
    	cc = message.text.split(maxsplit=1)[1].strip()
    	sent = bot.reply_to(message,"لحظه افحصها")
    except:
    	bot.reply_to(message, "❌ يرجى إدخال البيانات.\nمثال:\n/sa 4512490900362670|09|21|123")
    	return

    gate = "Strip Auth"
    try :
    	last =str(strip_auth(cc))

    except Exception as e:
    	last='Error in gateway'
    try:
    	data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
    except:
    	data = {}
    bank = data.get('bank', {}).get('name', 'unknown')
    country_flag = data.get('country', {}).get('emoji', 'unknown')
    country = data.get('country', {}).get('name', 'unknown')
    brand = data.get('scheme', 'unknown')
    card_type = data.get('type', 'unknown')
    end_time = time.time()
    execution_time = end_time - start_time
    msg = f'''<b>#Strip_Auth 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
	[↯] Card : <code>{cc}</code>
	[↯] Gate :{gate}
	[↯] Status :  {last} ✅
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
	[↯] Bank : {bank}
	[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Time : {"{:.1f}".format(execution_time)} sec.
	[↯] Check By : <a href='https://t.me/{message.from_user.username}'>{message.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Dev : @O21211 </b>'''

    if 'added' in last:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	msg = f'''<b>#Strip_Auth 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
	[↯] Card : <code>{cc}</code>
	[↯] Gate :{gate}
	[↯] Status :  {last} ✅
	[↯] Response: Payment method successfully added ✅
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
	[↯] Bank : {bank}
	[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Time : {"{:.1f}".format(execution_time)} sec.
	[↯] Check By : <a href='https://t.me/{message.from_user.username}'>{message.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Dev : @O21211 </b>'''
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    elif 'Failed_to_add_3DS' in last:
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    elif 'ERROR_IN_CARD' in last:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    elif 'ERROR_TOKEN_LOGIN' in last:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    if 'Error in gateway' in last:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    else:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    	
@bot.message_handler(commands=['bc'])
def cmd_bc(message):
    us = message.from_user.id
    if is_banned(us):
    	bot.reply_to(message, "⚠ انت محظور من استخدام البوت")
    	return
    user_id =message.from_user.id
    if get_user_plan(user_id) == "𝗙𝗥𝗘𝗘":
    	bot.send_message(user_id, "❌ Your subscription is expired or not activated.")
    	return
    start_time = time.time()
    try:
    	cc = message.text.split(maxsplit=1)[1].strip()
    	sent = bot.reply_to(message,"لحظه افحصها")
    except:
    	bot.reply_to(message, "❌ يرجى إدخال البيانات.\nمثال:\n/sa 4512490900362670|09|21|123")
    	return

    gate = "Braintree Charge"
    try :
    	last =str(brintree10(cc))

    except Exception as e:
    	last='Error in gateway'
    try:
    	data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
    except:
    	data = {}
    bank = data.get('bank', {}).get('name', 'unknown')
    country_flag = data.get('country', {}).get('emoji', 'unknown')
    country = data.get('country', {}).get('name', 'unknown')
    brand = data.get('scheme', 'unknown')
    card_type = data.get('type', 'unknown')
    end_time = time.time()
    execution_time = end_time - start_time
    msg = f'''<b>#Braintree_Charge 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
	[↯] Card : <code>{cc}</code>
	[↯] Gate :{gate}
	[↯] Status :  {last}
	[↯] Response :  {last}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
	[↯] Bank : {bank}
	[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Time : {"{:.1f}".format(execution_time)} sec.
	[↯] Check By : <a href='https://t.me/{message.from_user.username}'>{message.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Dev : @O21211 </b>'''
    if 'Insufficient Funds' in last:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    elif 'gateway_rejected'  in last:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    elif 'processor_declined' in last:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    elif 'ERROR in gateway' in last:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    else:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)

@bot.message_handler(commands=['sc'])
def cmd_charge(message):
    us = message.from_user.id
    if is_banned(us):
    	bot.reply_to(message, "⚠ انت محظور من استخدام البوت")
    	return
    user_id =message.from_user.id
    if get_user_plan(user_id) == "𝗙𝗥𝗘𝗘":
    	bot.send_message(user_id, "❌ Your subscription is expired or not activated.")
    	return
    start_time = time.time()
    try:
    	cc = message.text.split(maxsplit=1)[1].strip()
    	sent = bot.reply_to(message,"لحظه افحصها")
    except:
    	bot.reply_to(message, "❌ يرجى إدخال البيانات.\nمثال:\n/sa 4512490900362670|09|21|123")
    	return

    gate = "Strip Charge"
    try :
    	last =str(strip_charge(cc))

    except Exception as e:
    	last='Error in gateway'
    try:
    	data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
    except:
    	data = {}
    bank = data.get('bank', {}).get('name', 'unknown')
    country_flag = data.get('country', {}).get('emoji', 'unknown')
    country = data.get('country', {}).get('name', 'unknown')
    brand = data.get('scheme', 'unknown')
    card_type = data.get('type', 'unknown')
    end_time = time.time()
    execution_time = end_time - start_time
    msg = f'''<b>#Strip_Charge 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
	[↯] Card : <code>{cc}</code>
	[↯] Gate :{gate}
	[↯] Status :  {last}
	[↯] Response :  {last}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
	[↯] Bank : {bank}
	[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Time : {"{:.1f}".format(execution_time)} sec.
	[↯] Check By : <a href='https://t.me/{message.from_user.username}'>{message.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Dev : @O21211 </b>'''
    if 'charge' in last.lower():
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    elif 'card was declined' in last.lower():
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    elif 'card number is incorrect.' in last.lower():
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    elif 'Error in gateway' in last:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    else:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id,  f"{cc.strip()} | res: {last}")

	


@bot.message_handler(commands=['chk'])
def chks(message):
    us = message.from_user.id
    if is_banned(us):
    	bot.reply_to(message, "⚠ انت محظور من استخدام البوت")
    	return
    user_id =message.from_user.id
    if get_user_plan(user_id) == "𝗙𝗥𝗘𝗘":
    	bot.send_message(user_id, "❌ Your subscription is expired or not activated.")
    	return
    start_time = time.time()
    try:
    	cc = message.text.split(maxsplit=1)[1].strip()
    	sent = bot.reply_to(message,"لحظه افحصها")
    except:
    	bot.reply_to(message, "❌ يرجى إدخال البيانات.\nمثال:\n/sa 4512490900362670|09|21|123")
    	return

    gate = "Braintree Lookup"
    try :
    	last =str(lookups(cc))

    except Exception as e:
    	last='Error in gateway'
    try:
    	data = requests.get('https://lookup.binlist.net/' + cc[:6]).json()
    except:
    	data = {}
    bank = data.get('bank', {}).get('name', 'unknown')
    country_flag = data.get('country', {}).get('emoji', 'unknown')
    country = data.get('country', {}).get('name', 'unknown')
    brand = data.get('scheme', 'unknown')
    card_type = data.get('type', 'unknown')
    end_time = time.time()
    execution_time = end_time - start_time
    passeds = f'''<b>#Braintree_Lookup 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
	[↯] Card : <code>{cc}</code>
	[↯] Gate :{gate}
	[↯] Status :  {last}
	[↯] Response :  Passed ✅
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
	[↯] Bank : {bank}
	[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Time : {"{:.1f}".format(execution_time)} sec.
	[↯] Check By : <a href='https://t.me/{message.from_user.username}'>{message.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Dev : @O21211 </b>'''
    opts = f'''<b>#Braintree_Lookup 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
	[↯] Card : <code>{cc}</code>
	[↯] Gate :{gate}
	[↯] Status :  {last}
	[↯] Response :  OTP 🎲
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
	[↯] Bank : {bank}
	[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Time : {"{:.1f}".format(execution_time)} sec.
	[↯] Check By : <a href='https://t.me/{message.from_user.username}'>{message.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Dev : @O21211 </b>'''
    msg = f'''<b>#Braintree_Lookup 🎲\n- - - - - - - - - - - - - - - - - - - - - -\n
	[↯] Card : <code>{cc}</code>
	[↯] Gate :{gate}
	[↯] Status :  {last}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Bin: <code>{cc[:6]} - {card_type} - {brand}</code>
	[↯] Bank : {bank}
	[↯] Country : {country} - {country_flag}
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Time : {"{:.1f}".format(execution_time)} sec.
	[↯] Check By : <a href='https://t.me/{message.from_user.username}'>{message.from_user.username}</a>
	- - - - - - - - - - - - - - - - - - - - - -
	[↯] Dev : @O21211 </b>'''
    if 'authenticate_attempt_successful' in last.lower():
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, passeds,parse_mode="html",disable_web_page_preview=True)
    elif 'challenge_required' in last.lower():
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, opts,parse_mode="html",disable_web_page_preview=True)
    elif 'Error in gateway' in last:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)
    else:
    	try:
    		bot.delete_message(message.chat.id, sent.message_id)
    	except:
    		pass
    	bot.send_message(message.from_user.id, msg,parse_mode="html",disable_web_page_preview=True)




@bot.message_handler(func=lambda m: m.text and m.text.strip().lower().startswith(("/bin", ".bin")))
def handle_bin_cmd(message):
    us = message.from_user.id
    if is_banned(us):
    	bot.reply_to(message, "⚠ انت محظور من استخدام البوت")
    	return
    user_id =message.from_user.id
    if get_user_plan(user_id) == "𝗙𝗥𝗘𝗘":
    	bot.send_message(user_id, "❌ Your subscription is expired or not activated.")
    	return
    try:
        text = message.text.strip()
        arg = re.sub(r'^\s*(?:/|\\.)bin\s+', '', text, flags=re.IGNORECASE).strip()

        if not arg:
            return bot.reply_to(message, "<b>Usage:</b> /bin 451249", parse_mode="HTML")

        digits = re.sub(r"\D", "", arg)
        if len(digits) < 6:
            return bot.reply_to(message, "<b>أدخل 6 أرقام على الأقل.</b>", parse_mode="HTML")

        bin6 = digits[:6]

        # Call API
        info = get_bin_info(bin6)
        if not info:
            return bot.reply_to(message, "<b>Service Error — Try again later.</b>", parse_mode="HTML")

        # Format line
        info_line = f"{info['scheme'].upper()} - {info['card_type'].upper()} - {info['brand']}"

        # Final message
        reply = (
            "🌩 <b>BIN Lookup</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"[ϟ] <b>BIN:</b> <code>{bin6}</code>\n"
            f"[ϟ] <b>Info:</b> {info_line}\n"
            f"[ϟ] <b>Bank:</b> {info['bank']}\n"
            f"[ϟ] <b>Country:</b> {info['country']} — {info['country_flag']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"[⎇] <b>Req By:</b> {message.from_user.first_name} \n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "[⌤] <b>Dev:</b> <a href='https://t.me/o21211'>Rashed</a> 🍀"
        )

        bot.reply_to(message, reply, parse_mode="HTML", disable_web_page_preview=True)

    except Exception as e:
        print("BIN Error:", e)
        bot.reply_to(message, "<b>⚠ Error occurred.</b>", parse_mode="HTML")




#اكواد
#code
@bot.message_handler(commands=["code"])
def create_code(message):

    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "The owner Only can create a subscription code.", parse_mode="HTML")
        return

    try:
        args = message.text.split(' ')[1:]
        if len(args) < 2:
            bot.reply_to(message, "Please provide the duration in hours and user limit.", parse_mode="HTML")
            return

        hours = int(args[0])
        user_limit = int(args[1])

        characters = string.ascii_uppercase + string.digits
        code = (
            "rashed-" +
            ''.join(secrets.choice(characters) for _ in range(4)) + "-" +
            ''.join(secrets.choice(characters) for _ in range(4)) + "-" +
            ''.join(secrets.choice(characters) for _ in range(4))
        )

        expiry_time = datetime.now() + timedelta(hours=hours)
        expiry_str = expiry_time.strftime('%Y-%m-%d %H:%M')

        new_data = {
            code: {
                "used_by": [],
                "user_limit": user_limit,
                "plan": "𝗩𝗜𝗣",
                "time": expiry_str
            }
        }

        existing_data = load_json_file(SUBSCRIPTION_FILE)
        existing_data.update(new_data)
        save_json_file(SUBSCRIPTION_FILE, existing_data)

        msg = f'''<b>𝗡𝗘𝗪 𝗞𝗘𝗬 𝗖𝗥𝗘𝗔𝗧𝗘𝗗 🚀
        
𝗣𝗟𝗔𝗡 ➜ 𝗩𝗜𝗣
𝗘𝗫𝗣𝗜𝗥𝗘𝗦 𝗜𝗡 ➜ {expiry_str}
𝗞𝗘𝗬 ➜ <code>{code}</code>

𝗨𝗦𝗘 /redeem [𝗞𝗘𝗬]</b>'''
        bot.reply_to(message, msg, parse_mode="HTML")

    except Exception as e:
        logging.error(f"Error creating subscription code: {str(e)}")
        bot.reply_to(message, "Error creating subscription code.", parse_mode="HTML")

@bot.message_handler(commands=["redeem"])
def redeem_code(message):
    us = message.from_user.id
    if is_banned(us):
    	bot.reply_to(message, "⚠ انت محظور من استخدام البوت")
    	return
    try:
        args = message.text.split(' ')
        if len(args) < 2:
            bot.reply_to(message, "Please provide a code to redeem!", parse_mode="HTML")
            return

        code = args[1].strip()
        user_id = str(message.from_user.id)

        db = load_json_file(SUBSCRIPTION_FILE)

        if code not in db:
            bot.reply_to(message, "Invalid code!", parse_mode="HTML")
            return

        sub = db[code]
        expiry_time = datetime.strptime(sub['time'], '%Y-%m-%d %H:%M')

        if datetime.now() >= expiry_time:
            bot.reply_to(message, "Code expired!", parse_mode="HTML")
            return

        used_by = sub.setdefault("used_by", [])
        if int(user_id) in used_by:
            bot.reply_to(message, "You have already activated this subscription!", parse_mode="HTML")
            return

        if len(used_by) >= sub['user_limit']:
            bot.reply_to(message, "User limit reached for this subscription code.", parse_mode="HTML")
            return

        # ------- تسجيل المستخدم كـ VIP في نفس ملف الاشتراكات ------- #
        db[user_id] = {
            "plan": sub["plan"],
            "timer": sub["time"]
        }

        used_by.append(int(user_id))
        save_json_file(SUBSCRIPTION_FILE, db)

        bot.reply_to(message, "Subscription activated!", parse_mode="HTML")

    except Exception as e:
        logging.error(f"Error redeeming code: {str(e)}")
        bot.reply_to(message, "An error occurred while redeeming the code.", parse_mode="HTML")






print("Bot Start On ✅")
def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print("Bot error:", e)
            time.sleep(3)
            print("Restarting bot...")

bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

while True:
    time.sleep(1)