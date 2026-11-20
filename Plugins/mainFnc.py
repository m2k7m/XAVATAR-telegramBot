import os
import shutil
from io import BytesIO
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

import aiohttp
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaDocument,
    InputMediaPhoto,
    Message,
)
from wand.image import Image as WandImage

from main import lang, ownerID, supported_formats
from storage import (
    decrement_usage,
    get_user_count,
    get_user_lang,
    increment_usage,
    is_user_busy,
    set_user_busy,
    set_user_free,
    user_exists,
)

sizes = [440, 260, 128, 64]


def create_online_json(dir: str) -> None:
    online_json_content = r"""{"avatarUrl":"http:\/\/static-resource.np.community.playstation.net\/avatar_xl\/WWS_E\/E0012_XL.png","firstName":"","lastName":"","pictureUrl":"https:\/\/image.api.np.km.playstation.net\/images\/?format=png&w=440&h=440&image=https%3A%2F%2Fkfscdn.api.np.km.playstation.net%2F00000000000008%2F000000000000003.png&sign=blablabla019501","trophySummary":"{\"level\":1,\"progress\":0,\"earnedTrophies\":{\"platinum\":0,\"gold\":0,\"silver\":0,\"bronze\":0}}","isOfficiallyVerified":"true"}"""
    with open(f"{dir}/online.json", "w") as f:
        f.write(online_json_content)


def add_files_to_zip_in_memory(file_paths: list[str]) -> bytes:
    in_memory_zip = BytesIO()

    with ZipFile(in_memory_zip, "w", ZIP_DEFLATED) as zf:
        for file_path in file_paths:
            arcname = os.path.basename(file_path)
            zf.write(file_path, arcname)

    in_memory_zip.seek(0)
    return in_memory_zip.read()


def process_image(img: WandImage, temp_dir: str) -> None:
    img.format = "png"
    img.resize(440, 440)

    img.save(filename=os.path.join(temp_dir, "avatar.png"))

    img.compression = "dxt5"

    for size in sizes:
        if img.width != size:
            img.resize(size, size)

        output_filename = os.path.join(temp_dir, f"avatar{size}.dds")
        img.save(filename=output_filename)


def copy_files(dir: str) -> None:
    create_online_json(dir)
    shutil.copy(f"{dir}/avatar.png", f"{dir}/picture.png")

    for size in sizes:
        outputdirection = f"{dir}/picture{size}.dds"
        inputdirection = f"{dir}/avatar{size}.dds"
        shutil.copy(inputdirection, outputdirection)


