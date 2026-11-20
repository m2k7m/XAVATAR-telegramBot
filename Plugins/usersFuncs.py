from pyrogram import Client, filters
from pyrogram.errors import MessageNotModified
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LinkPreviewOptions,
    Message,
)

from main import lang, ownerID
from storage import (
    add_new_user,
    add_supporter,
    get_all_supporters,
    get_user_lang,
    remove_supporter,
    set_language,
    user_exists,
)


@Client.on_message(filters.command("اضف داعم", "") & filters.user(ownerID))
async def addSupporter(c: Client, m: Message):
    if len(m.command) < 2:
        await m.reply("يرجى تقديم معرف مستخدم.")
        return

    supporter_id = m.command[1]

    if not supporter_id or not supporter_id.isdigit():
        await m.reply("يرجى تقديم معرف مستخدم صالح.")
        return

    await add_supporter(int(supporter_id))

    await m.reply("تمت اضافة الداعم")


@Client.on_message(filters.command("حذف داعم", "") & filters.user(ownerID))
async def removeSupporter(c: Client, m: Message):
    if len(m.command) < 2:
        await m.reply("يرجى تقديم معرف مستخدم.")
        return

    supporter_id = m.command[1]

    if not supporter_id or not supporter_id.isdigit():
        await m.reply("يرجى تقديم معرف مستخدم صالح.")
        return

    await remove_supporter(int(supporter_id))

    await m.reply("تم حذف الداعم")


@Client.on_callback_query(filters.regex(r"^(ar|en)$"))
async def changeLang(c: Client, cb: CallbackQuery):
    user_id = cb.from_user.id
    selected_lang = cb.data

    if not await user_exists(user_id):
        await add_new_user(user_id, selected_lang)

        await c.send_message(
            ownerID,
            "انضم عضو جديد!\n"
            + f"اسمه: {cb.from_user.full_name}\n"
            + f"يوزره: @{cb.from_user.username if cb.from_user.username else '-'}\n"
            + f"ايديه: `{cb.from_user.id}`",
        )
    else:
        await set_language(user_id, selected_lang)

    try:
        await cb.message.edit(
            lang[selected_lang]["welcome"].format(mention=cb.from_user.mention),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            lang[selected_lang]["aboutTxt"], callback_data="about"
                        ),
                        InlineKeyboardButton(
                            lang[selected_lang]["supporters"],
                            callback_data="supporters",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            lang[selected_lang]["avatarsCollection"],
                            url="https://psprices.com/region-us/collection/avatars",
                        )
                    ],
                ]
            ),
        )
    except MessageNotModified:
        pass
    except Exception as e:
        await c.send_message(ownerID, f"from {cb.from_user.id}:\n{e}")


@Client.on_callback_query(filters.regex(r"^back_to_main$"))
async def back_to_main(c: Client, cb: CallbackQuery):
    selected_lang = await get_user_lang(cb.from_user.id)
    await cb.message.edit(
        lang[selected_lang]["welcome"].format(mention=cb.from_user.mention),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        lang[selected_lang]["aboutTxt"], callback_data="about"
                    ),
                    InlineKeyboardButton(
                        lang[selected_lang]["supporters"], callback_data="supporters"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        lang[selected_lang]["avatarsCollection"],
                        url="https://psprices.com/region-us/collection/avatars",
                    )
                ],
            ]
        ),
    )


@Client.on_callback_query(filters.regex(r"^supporters$"))
async def showSupporters(c: Client, cb: CallbackQuery):
    supporter_ids = await get_all_supporters()
    userLang = await get_user_lang(cb.from_user.id)

    if not supporter_ids:
        await cb.answer(lang[userLang]["nosupportedyet"], show_alert=True)
        return

    if not isinstance(supporter_ids, list):
        supporter_ids = [supporter_ids]

    batch_ids = supporter_ids[:100]

    users_map = {}
    try:
        users = await c.get_users(batch_ids)

        if not isinstance(users, list):
            users = [users]

        users_map = {u.id: u for u in users}
    except Exception:
        pass

    lines = []
    header = lang[userLang]["supported_list"]

    for i, uid in enumerate(batch_ids, 1):
        if uid in users_map:
            lines.append(f"{i}. {users_map[uid].mention}")
        else:
            lines.append(f"{i}. `{uid}`")

    text = header + "\n".join(lines)

    await cb.message.edit(
        text=text,
        link_preview_options=LinkPreviewOptions(is_disabled=True),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        lang[userLang]["back"], callback_data="back_to_main"
                    )
                ]
            ]
        ),
    )


@Client.on_callback_query(filters.regex(r"^about$"))
async def about(c: Client, cb: CallbackQuery):
    userlang = await get_user_lang(cb.from_user.id)

    gamer = "[4GAMER](https://t.me/addlist/vDYvpf_HAx04NzUy)"

    if userlang == "ar":
        msg = """
⚡ XAVATAR by {gamer}

مرحبًا بك في بوت XAVATAR
الخدمة الرسمية من فريق {gamer} لتحويل الصور والملصقات والروابط المباشرة إلى صيغة .xavatar المستخدمة في صور حسابات جهاز PS4.

🔧 وظيفة البوت
تحويل أي صورة خلال ثوانٍ إلى صيغة XAVATAR الجاهزة للعمل على PS4 — بدون برامج إضافية وبدون تعقيد.


👑 فريق العمل

الإنشاء والإدارة:

	Čhiki Čhiki — مؤسّس {gamer}.


البرمجة والترجمة:

	Mahdi — المطوّر الأساسي والمترجم.


التصميم والإنتاج المرئي:

	ᴀʙᴏᴏᴅ ꜱᴄᴏꜰɪᴇʟᴅ ⚡ — مصمّم صورة البوت وصاحب الشرح على اليوتيوب.



🤝 شكر خاص لعائلة {gamer}

👑‌🇾‌🇦‌🇸‌🇪‌🇪‌🇷👑‏ — صاحب فكرة البوت.

عليٌ — مسؤول الاختبار ومراجعة الأداء.



🛠 للإبلاغ عن المشاكل أو الملاحظات

يرجى مراسلة المطوّر مباشرة:
@TheStorm991
    """
    else:
        msg = """
⚡ XAVATAR by {gamer}

Welcome to the XAVATAR bot
The official service from the {gamer} team for converting images, stickers, and direct links to the .xavatar format used for PS4 profile pictures.

🔧 Bot Function
Convert any image in seconds to the XAVATAR format, ready to work on PS4 — without additional software and without complications.

👑 Team

Creation and Management:

Čhiki Čhiki — Founder of {gamer}.

Programming and Translation:

Mahdi — Lead Developer and Translator.

Design and Visual Production:

Abood Scueyld ⚡ — Bot image designer and author of the tutorial on YouTube.

🤝 Special thanks to the {gamer} family

👑‌🇾‌🇦‌🇸‌🇪‌🇪‌🇷👑 — Bot suggester.

Ali — Testing and Performance Review Manager.

🛠 To report issues or feedback

Please contact the developer directly:

@TheStorm991

    """

    await cb.message.edit(
        msg.format(gamer=gamer),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        lang[userlang]["back"], callback_data="back_to_main"
                    )
                ]
            ]
        ),
    )
