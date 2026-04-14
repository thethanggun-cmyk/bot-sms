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

# --- [DỮ LIỆU & LƯU TRỮ] ---
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
def home(): return "SMS ZxC Marketplace is Online"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

def check_u(m):
    uid = str(m.from_user.id)
    if uid not in USERS_DATA:
        uname = f"@{m.from_user.username}" if m.from_user.username else m.from_user.first_name
        USERS_DATA[uid] = {"name": uname, "money": 0}
        save_data()
    return uid

# --- [GIAO DIỆN START] ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = check_u(message)
    text = (
        "🔥 **SMS ZxC Marketplace**\n"
        "📩 Thuê Sms Bào App/Tạo Zalo\n"
        "💬 Cskh @ZxCMarketplace\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🌐 Bot Uytin Tự Động Auto 24/7🛍️"
    )
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🛒 Mua Dịch Vụ", "👤 Thông Tin")
    markup.add("💳 Nạp Tiền")
    if int(uid) == ADMIN_ID: markup.add("⚙️ Quản Lý Admin")
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# --- [QUẢN LÝ ADMIN & BROADCAST] ---
@bot.message_handler(func=lambda m: m.text == "⚙️ Quản Lý Admin")
def admin_manage(m):
    if m.from_user.id != ADMIN_ID: return
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("📊 Thống kê User", callback_data="adm_stats"))
    mk.add(types.InlineKeyboardButton("➕ Cộng tiền User", callback_data="adm_addmoney"))
    mk.add(types.InlineKeyboardButton("📢 Thông báo All User", callback_data="adm_broadcast"))
    bot.send_message(m.chat.id, "🛠 **BẢNG ĐIỀU KHIỂN ADMIN**", reply_markup=mk, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "adm_broadcast")
def adm_broadcast_start(c):
    msg = bot.send_message(ADMIN_ID, "📝 **Nhập nội dung muốn thông báo đến TẤT CẢ người dùng:**")
    bot.register_next_step_handler(msg, adm_broadcast_finish)

def adm_broadcast_finish(m):
    content = m.text
    count, fail = 0, 0
    bot.send_message(ADMIN_ID, f"🚀 Đang gửi đến {len(USERS_DATA)} người dùng...")
    for uid in USERS_DATA.keys():
        try:
            bot.send_message(uid, f"🔔 **THÔNG BÁO MỚI**\n\n{content}", parse_mode="Markdown")
            count += 1
            time.sleep(0.05)
        except: fail += 1
    bot.send_message(ADMIN_ID, f"✅ Hoàn tất! Thành công: {count}, Thất bại: {fail}")

# --- [MUA BÁN DỊCH VỤ] ---
@bot.message_handler(func=lambda m: m.text == "🛒 Mua Dịch Vụ")
def shop(m):
    check_u(m)
    text = "🔥 **DANH MỤC DỊCH VỤ ZxC**\n\n1️⃣ Thuê SMS Bào App: `2,000đ`\n2️⃣ Thuê SMS Tạo Zalo: `5,000đ`"
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("Mua SMS Bào App 📩", callback_data="buy_smsbao"),
           types.InlineKeyboardButton("Mua SMS Tạo Zalo 👤", callback_data="buy_smszalo"))
    bot.send_message(m.chat.id, text, reply_markup=mk, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def ask_qty(c):
    loai = c.data.replace("buy_", "")
    msg = bot.send_message(c.message.chat.id, "🔢 **Nhập số lượng muốn mua:**")
    bot.register_next_step_handler(msg, lambda m: finish_buy(m, loai))

def finish_buy(m, loai):
    try:
        qty = int(m.text)
        uid = str(m.from_user.id)
        gia = 2000 if loai == "smsbao" else 5000
        key = "sms_bao" if loai == "smsbao" else "sms_zalo"
        tong = qty * gia
        if USERS_DATA[uid]["money"] < tong:
            bot.send_message(m.chat.id, f"❌ Thiếu {(tong - USERS_DATA[uid]['money']):,}đ"); return
        if len(KHO_DICH_VU[key]) < qty:
            bot.send_message(m.chat.id, "❌ Kho hết số!"); return
        
        items = [KHO_DICH_VU[key].pop(0) for _ in range(qty)]
        USERS_DATA[uid]["money"] -= tong; save_data()
        
        res = f"✅ **MUA THÀNH CÔNG**\n💰 Đã trừ: `{tong:,}đ`\n📱 Số của bạn:\n`" + "\n".join(items) + "`\n\n⚠️ Nhấn nút dưới sau khi đã gửi mã!"
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("📩 ĐÃ GỬI MÃ", callback_data=f"sent_{uid}_{loai}"))
        bot.send_message(m.chat.id, res, reply_markup=mk, parse_mode="Markdown")
    except: bot.send_message(m.chat.id, "❌ Lỗi.")

