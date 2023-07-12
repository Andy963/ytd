# -*- coding: utf-8 -*-
import asyncio
import shutil
from pathlib import Path

import uvloop
import validators
import yt_dlp
from pyrogram import Client, filters

import config
from config import (api_id, api_hash, token)

uvloop.install()
app = Client("ytd", api_id, api_hash, bot_token=token, )
video_pattern = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"


@app.on_message(filters.command('start', '/'))
def start(_, message):
    """
    Func:start response
    Args:message: message
    Example:
    Return: None
    Author: Andy
    Version: 1.0
    Created: 2022/4/4 下午4:04
    Modified: 2022/4/4 下午4:04
    """
    message.reply_text((
        f"Welcome to ytd-dl!\n"
        f"Just send Video or Audio url, and let me try to download.")
    )


@app.on_message(filters.regex(video_pattern))
async def webpage(client, message):
    url = message.text
    if validators.url(url):
        loop = asyncio.get_event_loop()

        opt = {
            "username": '',
            "password": '',
            "format": 'bv*+ba/b',
            "format_id": 'bv*+ba/b',
            "outtmpl": "%(title)s.%(ext)s",
            "noplaylist": True,
            "writethumbnail": False,
            "final_ext": "%(ext)s",
            "trim_file_name": 50,
            "windowsfilenames": True,
        }
        with yt_dlp.YoutubeDL(opt) as ydl:
            result = await loop.run_in_executor(None, ydl.extract_info, url,
                                                True)
            saved_path = await loop.run_in_executor(None, ydl.prepare_filename,
                                                    result)
            title = result.get('title')
            if Path(saved_path).exists():
                if Path(saved_path) != Path(config.download_path):
                    shutil.move(saved_path, config.download_path)
            else:
                await client.send_message(message.chat.id, f"视频下载失败！")
            await message.delete()
            await client.send_message(message.chat.id,
                                      f"URL: {url}\n"
                                      f"Title: {title}\n"
                                      f"视频下载完成！")

    else:
        await client.send_message(message.chat.id, "Send The Valid Url Please")


if __name__ == '__main__':
    app.run()
