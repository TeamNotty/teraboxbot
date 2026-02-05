from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

from config import API_ID, API_HASH, BOT_TOKEN, TERABOX_KEY, ADMIN_ID
from database import (
    can_download,
    increase_usage,
    add_served_user,
    get_daily_limit,
    set_daily_limit,
    is_premium
)

bot = Client("TeraboxBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

CACHE = {}


# Tiny Font Function
def tiny(text):
    return f"<small>{text}</small>"


# Terabox API Fetch
def fetch_terabox(url):
    api_url = "https://xapiverse.com/api/terabox"
    payload = {"url": url}
    headers = {
        "Content-Type": "application/json",
        "xAPIverse-Key": TERABOX_KEY
    }
    r = requests.post(api_url, json=payload, headers=headers)
    return r.json()


# Start Command
@bot.on_message(filters.command("start"))
async def start(_, msg):
    await add_served_user(msg.from_user.id)

    await msg.reply_text(
        tiny("👋 Welcome to Terabox Downloader Bot\n\nSend Terabox Link 🚀"),
        parse_mode="html"
    )


# Admin Change Daily Limit
@bot.on_message(filters.command("setlimit") & filters.user(ADMIN_ID))
async def setlimit(_, msg):
    if len(msg.command) < 3:
        return await msg.reply_text(
            "Usage: /setlimit normal premium"
        )

    normal = int(msg.command[1])
    premium = int(msg.command[2])

    await set_daily_limit(normal, premium)
    await msg.reply_text(
        tiny(f"✅ Daily Limits Updated\nNormal: {normal}\nPremium: {premium}"),
        parse_mode="html"
    )


# Handle Terabox Links
@bot.on_message(filters.regex("terabox.com|1024terabox.com"))
async def terabox_handler(_, msg):
    user_id = msg.from_user.id

    if not await can_download(user_id):
        return await msg.reply_text(
            tiny("❌ Daily Limit Reached!\nCome Back Tomorrow 🚀"),
            parse_mode="html"
        )

    await increase_usage(user_id)

    m = await msg.reply_text(tiny("⏳ Fetching Files..."), parse_mode="html")

    data = fetch_terabox(msg.text.strip())

    if data.get("status") != "success":
        return await m.edit(tiny("❌ Failed to fetch link"), parse_mode="html")

    file = data["list"][0]
    file_id = str(file["fs_id"])
    CACHE[file_id] = file

    name = file["name"]
    size = file["size_formatted"]

    caption = tiny(
        f"📂 File Found!\n\n🎬 {name}\n📦 Size: {size}\n\nChoose Option 👇"
    )

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎬 Stream", callback_data=f"stream|{file_id}"),
                InlineKeyboardButton("⬇️ Download", callback_data=f"download|{file_id}")
            ],
            [
                InlineKeyboardButton("⚡ Fast Stream", callback_data=f"faststream|{file_id}"),
                InlineKeyboardButton("🚀 Fast Download", callback_data=f"fastdownload|{file_id}")
            ]
        ]
    )

    await m.edit(caption, reply_markup=buttons, parse_mode="html")


# Callback Handler
@bot.on_callback_query()
async def cb_handler(_, query):
    action, file_id = query.data.split("|")
    file = CACHE.get(file_id)

    if not file:
        return await query.message.edit("❌ Expired, Send Link Again")

    if action == "stream":
        await query.message.reply_text(
            tiny(f"🎬 Stream:\n{file['stream_url']}"),
            parse_mode="html"
        )

    elif action == "download":
        await query.message.reply_text(
            tiny(f"⬇️ Download:\n{file['download_link']}"),
            parse_mode="html"
        )

    elif action == "fastdownload":
        await query.message.reply_text(
            tiny(f"🚀 Fast Download:\n{file['fast_download_link']}"),
            parse_mode="html"
        )

    elif action == "faststream":
        qualities = file["fast_stream_url"]

        btn = []
        for q, link in qualities.items():
            btn.append([InlineKeyboardButton(f"🎥 {q}", url=link)])

        await query.message.reply_text(
            tiny("⚡ Select Quality:"),
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode="html"
        )


print("🔥 Terabox Pro Bot Running...")
bot.run()
