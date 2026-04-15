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
            'keys': GIFT_KEYS
        }, f, ensure_ascii=False)

def load_data():
    if os.path.exists('zxc_database.json'):
        try:
            with open('zxc_database.json', 'r') as f:
                d = json.load(f)
                return (d.get('kho', {"sms_bao": [], "sms_zalo": []}), 
                        d.get('users', {}), 
                        d.get('free_link', {"name": "Link Nhiệm Vụ", "url": "https://t.me/ZxCMarketplace"}),
                        d.get('keys', {}))
        except: pass
    return {"sms_bao": [], "sms_zalo": []}, {}, {"name": "Link Nhiệm Vụ", "url": "https://t.me/ZxCMarketplace"}, {}

KHO_DICH_VU, USERS_DATA, FREE_LINK, GIFT_KEYS = load_data()

def check_u(m):
    uid = str(m.from_user.id)
    if uid not in USERS_DATA:
        USERS_DATA[uid] = {"name": m.from_user.first_name, "money": 0}
        save_data()
    return uid

# --- [MENU CHÍNH] ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = check_u(message)
    bot.clear_step_handler_by_chat_id(message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛒 Mua Dịch Vụ", "👤 Thông Tin")
    markup.row("💳 Nạp Tiền", "Nhập Key Giftcode 🎁")
    markup.row("Kiếm Tiền Free Để Lấy Otp 🆓")
    if int(uid) == ADMIN_ID: markup.row("⚙️ Quản Lý Admin")
    bot.send_message(message.chat.id, "🔥 **GUN STORE MARKETPLACE**\n🌐 Thuê SMS tự động 24/7", reply_markup=markup, parse_mode="Markdown")

# --- [ADMIN: THÊM SỐ VÀO KHO] ---
@bot.message_handler(commands=['add'])
def add_stock(m):
    if m.from_user.id != ADMIN_ID: return
    try:
        # Cú pháp: /add sms_bao 09123|09456
        args = m.text.split(maxsplit=2)
        loai = args[1].lower() # sms_bao hoặc sms_zalo
        danh_sach = args[2].split("|")
        
        if loai in KHO_DICH_VU:
            KHO_DICH_VU[loai].extend(danh_sach)
            save_data()
            bot.reply_to(m, f"✅ Đã thêm {len(danh_sach)} số vào kho `{loai}`.")
        else:
            bot.reply_to(m, "❌ Loại không hợp lệ! Dùng: `sms_bao` hoặc `sms_zalo`")
    except:
        bot.reply_to(m, "⚠️ Cú pháp: `/add [sms_bao/sms_zalo] số1|số2|số3`")

# --- [XỬ LÝ MUA DỊCH VỤ] ---
@bot.message_handler(func=lambda m: m.text == "🛒 Mua Dịch Vụ")
def shop(m):
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(f"Sms Bào App (6k) - Kho: {len(KHO_DICH_VU['sms_bao'])}", callback_data="buy_sms_bao"),
           types.InlineKeyboardButton(f"Sms Zalo (10k) - Kho: {len(KHO_DICH_VU['sms_zalo'])}", callback_data="buy_sms_zalo"))
    bot.send_message(m.chat.id, "🛒 **Chọn loại dịch vụ muốn mua:**", reply_markup=mk, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_sms_"))
def process_buy(c):
    uid = str(c.from_user.id)
    loai = c.data.replace("buy_", "") # sms_bao hoặc sms_zalo
    gia = 6000 if loai == "sms_bao" else 10000
    
    if USERS_DATA[uid]["money"] < gia:
        bot.answer_callback_query(c.id, "❌ Bạn không đủ tiền!", show_alert=True)
        return
    
    if not KHO_DICH_VU[loai]:
        bot.answer_callback_query(c.id, "❌ Kho đang hết số, vui lòng quay lại sau!", show_alert=True)
        return

    # Lấy số ra khỏi kho
    so_dt = KHO_DICH_VU[loai].pop(0)
    USERS_DATA[uid]["money"] -= gia
    save_data()
    
    bot.edit_message_text(f"✅ **MUA THÀNH CÔNG**\n💰 Trừ: `{gia:,}đ`\n📱 Số điện thoại: `{so_dt}`\n\n⚠️ Admin đang chờ lấy mã cho bạn...", 
                         c.message.chat.id, c.message.message_id, parse_mode="Markdown")
    
    # Thông báo cho Admin để cấp OTP
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("💬 Trả mã OTP", callback_data=f"otp_{uid}_{so_dt}"),
           types.InlineKeyboardButton("❌ Lỗi (Hoàn tiền)", callback_data=f"refund_{uid}_{gia}_{so_dt}"))
    bot.send_message(ADMIN_ID, f"🔔 **LỆNH MỚI**\n👤 Khách: `{uid}`\n📱 Số: `{so_dt}`\n📦 Loại: `{loai.upper()}`", reply_markup=mk, parse_mode="Markdown")

