import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os
import json
import time

# --- [CẤU HÌNH HỆ THỐNG] ---
TOKEN = '7896835072:AAG9GWVWVJ4BV3t5fCovQCXW8np8uC97gKM'
ADMIN_ID = 7652160174

# --- [KHỞI TẠO BOT & SERVER] ---
bot = telebot.TeleBot(TOKEN)
server = Flask('')

@server.route('/')
def home():
    return "ZxC SMS Marketplace is Online"

# --- [QUẢN LÝ DỮ LIỆU] ---
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

def check_u(m):
    uid = str(m.from_user.id)
    if uid not in USERS_DATA:
        uname = f"@{m.from_user.username}" if m.from_user.username else m.from_user.first_name
        USERS_DATA[uid] = {"name": uname, "money": 0}
        save_data()
    return uid

# --- [LỆNH START & MENU] ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = check_u(message)
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

# --- [XỬ LÝ MUA DỊCH VỤ] ---
@bot.message_handler(func=lambda m: m.text == "🛒 Mua Dịch Vụ")
def shop(m):
    check_u(m)
    text = "🔥 **DANH MỤC DỊCH VỤ ZxC**\n\n1️⃣ Sms Bào App ( All ): `6,000đ`\n2️⃣ Sms Tạo Zalo: `10,000đ`"
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("Sms Bào App ( All ) 📩", callback_data="buy_smsbao"),
           types.InlineKeyboardButton("Sms Tạo Zalo 👤", callback_data="buy_smszalo"))
    bot.send_message(m.chat.id, text, reply_markup=mk, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def auto_buy(c):
    loai = c.data.replace("buy_", "")
    uid = str(c.from_user.id)
    gia = 6000 if loai == "smsbao" else 10000
    key = "sms_bao" if loai == "smsbao" else "sms_zalo"
    
    if USERS_DATA[uid]["money"] < gia:
        bot.answer_callback_query(c.id, "❌ Ví không đủ tiền!", show_alert=True); return
    if len(KHO_DICH_VU[key]) < 1:
        bot.answer_callback_query(c.id, "❌ Kho đang hết số!", show_alert=True); return

    so_dt = KHO_DICH_VU[key].pop(0)
    USERS_DATA[uid]["money"] -= gia
    save_data()
    
    bot.delete_message(c.message.chat.id, c.message.message_id)
    res = f"✅ **MUA THÀNH CÔNG**\n💰 Trừ: `{gia:,}đ`\n📱 Số của bạn: `{so_dt}`\n\n⚠️ Vui lòng nhấn nút dưới khi app đã gửi mã!"
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("📩 ĐÃ GỬI MÃ (XÁC NHẬN)", callback_data=f"sent_{uid}_{loai}_{gia}_{so_dt}"))
    bot.send_message(c.message.chat.id, res, reply_markup=mk, parse_mode="Markdown")

