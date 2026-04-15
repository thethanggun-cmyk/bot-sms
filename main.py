import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os
import json
import random
import string

# --- [CẤU HÌNH] ---
TOKEN = '7896835072:AAG9GWVWVJ4BV3t5fCovQCXW8np8uC97gKM'
ADMIN_ID = 7652160174

bot = telebot.TeleBot(TOKEN)
server = Flask('')

@server.route('/')
def home(): return "Gun Store is Live"

# --- [QUẢN LÝ DỮ LIỆU] ---
def save_data():
    with open('zxc_database.json', 'w') as f:
        json.dump({
            'kho': KHO_DICH_VU, 
            'users': USERS_DATA, 
            'free_link': FREE_LINK,
            'keys': GIFT_KEYS # Lưu trữ danh sách key
        }, f, ensure_ascii=False)

def load_data():
    if os.path.exists('zxc_database.json'):
        with open('zxc_database.json', 'r') as f:
            d = json.load(f)
            return (d.get('kho', {"sms_bao": [], "sms_zalo": []}), 
                    d.get('users', {}), 
                    d.get('free_link', {"name": "Link Nhiệm Vụ", "url": "https://t.me/ZxCMarketplace"}),
                    d.get('keys', {})) # key: số_tiền
    return {"sms_bao": [], "sms_zalo": []}, {}, {"name": "Link Nhiệm Vụ", "url": "https://t.me/ZxCMarketplace"}, {}

KHO_DICH_VU, USERS_DATA, FREE_LINK, GIFT_KEYS = load_data()

# --- [LỆNH START & MENU] ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    if uid not in USERS_DATA:
        USERS_DATA[uid] = {"name": message.from_user.first_name, "money": 0}
        save_data()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛒 Mua Dịch Vụ", "👤 Thông Tin")
    markup.row("💳 Nạp Tiền", "Nhập Key Giftcode 🎁") # Thêm nút nhập key
    markup.row("Kiếm Tiền Free Để Lấy Otp 🆓")
    if int(uid) == ADMIN_ID: markup.row("⚙️ Quản Lý Admin")
    
    bot.send_message(message.chat.id, "🔥 **GUN STORE MARKETPLACE**\n🌐 Hệ thống thuê SMS tự động 24/7", reply_markup=markup, parse_mode="Markdown")

