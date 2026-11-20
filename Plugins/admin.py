from pyrogram import Client, filters
from pyrogram.types import Message

from main import ownerID
from storage import (
    get_all_users,
    get_language_stats,
    get_sum_of_counts,
    get_top_10_users,
    get_user_count,
    get_user_lang,
)


@Client.on_message(
    filters.command(["الإحصائيات", "إحصائيات", "احصائيات", "الاحصائيات"], "")
    & filters.user(ownerID),
    group=2,
)
async def stats_command(c: Client, m: Message):
    total_users = await get_all_users()
    ar_count, en_count = await get_language_stats()
    total_usage = await get_sum_of_counts()
    top_10_users = await get_top_10_users()

    if total_users > 0:
        ar_percent = (ar_count / total_users) * 100
        en_percent = (en_count / total_users) * 100
    else:
        ar_percent = 0.0
        en_percent = 0.0

    lines = [
        "📊 **إحصائيات البوت:**\n",
        f"👥 إجمالي المستخدمين: {total_users}",
        f"⚙️ إجمالي الاستخدامات: {total_usage}",
        f"🌐 المستخدمين اللغة العربية: {ar_count}",
        f"🌐 نسبة المستخدمين اللغة العربية: {ar_percent:.2f}%",
        f"🌐 المستخدمين اللغة الانجليزية: {en_count}",
        f"🌐 نسبة المستخدمين اللغة الانجليزية: {en_percent:.2f}%\n",
        "🏆 **أفضل 10 مستخدمين:**",
    ]

    for i, (user_id, count) in enumerate(top_10_users, 1):
        lines.append(f"{i}. `{user_id}` - {count}")

    final_text = "\n".join(lines)

    await m.reply(final_text)


@Client.on_message(filters.command("معلومات", "") & filters.user(ownerID), group=2)
async def info_command(c: Client, m: Message):
    user_id = m.command[1] if len(m.command) > 1 else None

    if not user_id or not user_id.isdigit():
        await m.reply("يرجى تقديم معرف مستخدم صالح.")
        return

    try:
        user_stats = await c.get_users(int(user_id))
        user_lang = await get_user_lang(int(user_id))
        user_count = await get_user_count(int(user_id))
    except Exception:
        await m.reply("تعذر العثور على المستخدم.")
        return

    lines = [
        "📄 **معلومات المستخدم:**\n",
        f"📛 الاسم الكامل: {user_stats.full_name}",
        f"👤 معرف المستخدم: `{user_stats.id}`",
        f"📝 اسم المستخدم: @{user_stats.username if user_stats.username else '-'}",
        f"رابط حسابه: {user_stats.mention}",
        f"حساب محذوف: {'نعم' if user_stats.is_deleted else 'لا'}",
        f"مشترك في تيليجرام مميز: {'نعم' if user_stats.is_premium else 'لا'}",
        f"🌐 اللغة: {user_lang}",
        f"⚙️ إجمالي الاستخدامات: {user_count}",
    ]

    final_text = "\n".join(lines)
    await m.reply(final_text)