# --- [ADMIN TRẢ MÃ & HOÀN TIỀN] ---
@bot.callback_query_handler(func=lambda c: c.data.startswith(("otp_", "refund_")))
def handle_otp_refund(c):
    d = c.data.split("_")
    action, uid, info = d[0], d[1], d[2] # info là số đt hoặc giá tiền tùy action
    
    if action == "otp":
        msg = bot.send_message(ADMIN_ID, f"⌨️ Nhập mã OTP cho khách `{uid}` (Số `{info}`):")
        bot.register_next_step_handler(msg, lambda m: bot.send_message(uid, f"📩 **MÃ OTP CỦA BẠN LÀ:**\n\n🔥 `{m.text}` 🔥", parse_mode="Markdown"))
        bot.edit_message_text(f"✅ Đã trả mã cho khách {uid}", c.message.chat.id, c.message.message_id)
        
    elif action == "refund":
        gia = int(d[2])
        so = d[3]
        USERS_DATA[uid]["money"] += gia
        save_data()
        bot.send_message(uid, f"🔄 **HOÀN TIỀN:** Đơn hàng số `{so}` bị lỗi. Đã hoàn `{gia:,}đ` vào ví của bạn.")
        bot.edit_message_text(f"✅ Đã hoàn {gia}đ cho khách {uid}", c.message.chat.id, c.message.message_id)

# --- [PHẦN NẠP TIỀN & QUẢN LÝ ADMIN (GIỮ NGUYÊN)] ---
@bot.message_handler(func=lambda m: m.text == "💳 Nạp Tiền")
def deposit_init(message):
    msg = bot.send_message(message.chat.id, "💰 **Nhập số tiền muốn nạp (Tối thiểu 15k):**")
    bot.register_next_step_handler(msg, process_deposit)

def process_deposit(message):
    try:
        amt = int("".join(filter(str.isdigit, message.text)))
        if amt < 15000: return
        uid = message.from_user.id
        qr = f"https://qr.sepay.vn/img?bank=OceanBank&acc=04312345&amount={amt}&des=NAP{uid}"
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("🏧 Link Qr: Nhấn để lấy mã QR", url=qr))
        mk.add(types.InlineKeyboardButton("✅ XÁC NHẬN ĐÃ CHUYỂN", callback_data=f"conf_{uid}_{amt}"))
        bot.send_photo(message.chat.id, qr, caption=f"🏦 **MBV BANK (OceanBank)**\n💳 STK: `04312345`\n💰 Tiền: `{amt:,}đ`\n📝 ND: `NAP{uid}`", reply_markup=mk, parse_mode="Markdown")
    except: pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("conf_"))
def admin_confirm_dep(c):
    _, uid, amt = c.data.split("_")
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("✅ Duyệt", callback_data=f"ok_{uid}_{amt}"), types.InlineKeyboardButton("❌ Hủy", callback_data=f"no_{uid}"))
    bot.send_message(ADMIN_ID, f"🔔 Duyệt nạp {amt}đ cho {uid}", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith(("ok_", "no_")))
def adm_dep_act(c):
    d = c.data.split("_"); uid = d[1]
    if d[0] == "ok":
        amt = int(d[2]); USERS_DATA[uid]["money"] += amt; save_data()
        bot.send_message(uid, f"✅ Nạp thành công {amt:,}đ!")
    bot.edit_message_text("Xong!", c.message.chat.id, c.message.message_id)

# --- [KEY & FREE LINK] ---
@bot.message_handler(func=lambda m: m.text == "Nhập Key Giftcode 🎁")
def key_start(m):
    msg = bot.send_message(m.chat.id, "🔑 Nhập mã Giftcode:")
    bot.register_next_step_handler(msg, process_key)

def process_key(m):
    k = m.text.strip().upper(); uid = str(m.from_user.id)
    if k in GIFT_KEYS:
        amt = GIFT_KEYS[k]; USERS_DATA[uid]["money"] += amt; del GIFT_KEYS[k]; save_data()
        bot.send_message(m.chat.id, f"✅ Cộng {amt:,}đ thành công!")
    else: bot.send_message(m.chat.id, "❌ Mã sai!")

@bot.message_handler(commands=['taokey'])
def make_key(m):
    if m.from_user.id != ADMIN_ID: return
    args = m.text.split(); amt, count = int(args[1]), int(args[2])
    res = []
    for _ in range(count):
        k = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        GIFT_KEYS[k] = amt; res.append(f"`{k}`")
    save_data(); bot.reply_to(m, "\n".join(res), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "Kiếm Tiền Free Để Lấy Otp 🆓")
def free_link(m):
    mk = types.InlineKeyboardMarkup(); mk.add(types.InlineKeyboardButton(FREE_LINK["name"], url=FREE_LINK["url"]))
    bot.send_message(m.chat.id, "🎁 Làm nhiệm vụ tại đây:", reply_markup=mk)

@bot.message_handler(func=lambda m: m.text == "👤 Thông Tin")
def info(m):
    uid = check_u(m)
    bot.send_message(m.chat.id, f"🆔 ID: `{uid}`\n💰 Ví: `{USERS_DATA[uid]['money']:,}đ`", parse_mode="Markdown")

# --- [KHỞI CHẠY] ---
if __name__ == "__main__":
    Thread(target=lambda: server.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling()