# --- [ADMIN: TẠO KEY GIFTCODE] ---
@bot.message_handler(commands=['taokey'])
def create_key(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        # Cú pháp: /taokey [số tiền] [số lượng]
        args = message.text.split()
        amount = int(args[1])
        count = int(args[2])
        
        created_keys = []
        for _ in range(count):
            # Tạo key ngẫu nhiên 8 ký tự
            new_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            GIFT_KEYS[new_key] = amount
            created_keys.append(f"`{new_key}`")
        
        save_data()
        bot.reply_to(message, f"✅ Đã tạo {count} mã Giftcode trị giá {amount:,}đ:\n\n" + "\n".join(created_keys), parse_mode="Markdown")
    except:
        bot.reply_to(message, "⚠️ Cú pháp: `/taokey [số tiền] [số lượng]`")

# --- [XỬ LÝ NHẬP KEY] ---
@bot.message_handler(func=lambda m: m.text == "Nhập Key Giftcode 🎁")
def key_input_start(message):
    msg = bot.send_message(message.chat.id, "🔑 **Vui lòng nhập mã Giftcode của bạn:**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_redeem_key)

def process_redeem_key(message):
    key = message.text.strip().upper()
    uid = str(message.from_user.id)
    
    if key in GIFT_KEYS:
        amount = GIFT_KEYS[key]
        USERS_DATA[uid]["money"] += amount
        del GIFT_KEYS[key] # Xóa key sau khi dùng
        save_data()
        bot.send_message(message.chat.id, f"🎉 **Chúc mừng!**\nBạn đã nhập thành công mã Giftcode và được cộng `{amount:,}đ` vào tài khoản.", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ **Mã Giftcode không tồn tại hoặc đã bị sử dụng.**")

# --- [ADMIN: QUẢN LÝ LINK FREE] ---
@bot.message_handler(commands=['addfree'])
def set_free_link(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        data = message.text.replace("/addfree ", "").split("|")
        FREE_LINK["name"] = data[0].strip()
        FREE_LINK["url"] = data[1].strip()
        save_data()
        bot.reply_to(message, "✅ Đã cập nhật link kiếm tiền free.")
    except:
        bot.reply_to(message, "⚠️ Cú pháp: `/addfree Tên Nút | Link` ")

@bot.message_handler(func=lambda m: m.text == "Kiếm Tiền Free Để Lấy Otp 🆓")
def free_money(m):
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(text=FREE_LINK["name"], url=FREE_LINK["url"]))
    bot.send_message(m.chat.id, "🎁 **Làm nhiệm vụ kiếm tiền miễn phí tại đây:**", reply_markup=mk)

# --- [NẠP TIỀN] ---
@bot.message_handler(func=lambda m: m.text == "💳 Nạp Tiền")
def deposit_init(message):
    msg = bot.send_message(message.chat.id, "💰 **Nhập số tiền muốn nạp (Tối thiểu 15k):**")
    bot.register_next_step_handler(msg, process_deposit)

def process_deposit(message):
    try:
        val = "".join(filter(str.isdigit, message.text))
        amt = int(val)
        if amt < 15000:
            bot.send_message(message.chat.id, "❌ Nạp tối thiểu 15,000đ!")
            return
        uid = message.from_user.id
        qr = f"https://img.vietqr.io/image/MB-04312345-compact2.jpg?amount={amt}&addInfo=NAP{uid}"
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("✅ XÁC NHẬN ĐÃ CHUYỂN", callback_data=f"conf_{uid}_{amt}"))
        bot.send_photo(message.chat.id, qr, caption=f"🏦 **MB BANK**\n💳 STK: `04312345`\n💰 Tiền: `{amt:,}đ`\n📝 ND: `NAP{uid}`", reply_markup=mk, parse_mode="Markdown")
    except: bot.send_message(message.chat.id, "❌ Chỉ nhập số tiền!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("conf_"))
def admin_confirm(c):
    _, uid, amt = c.data.split("_")
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("✅ Duyệt", callback_data=f"ok_{uid}_{amt}"), types.InlineKeyboardButton("❌ Hủy", callback_data=f"no_{uid}"))
    bot.send_message(ADMIN_ID, f"🔔 Duyệt nạp {amt}đ cho ID: {uid}", reply_markup=mk)
    bot.answer_callback_query(c.id, "Đã gửi yêu cầu!")

@bot.callback_query_handler(func=lambda c: c.data.startswith(("ok_", "no_")))
def adm_act(c):
    d = c.data.split("_")
    uid = d[1]
    if d[0] == "ok":
        amt = int(d[2])
        USERS_DATA[uid]["money"] += amt
        save_data()
        bot.send_message(uid, f"✅ Đã nạp thành công {amt:,}đ!")
        bot.edit_message_text(f"✅ Đã duyệt {amt}đ cho {uid}", c.message.chat.id, c.message.message_id)
    else: bot.edit_message_text("❌ Đã hủy nạp", c.message.chat.id, c.message.message_id)

# --- [THÔNG TIN] ---
@bot.message_handler(func=lambda m: m.text == "👤 Thông Tin")
def info(m):
    uid = str(m.from_user.id)
    bot.send_message(m.chat.id, f"👤 Tài khoản: {USERS_DATA[uid]['name']}\n🆔 ID: `{uid}`\n💰 Ví: `{USERS_DATA[uid]['money']:,}đ`", parse_mode="Markdown")

# --- [MUA DỊCH VỤ] ---
@bot.message_handler(func=lambda m: m.text == "🛒 Mua Dịch Vụ")
def shop(m):
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("Sms Bào App (6k)", callback_data="buy_6k"), types.InlineKeyboardButton("Sms Zalo (10k)", callback_data="buy_10k"))
    bot.send_message(m.chat.id, "🛒 Chọn loại dịch vụ:", reply_markup=mk)

# --- [SERVER] ---
def run_f():
    server.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    Thread(target=run_f).start()
    bot.infinity_polling()
