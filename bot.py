import json
import asyncio
import requests
from datetime import datetime, timezone
from colorama import init, Fore
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIG =================
init(autoreset=True)
TOKEN = "7966232208:AAFQA4sdnz4BhGLfII7Nd8zuYrGzFvULbxM"
URL = "https://dashboard.kingdev.sbs/tool_ug.php?status"
USER_FILE = "user_messages.json"
CHECK_INTERVAL_SECONDS = 300  # 5 phút

# ================= HELPER =================
def load_users():
    try:
        with open(USER_FILE, "r") as f:
            data = json.load(f)
            # Chỉ giữ những entry đúng format
            return {k: v for k, v in data.items() if isinstance(v, dict) and "message_id" in v}
    except:
        return {}

def save_users(users):
    try:
        with open(USER_FILE, "w") as f:
            json.dump(users, f)
    except Exception as e:
        print(Fore.RED + f"⚠ Lỗi lưu user_messages: {e}")

def get_stock_text():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(URL, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return f"❌ Lỗi khi kết nối: {e}"
    except json.JSONDecodeError:
        return f"❌ Lỗi parse JSON!\nServer trả về:\n```{response.text[:200]}...```"

    servers = data.get("servers", {})
    status = data.get("status", "unknown")
    last_updated = data.get("last_updated", datetime.now(timezone.utc).isoformat())

    green = "🟢"
    red = "🔴"

    msg = f"📡 *UGPHONE STOCK STATUS*\n"
    msg += f"**Status:** {status}\n"
    msg += f"**Message:** Hiếu Đẹp Zai\n\n"

    for server, stt in servers.items():
        icon = green if stt != "Out of Stock" else red
        msg += f"{server}: {icon} {stt}\n"

    msg += f"\n🕒 Lần cập nhật cuối: {last_updated}\n♻ Tự động làm mới mỗi 5 phút"
    return msg

# ================= COMMANDS =================
async def getstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    chat_id = str(update.effective_chat.id)
    text = get_stock_text()

    if chat_id in users:
        message_id = users[chat_id].get("message_id")
        if message_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=int(chat_id),
                    message_id=message_id,
                    text=text,
                    parse_mode="Markdown"
                )
                await update.message.reply_text("♻ Đã cập nhật message cũ!")
                return
            except:
                pass

    msg = await update.message.reply_text(text, parse_mode="Markdown")
    users[chat_id] = {"message_id": msg.message_id}
    save_users(users)
    await update.message.reply_text("✔ Bạn sẽ nhận auto cập nhật stock tại tin nhắn này!")

async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    chat_id = str(update.effective_chat.id)
    text = get_stock_text()

    if chat_id in users and users[chat_id].get("message_id"):
        try:
            await context.bot.edit_message_text(
                chat_id=int(chat_id),
                message_id=users[chat_id]["message_id"],
                text=text,
                parse_mode="Markdown"
            )
            await update.message.reply_text("♻ Stock đã được làm mới!")
            return
        except:
            pass

    msg = await update.message.reply_text(text, parse_mode="Markdown")
    users[chat_id] = {"message_id": msg.message_id}
    save_users(users)
    await update.message.reply_text("✔ Stock đã gửi mới!")

# ================= BACKGROUND TASK =================
async def auto_update(app):
    while True:
        users = load_users()
        if users:
            text = get_stock_text()
            for chat_id, info in users.items():
                if not isinstance(info, dict):
                    continue
                message_id = info.get("message_id")
                if message_id:
                    try:
                        await app.bot.edit_message_text(
                            chat_id=int(chat_id),
                            message_id=message_id,
                            text=text,
                            parse_mode="Markdown"
                        )
                        print(Fore.CYAN + f"♻ Updated stock cho {chat_id} lúc {datetime.now().strftime('%H:%M:%S')}")
                    except Exception as e:
                        print(Fore.RED + f"❌ Không edit được cho {chat_id}: {e}")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("getstock_ug", getstock))
    app.add_handler(CommandHandler("refresh", refresh))

    # Gợi ý lệnh khi nhấn "/"
    commands_list = [
        BotCommand("getstock_ug", "Nhận bảng stock và tự động cập nhật"),
        BotCommand("refresh", "Làm mới stock ngay lập tức"),
    ]

    async def post_init(app):
        await app.bot.set_my_commands(commands_list)
        asyncio.create_task(auto_update(app))

    app.post_init = post_init

    print(Fore.GREEN + "🤖 Telegram bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
