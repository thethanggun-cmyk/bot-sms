def process_deposit(m):
    # Kiểm tra nếu người dùng nhấn nút thay vì nhập số
    if m.text in ["💳 Nạp Tiền", "🛒 Mua Dịch Vụ", "👤 Thông Tin", "⚙️ Quản Lý Admin"]:
        bot.send_message(m.chat.id, "❌ Lệnh bị hủy. Vui lòng nhấn 'Nạp Tiền' và nhập số tiền lại.")
        return

    try:
        # Loại bỏ dấu chấm, dấu phẩy nếu khách nhập (ví dụ 15.000)
        clean_text = m.text.replace(".", "").replace(",", "").strip()
        amt = int(clean_text)
        
        if amt < 15000:
            bot.send_message(m.chat.id, "❌ **Lỗi:** Số tiền nạp tối thiểu là 15,000đ. Vui lòng thử lại!", parse_mode="Markdown")
            return
            
        uid = m.from_user.id
        stk = "04312345"
        bank = "mbv bank" 
        nd = f"NAP{uid}"
        qr = f"https://qr.sepay.vn/img?acc={stk}&bank={bank}&amount={amt}&des={nd}"
        
        txt = (
            f"🏦 **NGÂN HÀNG: OCEANBANK (MBV)**\n"
            f"💳 STK: `{stk}`\n"
            f"💰 Số tiền: `{amt:,}đ`\n"
            f"📝 Nội dung: `{nd}`\n"
            f"━━━━━━━━━━━━━━\n"
            f"⚠️ Lưu ý: Chuyển đúng nội dung để được duyệt auto!"
        )
        
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("✅ XÁC NHẬN ĐÃ CHUYỂN", callback_data=f"conf_{uid}_{amt}"))
        bot.send_photo(m.chat.id, qr, caption=txt, reply_markup=mk, parse_mode="Markdown")
        
    except ValueError:
        bot.send_message(m.chat.id, "❌ **Lỗi:** Vui lòng chỉ nhập số tiền (ví dụ: 15000). không nhập chữ hay ký tự đặc biệt!")
