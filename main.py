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
def home(): return "Gun Store Marketplace is Running"

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
    username = m.from_user.username if m.from_user.username else "nousername"
    if uid not in USERS_DATA:
        USERS_DATA[uid] = {"name": m.from_user.first_name, "username": username.lower(), "money": 0}
        save_data()
    else:
        USERS_DATA[uid]["username"] = username.lower()
        USERS_DATA[uid]["name"] = m.from_user.first_name
    return uid

# --- [MENU CHÍNH - ĐÃ CẬP NHẬT NỘI DUNG CHÀO MỪNG] ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = check_u(message)
    bot.clear_step_handler_by_chat_id(message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛒 Mua Dịch Vụ", "👤 Thông Tin")
    markup.row("💳 Nạp Tiền", "Nhập Key Giftcode 🎁")
    markup.row("Kiếm Tiền Free Để Lấy Otp 🆓")
    
    welcome_msg = (
        "🔥 **SMS ZxC Marketplace**\n"
        "📩 **Thuê Sms Bào App/Tạo Zalo**\n"
        "💬 **Cskh @ZxCMarketplace**\n"
        "🌐 **Bot Uytin Tự Động Auto 24/7🛍️**"
    )
    bot.send_message(message.chat.id, welcome_msg, reply_markup=markup, parse_mode="Markdown")

# --- [LỆNH ADMIN: QUẢN LÝ NGƯỜI DÙNG] ---

@bot.message_handler(commands=['checkuser'])
def check_all_users(m):
    if m.from_user.id != ADMIN_ID: return
    if not USERS_DATA:
        bot.reply_to(m, "📭 Chưa có dữ liệu người dùng.")
        return

    text = "📊 **DANH SÁCH KHÁCH HÀNG**\n\n"
    count = 0
    for uid, info in USERS_DATA.items():
        count += 1
        username = f"@{info.get('username')}" if info.get('username') != "nousername" else "Không có @tag"
        text += f"{count}. {info['name']} | {username}\n"
        text += f"   🆔 ID: `{uid}` | 💰 Ví: `{info['money']:,}đ`\n"
        text += "--------------------------\n"
        if len(text) > 3500:
            bot.send_message(m.chat.id, text, parse_mode="Markdown")
            text = ""
    
    if text: bot.send_message(m.chat.id, text, parse_mode="Markdown")
    bot.send_message(m.chat.id, f"✅ **Tổng cộng:** {count} người dùng.")

@bot.message_handler(commands=['thongbao'])
def broadcast(m):
    if m.from_user.id != ADMIN_ID: return
    content = m.text.replace("/thongbao ", "")
    if not content or content == "/thongbao": return
    success = 0
    for uid in USERS_DATA:
        try:
            bot.send_message(uid, f"🔔 **THÔNG BÁO TỪ HỆ THỐNG**\n\n{content}", parse_mode="Markdown")
            success += 1
        except: pass
    bot.reply_to(m, f"✅ Đã gửi tới {success} người dùng.")

# --- [LỆNH ADMIN: QUẢN LÝ KHO & NHIỆM VỤ] ---

@bot.message_handler(commands=['addfree'])
def set_free_task(m):
    if m.from_user.id != ADMIN_ID: return
    try:
        data = m.text.replace("/addfree ", "").split("|")
        FREE_LINK["name"], FREE_LINK["url"] = data[0].strip(), data[1].strip()
        save_data()
        bot.reply_to(m, "✅ Cập nhật nhiệm vụ thành công!")
    except: bot.reply_to(m, "⚠️ Cú pháp: `/addfree Tên Nút | Link` ")

@bot.message_handler(commands=['add'])
def add_stock(m):
    if m.from_user.id != ADMIN_ID: return
    try:
        args = m.text.split(maxsplit=2)
        loai, danh_sach = args[1].lower(), args[2].split("|")
        if loai in KHO_DICH_VU:
            KHO_DICH_VU[loai].extend(danh_sach); save_data()
            bot.reply_to(m, f"✅ Đã thêm {len(danh_sach)} số vào kho `{loai}`.")
    except: bot.reply_to(m, "⚠️ Cú pháp: `/add [sms_bao/sms_zalo] số1|số2` ")

@bot.message_handler(commands=['taokey'])
def make_key(m):
    if m.from_user.id != ADMIN_ID: return
    try:
        args = m.text.split(); amt, count = int(args[1]), int(args[2])
        res = []
        for _ in range(count):
            k = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            GIFT_KEYS[k] = amt; res.append(f"`{k}`")
        save_data(); bot.reply_to(m, "🎁 **MÃ ĐÃ TẠO:**\n" + "\n".join(res), parse_mode="Markdown")
    except: pass

# --- [PHẦN NẠP TIỀN - OCEANBANK] ---

@bot.message_handler(func=lambda m: m.text == "💳 Nạp Tiền")
def deposit_init(message):
    msg = bot.send_message(message.chat.id, "💰 **Nhập số tiền muốn nạp (Tối thiểu 15k):**")
    bot.register_next_step_handler(msg, process_deposit)

def process_deposit(message):
    try:
        amt = int("".join(filter(str.isdigit, message.text)))
        if amt < 15000:
            bot.send_message(message.chat.id, "❌ Nạp tối thiểu 15,000đ!")
            return
        uid = message.from_user.id
        qr_url = f"https://qr.sepay.vn/img?bank=OceanBank&acc=04312345&amount={amt}&des=NAP{uid}"
        caption = (f"🏦 **MBV BANK (OceanBank)**\n💳 STK: `04312345`\n💰 Tiền: `{amt:,}đ`\n📝 ND: `NAP{uid}`")
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("🏧 Link Qr: Nhấn để lấy mã QR", url=qr_url))
        mk.add(types.InlineKeyboardButton("✅ XÁC NHẬN ĐÃ CHUYỂN", callback_data=f"conf_{uid}_{amt}"))
        bot.send_photo(message.chat.id, qr_url, caption=caption, reply_markup=mk, parse_mode="Markdown")
    except: bot.send_message(message.chat.id, "❌ Vui lòng chỉ nhập số tiền!")