# --- [XỬ LÝ LỆNH CHO ADMIN] ---
@bot.callback_query_handler(func=lambda c: c.data.startswith("sent_"))
def handle_sent(c):
    _, uid, loai, gia, so = c.data.split("_")
    bot.edit_message_text(f"📱 Số: `{so}`\n⏳ **Trạng thái:** Chờ Admin check mã...", 
                         c.message.chat.id, c.message.message_id, parse_mode="Markdown")
    
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("💬 TRẢ MÃ OTP", callback_data=f"adm_otp_{uid}_{so}"))
    mk.add(types.InlineKeyboardButton("❌ KHÔNG THẤY MÃ (HOÀN TIỀN)", callback_data=f"adm_refund_{uid}_{gia}_{so}"))
    bot.send_message(ADMIN_ID, f"🔔 **LỆNH XỬ LÝ SMS**\n👤 Khách: `{uid}`\n📱 Số: `{so}`\n📦 Loại: {loai.upper()}", reply_markup=mk, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_otp_"))
def admin_otp_start(c):
    _, _, uid, so = c.data.split("_")
    msg = bot.send_message(ADMIN_ID, f"⌨️ **Nhập mã OTP cho số `{so}`:**")
    bot.register_next_step_handler(msg, lambda m: admin_send_otp(m, uid, so))

def admin_send_otp(m, uid, so):
    otp = m.text
    bot.send_message(uid, f"📩 **MÃ OTP CHO SỐ `{so}` LÀ:**\n\n🔥 ` {otp} ` 🔥", parse_mode="Markdown")
    bot.send_message(ADMIN_ID, f"✅ Đã trả mã `{otp}` cho số `{so}`")

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_refund_"))
def admin_refund_action(c):
    _, _, uid, gia, so = c.data.split("_")
    if uid in USERS_DATA:
        USERS_DATA[uid]["money"] += int(gia)
        save_data()
        bot.send_message(uid, f"🔄 **HOÀN TIỀN**\nAdmin báo không thấy mã cho số `{so}`.\n💰 Đã cộng lại `{int(gia):,}đ` vào ví của bạn.")
        bot.edit_message_text(f"✅ Đã hoàn {int(gia):,}đ cho ID {uid} (Số {so})", c.message.chat.id, c.message.message_id)

# --- [XỬ LÝ NẠP TIỀN] ---
@bot.message_handler(func=lambda m: m.text == "💳 Nạp Tiền")
def deposit_init(message):
    check_u(message)
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    msg = bot.send_message(message.chat.id, "💰 **Nhập số tiền muốn nạp:**\n⚠️ *Lưu ý: Nạp tối thiểu 15,000đ*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_deposit_step)

def process_deposit_step(message):
    if message.text in ["💳 Nạp Tiền", "🛒 Mua Dịch Vụ", "👤 Thông Tin", "/start", "⚙️ Quản Lý Admin"]:
        bot.send_message(message.chat.id, "❌ Lệnh nạp đã bị hủy.")
        return
    try:
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
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("✅ XÁC NHẬN ĐÃ CHUYỂN", callback_data=f"conf_{uid}_{amt}"))
        bot.send_photo(message.chat.id, qr, caption=f"🏦 **OCEANBANK (MBV)**\n💳 STK: `{stk}`\n💰 Tiền: `{amt:,}đ`\n📝 ND: `{nd}`", reply_markup=mk, parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ **Lỗi:** Vui lòng chỉ nhập số tiền!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("conf_"))
def conf_dep(c):
    _, uid, amt = c.data.split("_")
    bot.answer_callback_query(c.id, "Đã gửi lệnh duyệt cho Admin!")
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("✅ Duyệt", callback_data=f"ok_{uid}_{amt}"), types.InlineKeyboardButton("❌ Hủy", callback_data=f"no_{uid}"))
    bot.send_message(ADMIN_ID, f"🔔 DUYỆT NẠP: {amt}đ cho {uid}", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith(("ok_", "no_")))
def adm_dep_act(c):
    d = c.data.split("_"); uid = d[1]
    if d[0] == "ok":
        amt = int(d[2])
        if uid in USERS_DATA:
            USERS_DATA[uid]["money"] += amt; save_data()
            bot.send_message(uid, f"🔔 Đã nạp thành công {amt:,}đ vào ví!"); bot.edit_message_text(f"✅ Xong {amt}đ", c.message.chat.id, c.message.message_id)
    else: bot.edit_message_text("❌ Hủy nạp", c.message.chat.id, c.message.message_id)

# --- [QUẢN LÝ ADMIN] ---
@bot.message_handler(commands=['add'])
def add_s(m):
    if m.from_user.id != ADMIN_ID: return
    try:
        a = m.text.split(maxsplit=2); l = a[1].lower(); ds = a[2].split("|")
        if l in KHO_DICH_VU: KHO_DICH_VU[l].extend(ds); save_data(); bot.reply_to(m, f"✅ Đã thêm {len(ds)} số.")
    except: bot.reply_to(m, "/add sms_bao số1|số2")

@bot.message_handler(func=lambda m: m.text == "⚙️ Quản Lý Admin")
def admin_manage(m):
    if m.from_user.id != ADMIN_ID: return
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("📊 Thống kê", callback_data="adm_stats"),
           types.InlineKeyboardButton("📢 Thông báo", callback_data="adm_broadcast"))
    bot.send_message(m.chat.id, "🛠 **BẢNG ĐIỀU KHIỂN ADMIN**", reply_markup=mk, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "adm_stats")
def adm_stats(c):
    res = f"📊 **KHO:** {len(KHO_DICH_VU['sms_bao'])} Bào | {len(KHO_DICH_VU['sms_zalo'])} Zalo\n👤 **USER:** {len(USERS_DATA)} người."
    bot.send_message(ADMIN_ID, res, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "👤 Thông Tin")
def info(m):
    u = check_u(m)
    bot.send_message(m.chat.id, f"🆔 ID: `{u}`\n💰 Ví: `{USERS_DATA[u]['money']:,}đ`", parse_mode="Markdown")

# --- [KHỞI CHẠY HỆ THỐNG] ---
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("✅ Web Server & Bot đã sẵn sàng!")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
