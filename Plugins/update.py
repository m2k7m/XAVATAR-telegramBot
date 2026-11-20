import os
import subprocess
import sys

import git
from pyrogram import Client, filters
from pyrogram.types import Message

from main import ownerID


def restart():
    os.execv(sys.executable, [sys.executable] + sys.argv)


@Client.on_message(filters.command("تحديث", "") & filters.user(ownerID))
async def update(_: Client, m: Message):
    msg = await m.reply("⌛ | جار العمل...")

    current_hash = git.Repo().head.commit.hexsha

    git.Repo().remote("origin").fetch()

    branch = git.Repo().active_branch.name
    upcoming = next(git.Repo().iter_commits(f"origin/{branch}", max_count=1)).hexsha

    if current_hash == upcoming:
        return await msg.edit("**✅ | انت على اخر اصدار من البوت.**")

    try:
        await msg.edit(
            f"⌛ | يتم التحديث من `{current_hash[:5]}` الى `{upcoming[:5]}` ..."
        )
        git.Repo().remote("origin").pull()
    except git.exc.GitCommandError as e:
        return await msg.edit(
            "<b>Update failed! Try again with --hard argument.</b>\n\n"
            f"```bash\n{e.stderr.strip()}\n```"
        )

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-U", "pip"], check=True
        )
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-U", "-r", "requirements.txt"],
            check=True,
        )
    except Exception as e:
        await msg.edit(f"❌ | فشل التحديث.\n```bash\n{e!s}\n```")
    else:
        await msg.edit("✅ | تم التحديث, جار إعادة التشغيل...")
        restart()
