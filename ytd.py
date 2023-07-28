import asyncio
import logging
import shutil
from pathlib import Path

import validators
import yt_dlp
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.methods import SendMessage
from aiogram.types import Message

import config as config

bot = Bot(config.telegram_token, parse_mode="HTML")
router = Router()
dp = Dispatcher()
video_pattern = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"


@router.message(Command(commands=["start"]))
async def command_start_handler(message: Message) -> None:
    """
    This handler receive messages with `/start` command
    """
    text = "Hi! I'm An Youtube Download Bot🤖\n\n Now you can send me a youtube link to download it."
    await message.answer(text)


def download(url: str):
    video_opt = {
        "outtmpl": "%(title)s.%(ext)s",
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a],bestaudio[ext=m4a]",
    }
    exts = ["m4a", "mp4"]

    if "youtu.be" in url:
        with yt_dlp.YoutubeDL(video_opt) as ydl:
            info_dict = ydl.extract_info(url, download=True)
    else:
        with yt_dlp.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(url, download=True)
    filename = ydl.prepare_filename(info_dict)
    ext = Path(filename).suffix
    if ext not in exts:
        exts.append(ext)
    cur_path = Path(filename).absolute()
    title = info_dict.get("title")
    name = Path(filename).stem
    for ext in exts:
        f = f"{name}.{ext}"
        cur_f = cur_path.parent / f"{name}.{ext}"
        if not cur_f.exists():
            continue
        p_ = Path(config.download_path) / f
        if not p_.exists() and cur_f != p_:
            shutil.move(cur_f, config.download_path)
        else:
            cur_f.unlink()
    return title


@dp.message()
async def message_handler(message: types.Message) -> None:
    if validators.url(url := message.text):
        url_msg = await SendMessage(
            chat_id=message.from_user.id,
            text=message.text,
            disable_web_page_preview=True,
            disable_notification=True,
        )
        await message.delete()
        tip_msg = await SendMessage(
            chat_id=message.from_user.id,
            text=f"<pre" f">{message.text}</pre>will start download soon.",
            disable_notification=True,
        )
        chat_id = message.from_user.id
        title = download(message.text)
        await bot.delete_message(chat_id=chat_id, message_id=url_msg.message_id)
        await bot.delete_message(chat_id=chat_id, message_id=tip_msg.message_id)
        await bot.send_message(
            chat_id=chat_id,
            text=f"<pre>{message.text}</pre>\n\n{title}\n\n download finished!",
        )
    else:
        await SendMessage(
            chat_id=message.from_user.id,
            text="Please send me a valid youtube link.",
            disable_notification=True,
        )


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
