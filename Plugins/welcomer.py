from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message


@Client.on_message(filters.command("start") & filters.private)
async def startCommand(c: Client, m: Message):
    await m.reply("👋")
    await c.send_message(
        m.chat.id,
        "🌍🌎🌏🌍🌎🌏",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("English 🇬🇧", callback_data="en"),
                    InlineKeyboardButton(
                        "اللغة العربية 🇮🇶", callback_data="ar"
                    ),
                ]
            ]
        ),
    )