# --- [XỬ LÝ MUA DỊCH VỤ & CALLBACKS] ---

@bot.message_handler(func=lambda m: m.text == "🛒 Mua Dịch Vụ")
def shop(m):
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(f"Sms Bào App (6k) - Kho: {len(KHO_DICH_VU['sms_bao'])}", callback_data="buy_sms_bao"),
           types.InlineKeyboardButton(f"Sms Zalo (10k) - Kho: {len(KHO_DICH_VU['sms_zalo'])}", callback_data="buy_sms_zalo"))
    bot.send_message(m.chat.id, "🛒 **Chọn loại dịch vụ muốn mua:**", reply_markup=mk, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: True)
def handle_all_callbacks(c):
    uid = str(c.from_user.id)
    
    if c.data.startswith("conf_"):
        _, u, a = c.data.split("_")
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("✅ Duyệt", callback_data=f"ok_{u}_{a}"), types.InlineKeyboardButton("❌ Hủy", callback_data=f"no_{u}"))
        bot.send_message(ADMIN_ID, f"🔔 Duyệt nạp {a}đ cho {u}", reply_markup=mk)

    elif c.data.startswith("ok_"):
        _, u, a = c.data.split("_")
        USERS_DATA[u]["money"] += int(a); save_data()
        bot.send_message(u, f"✅ Tài khoản đã cộng `{int(a):,}đ`!", parse_mode="Markdown")
        bot.edit_message_text("✅ Đã duyệt nạp!", c.message.chat.id, c.message.message_id)

    elif c.data.startswith("buy_sms_"):
        loai = c.data.replace("buy_", "")
        gia = 6000 if loai == "sms_bao" else 10000
        if USERS_DATA[uid]["money"] < gia:
            bot.answer_callback_query(c.id, "❌ Bạn không đủ tiền!", show_alert=True); return
        if not KHO_DICH_VU[loai]:
            bot.answer_callback_query(c.id, "❌ Kho đang hết số!", show_alert=True); return
        
        so_dt = KHO_DICH_VU[loai].pop(0); USERS_DATA[uid]["money"] -= gia; save_data()
        bot.edit_message_text(f"✅ **MUA THÀNH CÔNG**\n📱 Số: `{so_dt}`\n⚠️ Chờ Admin trả mã...", c.message.chat.id, c.message.message_id, parse_mode="Markdown")
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("💬 Trả mã", callback_data=f"otp_{uid}_{so_dt}"), 
               types.InlineKeyboardButton("❌ Hoàn tiền", callback_data=f"refund_{uid}_{gia}_{so_dt}"))
        bot.send_message(ADMIN_ID, f"🔔 **ĐƠN MỚI:** {so_dt}", reply_markup=mk, parse_mode="Markdown")

    elif c.data.startswith("otp_"):
        _, u, so = c.data.split("_")
        msg = bot.send_message(ADMIN_ID, f"⌨️ Nhập OTP cho {u}:")
        bot.register_next_step_handler(msg, lambda m: bot.send_message(u, f"📩 **MÃ OTP:** `{m.text}`", parse_mode="Markdown"))

    elif c.data.startswith("refund_"):
        _, u, g, s = c.data.split("_")
        USERS_DATA[u]["money"] += int(g); save_data()
        bot.send_message(u, f"🔄 Hoàn {int(g):,}đ cho số {s}"); bot.edit_message_text("Đã hoàn tiền!", c.message.chat.id, c.message.message_id)

# --- [GIFTCODE & THÔNG TIN] ---

@bot.message_handler(func=lambda m: m.text == "Nhập Key Giftcode 🎁")
def key_start(m):
    msg = bot.send_message(m.chat.id, "🔑 Nhập mã Giftcode:")
    bot.register_next_step_handler(msg, process_key)

def process_key(m):
    k, uid = m.text.strip().upper(), str(m.from_user.id)
    if k in GIFT_KEYS:
        amt = GIFT_KEYS[k]; USERS_DATA[uid]["money"] += amt; del GIFT_KEYS[k]; save_data()
        bot.send_message(m.chat.id, f"✅ Đã nhận {amt:,}đ!")
    else: bot.send_message(m.chat.id, "❌ Mã sai!")

@bot.message_handler(func=lambda m: m.text == "Kiếm Tiền Free Để Lấy Otp 🆓")
def show_free(m):
    mk = types.InlineKeyboardMarkup(); mk.add(types.InlineKeyboardButton(FREE_LINK["name"], url=FREE_LINK["url"]))
    bot.send_message(m.chat.id, "🎁 Làm nhiệm vụ tại đây:", reply_markup=mk)

@bot.message_handler(func=lambda m: m.text == "👤 Thông Tin")
def info(m):
    uid = check_u(m)
    bot.send_message(m.chat.id, f"👤 {USERS_DATA[uid]['name']}\n🆔 ID: `{uid}`\n💰 Ví: `{USERS_DATA[uid]['money']:,}đ`", parse_mode="Markdown")

if __name__ == "__main__":
    Thread(target=lambda: server.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling()
