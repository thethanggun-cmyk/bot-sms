import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os
import json
import time

# --- [CẤU HÌNH] ---
TOKEN = '7896835072:AAG9GWVWVJ4BV3t5fCovQCXW8np8uC97gKM'
ADMIN_ID = 7652160174

# --- [DỮ LIỆU] ---
def save_data():
    with open('zxc_database.json', 'w') as f:
        json.dump({'kho': KHO_DICH_VU, 'users': USERS_DATA}, f, ensure_ascii=False)

def load_data():
    if os.path.exists('zxc_database.json'):
        with open('zxc_database.json', 'r') as f:
            data = json.load(f)
            return data.get('kho', {"sms_bao": [], "sms_zalo": []}), data.get('users', {})
    return {"sms_bao": [], "sms_zalo": []}, {}

KHO_DICH_VU, USERS_DATA = load_data()
bot = telebot.TeleBot(TOKEN)
server = Flask('')

@server.route('/')
def home(): return "ZxC Marketplace is Online"

def check_u(m):
    uid = str(m.from_user.id)
    if uid not in USERS_DATA:
        uname = f"@{m.from_user.username}" if m.from_user.username else m.from_user.first_name
        USERS_DATA[uid] = {"name": uname, "money": 0}
        save_data()
    return uid

# --- [1. FIX LỆNH START] ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = check_u(message)
    # Xóa các bước đợi cũ để tránh kẹt lệnh nạp
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    
    text = (
        "🔥 **SMS ZxC Marketplace**\n"
        "📩 Thuê Sms Bào App/Tạo Zalo\n"
        "💬 Cskh @ZxCMarketplace\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🌐 **Bot Uytin Tự Động Auto 24/7** 🛍️"
    )
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🛒 Mua Dịch Vụ", "👤 Thông Tin")
    markup.add("💳 Nạp Tiền")
    if int(uid) == ADMIN_ID: markup.add("⚙️ Quản Lý Admin")
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# --- [2. FIX LỖI NẠP TIỀN] ---
@bot.message_handler(func=lambda m: m.text == "💳 Nạp Tiền")
def deposit_init(message):
    check_u(message)
    # Quan trọng: Xóa các xử lý cũ đang treo trước khi bắt đầu luồng mới
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    
    msg = bot.send_message(message.chat.id, "💰 **Nhập số tiền muốn nạp:**\n⚠️ *Lưu ý: Nạp tối thiểu 15,000đ*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_deposit_step)

def process_deposit_step(message):
    # Nếu khách nhấn nút menu thay vì nhập số, hãy hủy lệnh cũ
    if message.text in ["💳 Nạp Tiền", "🛒 Mua Dịch Vụ", "👤 Thông Tin", "/start"]:
        bot.send_message(message.chat.id, "❌ Lệnh nạp đã hủy. Vui lòng nhập số tiền sau khi nhấn nút!")
        return

    try:
        # Xử lý chuỗi: xóa khoảng trắng, dấu chấm, dấu phẩy
        clean_amt = message.text.replace(".", "").replace(",", "").replace(" ", "").strip()
        amt = int(clean_amt)
        
        if amt < 15000:
            bot.send_message(message.chat.id, "❌ **Lỗi:** Nạp tối thiểu 15,000đ. Vui lòng thử lại!")
            return
            
        uid = message.from_user.id
        stk = "04312345"
        bank = "mbv bank" 
        nd = f"NAP{uid}"
        qr = f"https://qr.sepay.vn/img?acc={stk}&bank={bank}&amount={amt}&des={nd}"
        
        txt = (
            f"🏦 **NGÂN HÀNG: OCEANBANK (MBV)**\n"
            f"💳 STK: `{stk}`\n"
            f"💰 Tiền: `{amt:,}đ`\n"
            f"📝 ND: `{nd}`\n"
            "━━━━━━━━━━━━━━\n"
            "⚠️ Vui lòng chuyển đúng số tiền và nội dung!"
        )
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("✅ XÁC NHẬN ĐÃ CHUYỂN", callback_data=f"conf_{uid}_{amt}"))
        bot.send_photo(message.chat.id, qr, caption=txt, reply_markup=mk, parse_mode="Markdown")
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ **Lỗi:** Vui lòng chỉ nhập số tiền (VD: 20000). Không nhập chữ!")

# --- [GIỮ NGUYÊN CÁC PHẦN CÒN LẠI: MUA BÁN, ADMIN...] ---
# (Hãy đảm bảo bạn copy lại toàn bộ các hàm @bot.callback_query_handler của bản trước vào đây)

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