# --- [XỬ LÝ TRẢ MÃ OTP] ---
@bot.callback_query_handler(func=lambda c: c.data.startswith("sent_"))
def handle_sent(c):
    _, uid, loai = c.data.split("_")
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, 
                         text=c.message.text + "\n\n⏳ **Trạng thái:** Đang chờ Admin trả mã...", parse_mode="Markdown")
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("💬 Trả mã OTP", callback_data=f"reply_{uid}"))
    bot.send_message(ADMIN_ID, f"🔔 **KHÁCH ĐỢI MÃ**\n🆔 ID: `{uid}`\n📦 Loại: {loai.upper()}", reply_markup=mk, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("reply_"))
def admin_reply_start(c):
    target_uid = c.data.split("_")[1]
    msg = bot.send_message(ADMIN_ID, f"⌨️ **Nhập mã OTP/Nội dung cho ID `{target_uid}`:**")
    bot.register_next_step_handler(msg, lambda m: admin_send_otp_to_user(m, target_uid))

def admin_send_otp_to_user(message, target_uid):
    bot.send_message(target_uid, f"📩 **MÃ OTP CỦA BẠN LÀ:**\n\n🔥 ` {message.text} ` 🔥", parse_mode="Markdown")
    bot.send_message(ADMIN_ID, f"✅ Đã trả mã `{message.text}` cho `{target_uid}`")

# --- [NẠP TIỀN & ADD SỐ] ---
@bot.message_handler(commands=['add'])
def add_bulk(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split(maxsplit=2)
        loai = args[1].lower(); danh_sach = args[2].split("|")
        if loai in KHO_DICH_VU:
            KHO_DICH_VU[loai].extend(danh_sach); save_data()
            bot.reply_to(message, f"✅ Đã thêm {len(danh_sach)} số vào {loai}")
    except: bot.reply_to(message, "HD: `/add sms_bao số1|số2`")

@bot.message_handler(func=lambda m: m.text == "💳 Nạp Tiền")
def request_deposit(message):
    msg = bot.send_message(message.chat.id, "💰 Nhập số tiền muốn nạp:")
    bot.register_next_step_handler(msg, process_deposit_step)

def process_deposit_step(message):
    try:
        amount = int(message.text)
        uid = message.from_user.id
        stk = "04312345"; bank = "MBBank"; nd = f"NAP{uid}"
        qr = f"https://qr.sepay.vn/img?acc={stk}&bank={bank}&amount={amount}&des={nd}"
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("✅ XÁC NHẬN", callback_data=f"conf_{uid}_{amount}"))
        bot.send_photo(message.chat.id, qr, caption=f"🏦 **MBBANK**\n💳 **STK:** `{stk}`\n💰 **TIỀN:** `{amount:,}đ`\n📝 **ND:** `{nd}`", reply_markup=mk, parse_mode="Markdown")
    except: bot.send_message(message.chat.id, "❌ Lỗi số tiền.")

@bot.callback_query_handler(func=lambda c: c.data.startswith("conf_"))
def customer_confirm(c):
    _, uid, amt = c.data.split("_")
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("✅ Duyệt", callback_data=f"ok_{uid}_{amt}"), types.InlineKeyboardButton("❌ Hủy", callback_data=f"no_{uid}"))
    bot.send_message(ADMIN_ID, f"🔔 DUYỆT NẠP: {amt}đ cho ID {uid}", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith(("ok_", "no_")))
def admin_action(c):
    data = c.data.split("_"); uid = data[1]
    if data[0] == "ok":
        amt = int(data[2])
        if uid in USERS_DATA:
            USERS_DATA[uid]["money"] += amt; save_data()
            bot.send_message(uid, f"🔔 Nạp thành công {amt:,}đ!"); bot.edit_message_text(f"✅ Duyệt {amt}đ", c.message.chat.id, c.message.message_id)
    else: bot.edit_message_text("❌ Đã hủy", c.message.chat.id, c.message.message_id)

@bot.message_handler(func=lambda m: m.text == "👤 Thông Tin")
def info(m):
    uid = check_u(m)
    bot.send_message(m.chat.id, f"🆔 ID: `{uid}`\n💰 Ví: `{USERS_DATA[uid]['money']:,}đ`", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "adm_stats")
def adm_stats(c):
    res = "📊 **DANH SÁCH USER:**\n"
    for uid, data in USERS_DATA.items():
        res += f"- `{uid}` | {data['name']} | Ví: {data['money']:,}đ\n"
    bot.send_message(ADMIN_ID, res, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "adm_addmoney")
def adm_addmoney_start(c):
    msg = bot.send_message(ADMIN_ID, "Nhập: `ID_SỐTIỀN` (VD: `7652160174_50000`)")
    bot.register_next_step_handler(msg, adm_addmoney_finish)

def adm_addmoney_finish(m):
    try:
        uid, amt = m.text.split("_")
        if uid in USERS_DATA:
            USERS_DATA[uid]["money"] += int(amt); save_data()
            bot.send_message(ADMIN_ID, f"✅ Đã cộng {int(amt):,}đ cho {uid}")
            bot.send_message(uid, f"🔔 Admin đã cộng {int(amt):,}đ vào tài khoản bạn!")
    except: bot.send_message(ADMIN_ID, "❌ Sai cú pháp!")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling()