@Client.on_message(
    (filters.photo | filters.document | filters.sticker)
    & filters.private
    & ~filters.media_group
    & ~filters.me,
    group=1,
)
async def prossesImage(c: Client, m: Message) -> None:
    if not await user_exists(m.from_user.id):
        await m.reply(
            "برجى اختيار لغة للمتابعة.\n\nPlease select a language to continue.",
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
        return

    userlang = await get_user_lang(m.from_user.id)

    if await is_user_busy(m.from_user.id):
        await m.reply(lang[userlang]["busy"])
        return

    if m.document:
        if m.document.file_name.endswith(".xavatar"):
            return await prossesXavatar(c, m)

        if m.document.file_size > 10485760:
            await m.reply(lang[userlang]["tooBig"])
            return

        if m.document.file_name.split(".", 1)[1].lower() not in supported_formats:
            await m.reply(lang[userlang]["notSupported"])
            return

    if m.sticker:
        if m.sticker.is_animated:
            await m.reply(lang[userlang]["notSupported"])
            return

        if m.sticker.is_video:
            await m.reply(lang[userlang]["notSupported"])
            return

        if m.sticker.premium_animation:
            await m.reply(lang[userlang]["notSupported"])
            return

    await set_user_busy(m.from_user.id)

    wait_msg = await m.reply(lang[userlang]["wait"])

    with TemporaryDirectory() as temp_dir:
        image_path = await m.download(temp_dir + "/")
        output_path = os.path.join(temp_dir, "avatar.png")

        try:
            with WandImage(filename=image_path) as img:
                process_image(img, temp_dir)
        except Exception as isError:
            await wait_msg.edit(lang[userlang]["failedprocessingimg"])
            await c.send_message(ownerID, isError)
            return

        copy_files(temp_dir)

        os.remove(image_path)

        files = [entry.path for entry in os.scandir(temp_dir)]

        archiveBytes = add_files_to_zip_in_memory(files)

        await increment_usage(m.from_user.id)

        Count = await get_user_count(m.from_user.id)

        xavatarPath = f"{temp_dir}/{m.from_user.id}-{Count}.xavatar"

        with open(xavatarPath, "wb") as f:
            f.write(archiveBytes)

        try:
            await wait_msg.edit_media(
                InputMediaDocument(
                    xavatarPath, thumb=output_path, caption=f"- @{c.me.username}"
                )
            )
        except Exception as e:
            await wait_msg.edit(lang[userlang]["failedprocessingimg"])
            await c.send_message(
                ownerID, f"Failed to send file to user `{m.from_user.id}`\nError: {e}"
            )
            await decrement_usage(m.from_user.id)
        finally:
            await set_user_free(m.from_user.id)


@Client.on_message(
    filters.regex(
        r"^((https?|ftp|smtp):\/\/)?(www.)?[a-z0-9]+(\.[a-z]{2,}){1,3}(#?\/?[a-zA-Z0-9#]+)*\/?(\?[a-zA-Z0-9-_]+=[a-zA-Z0-9-%]+&?)?"
    )
    & filters.text
    & filters.private
    & ~filters.me,
    group=1,
)
async def prossesImageFromURL(c: Client, m: Message) -> None:
    if not await user_exists(m.from_user.id):
        await m.reply(
            "برجى اختيار لغة للمتابعة.\n\nPlease select a language to continue.",
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
        return

    userlang = await get_user_lang(m.from_user.id)

    if await is_user_busy(m.from_user.id):
        await m.reply(lang[userlang]["busy"])
        return

    wait_msg: Message = await m.reply(lang[userlang]["wait"])

    try:
        async with aiohttp.ClientSession() as session, session.get(m.text) as r:
            if r.status != 200:
                await wait_msg.edit(
                    lang[userlang]["connectionError"].format(errorCode=r.status)
                )
                return
            data = await r.read()
    except Exception as e:
        await c.send_message(
            ownerID, f"Failed to send file to user `{m.from_user.id}`\nError: {e}"
        )
        await wait_msg.edit(lang[userlang]["InvalidURL"])
        return

    await set_user_busy(m.from_user.id)

    with TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "avatar.png")
        try:
            with WandImage(blob=data) as img:
                process_image(img, temp_dir)
        except Exception as isError:
            await wait_msg.edit(lang[userlang]["failedprocessingimg"])
            await c.send_message(ownerID, isError)
            return

        copy_files(temp_dir)

        files = [os.path.join(temp_dir, filename) for filename in os.listdir(temp_dir)]

        archiveBytes = add_files_to_zip_in_memory(files)

        await increment_usage(m.from_user.id)

        Count = await get_user_count(m.from_user.id)

        xavatarPath = f"{temp_dir}/{m.from_user.id}-{Count}.xavatar"

        with open(xavatarPath, "wb") as f:
            f.write(archiveBytes)

        try:
            await wait_msg.edit_media(
                InputMediaDocument(
                    xavatarPath, thumb=output_path, caption=f"- @{c.me.username}"
                )
            )
        except Exception as e:
            await wait_msg.edit(lang[userlang]["failedprocessingimg"])
            await c.send_message(
                ownerID, f"Failed to send file to user `{m.from_user.id}`\nError: {e}"
            )
            await decrement_usage(m.from_user.id)
        finally:
            await set_user_free(m.from_user.id)


async def prossesXavatar(c: Client, m: Message) -> None:
    userlang = await get_user_lang(m.from_user.id)

    if await is_user_busy(m.from_user.id):
        await m.reply(lang[userlang]["busy"])
        return
    
    await set_user_busy(m.from_user.id)

    waitMsg = await m.reply(lang[userlang]["wait"])

    try:
        with TemporaryDirectory() as temp_dir:
            xavatarPath = await m.download(temp_dir + "/")

            with ZipFile(xavatarPath, "r") as xav:
                xav.extract("avatar.png", temp_dir)

            try:
                await waitMsg.edit_media(
                    InputMediaPhoto(
                        f"{temp_dir}/avatar.png", caption=f"- @{c.me.username}"
                    )
                )
            except Exception as e:
                await waitMsg.edit(lang[userlang]["failedprocessingimg"])
                await c.send_message(
                    ownerID,
                    f"Failed to send file to user 2nd `{m.from_user.id}`\nError: {e}",
                )
    finally:
        await set_user_free(m.from_user.id)
