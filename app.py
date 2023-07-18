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

# Bot token can be obtained via https://t.me/BotFather
TOKEN = config.telegram_token
q = asyncio.Queue()
# All handlers should be attached to the Router (or Dispatcher)
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
    # 选择视频+音频格式

    opt = {
        'outtmpl': '%(title)s.%(ext)s',
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]',
        'embedthumbnail': True,
        'rm_thumbnail': True,
        'merge_output_format': 'mp4',
    }

    with yt_dlp.YoutubeDL(opt) as ydl:
        info_dict = ydl.extract_info(url, download=True)
    title = info_dict.get('title', 'No title found')

    # 获取转换后的音频文件名
    filename = ydl.prepare_filename(info_dict)
    cur_path = Path(filename).absolute()
    if cur_path.parent != Path(config.download_path):
        if not (Path(config.download_path) / filename).exists():
            shutil.move(cur_path, config.download_path)
        else:
            shutil.move(cur_path, Path(config.download_path) / f'ytd/{title}.mp4')
    return title


async def download_consumer(q, bot):
    while True:
        chat_id, url = await q.get()
        title = download(url)

        try:
            await bot.send_message(chat_id=chat_id, text=f'<pre>{title}</pre>download finished!.',
                                   disable_notification=True)
        except Exception as e:
            await bot.send_message(chat_id=chat_id, text=f"error occured:\n{e}",
                                   disable_notification=True)


@dp.message()
async def message_handler(message: types.Message) -> None:
    if validators.url(message.text):
        await SendMessage(chat_id=message.from_user.id, text=message.text,
                          disable_web_page_preview=True, disable_notification=True)
        await message.delete()
        await q.put([message.from_user.id, message.text])
        await SendMessage(chat_id=message.from_user.id,
                          text=f'<pre>{message.text}</pre>will start download soon.',
                          disable_notification=True)
    else:
        await SendMessage(chat_id=message.from_user.id, text='Please send me a valid youtube link.',
                          disable_notification=True)


async def main() -> None:
    # Dispatcher is a root router
    # ... and all other routers should be attached to Dispatcher
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode="HTML")
    # And the run events dispatching

    download_worker_task = asyncio.create_task(download_consumer(q, bot))
    await dp.start_polling(bot)
    await download_worker_task


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
