# ugphone_bot.py
import os
import json
import asyncio
from datetime import datetime
import requests
from colorama import init, Fore
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import nest_asyncio
from keep_alive import keep_alive  # import keep_alive.py

# ================= CONFIG =================
init(autoreset=True)
nest_asyncio.apply()  # fix "event loop already running" trên Replit

TELEGRAM_TOKEN = "7966232208:AAFQA4sdnz4BhGLfII7Nd8zuYrGzFvULbxM"  # Thay token bot của bạn
URL = "https://dashboard.kingdev.sbs/tool_ug.php?status"
MESSAGE_FILE = "stock_message.json"

# ================= HELPER =================
def load_stock_messages():
    """Load message_id cho từng chat từ file JSON"""
    if os.path.exists(MESSAGE_FILE):
        try:
            data = json.load(open(MESSAGE_FILE))
            return {int(k): v for k, v in data.items()}
        except Exception as e:
            print(Fore.RED + f"⚠ Lỗi load stock_messages: {e}")
    return {}

def save_stock_messages(messages):
    """Lưu message_id cho từng chat vào file JSON"""
    with open(MESSAGE_FILE, "w") as f:
        json.dump(messages, f)

def get_stock_text():
    """Lấy dữ liệu stock từ server và trả về text"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(URL, headers=headers, timeout=30)
        response.raise_for_status()
        try:
            data = response.json()
        except json.JSONDecodeError:
            return f"❌ Lỗi khi parse JSON!\nServer trả về:\n{response.text[:200]}..."
    except requests.RequestException as e:
        return f"❌ Lỗi khi kết nối: {e}"

    servers = data.get("servers", {})
    status = data.get("status", "unknown")
    last_updated = data.get("last_updated", "unknown")

    text = f"📡 *UGPHONE STOCK STATUS*\nStatus: `{status}`\nMessage: Hiếu Đẹp Zai\n\n"
    for server, stt in servers.items():
        icon = "🟢" if stt != "Out of Stock" else "🔴"
        text += f"{icon} *{server}*: {stt}\n"

    text += f"\n_Lần cập nhật cuối: {last_updated} • Tự động làm mới mỗi 5 phút_"
    return text

# ================= TELEGRAM BOT =================
stock_messages = load_stock_messages()

async def send_or_edit_stock(chat_id, bot):
    """Gửi hoặc edit message stock cho 1 chat"""
    text = get_stock_text()
    message_id = stock_messages.get(chat_id)
    while True:  # Retry liên tục nếu lỗi
        try:
            if message_id:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                msg = await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
                stock_messages[chat_id] = msg.message_id
                save_stock_messages(stock_messages)
            print(Fore.CYAN + f"♻ Updated stock at {datetime.now().strftime('%H:%M:%S')} in chat {chat_id}")
            break  # thành công thì thoát loop
        except Exception as e:
            print(Fore.RED + f"❌ Lỗi khi gửi/edit stock chat {chat_id}: {e}")
            print(Fore.YELLOW + "♻ Thử lại sau 5 giây...")
            await asyncio.sleep(5)

# Lệnh /refresh
async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await send_or_edit_stock(chat_id, context.bot)
    await update.message.reply_text("♻ Stock đã được làm mới!", quote=True)

# Loop tự động cập nhật stock mỗi 5 phút cho tất cả chat
async def auto_update(bot):
    while True:
        await asyncio.sleep(300)  # 5 phút
        for chat_id in list(stock_messages.keys()):
            try:
                await send_or_edit_stock(chat_id, bot)
            except Exception as e:
                print(Fore.RED + f"❌ Lỗi khi auto update chat {chat_id}: {e}")

# ================= MAIN =================
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("refresh", refresh))

    # Bắt đầu auto update
    asyncio.create_task(auto_update(app.bot))

    # Chạy bot
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.idle()

# ================= RUN =================
if __name__ == "__main__":
    keep_alive()  # giữ bot luôn sống trên Replit
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
