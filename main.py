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

# Khởi tạo Flask để giữ Render không tắt bot
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    # Render yêu cầu port từ môi trường
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- [DỮ LIỆU] ---
# (Giữ nguyên các hàm load_data, save_data và logic mua bán như bản trước)
# ... [Phần code logic của bạn] ...

if __name__ == "__main__":
    # Chạy Web Server trước
    keep_alive()
    print("Web Server Started!")
    
    # Khởi tạo Bot
    bot = telebot.TeleBot(TOKEN)
    
    # [Dán toàn bộ các handler @bot.message_handler của bạn vào đây]
    
    # Chạy Bot
    print("Bot is Polling...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
