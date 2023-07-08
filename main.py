# -*- coding: utf-8 -*-
import asyncio

import uvloop
import validators
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup

from config import (api_id, api_hash, token)
from utils import get_info, render_btn_list, download_file, remove_file, upload_file

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
        get_task = asyncio.create_task(get_info(url))
        finished_get, unfinished = await asyncio.wait([get_task])
        for get in finished_get:
            title, videos, audios = get.result()
            print(title)
            if not videos:
                other_task = asyncio.create_task(download_file(url=url))
                # wait args must be a list, and the return is a set
                finished_others, _ = await asyncio.wait([other_task])
                for finished_o in finished_others:
                    saved_path, title = finished_o.result()
                    await upload_file(saved_path, client, message.chat.id, title)
                    await remove_file(saved_path)
            else:
                video_btn, audio_btn = render_btn_list(url, videos, audios)
                chat_id = message.chat.id
                await client.send_message(
                    chat_id,
                    (f"Good! {url} is a valid video url.\n"
                     f"Title: {title}\n"
                     f"Now please select quality:\n"
                     ),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            video_btn,
                            audio_btn
                        ]
                    ), disable_web_page_preview=True, reply_to_message_id=chat_id, disable_notification=True
                )
                await client.delete_messages(chat_id, message.id)
    else:
        await client.send_message(message.chat.id, "Send The Valid Url Please")


@app.on_callback_query()
async def download(client, query):  # c Mean Client | q Mean Query
    chat_id = query.message.chat.id
    data = query.data
    url, opts = data.split("||")
    download_f_msg = await client.send_message(chat_id, 'Start Downloading...', disable_notification=True)
    download_task = asyncio.create_task(download_file(download_msg=download_f_msg, url=url, format_id=opts))
    finished_download, unfinished = await asyncio.wait([download_task])
    for downloaded in finished_download:
        await download_f_msg.delete()
        saved_path, title = downloaded.result()
        await upload_file(saved_path, client, chat_id, title)
        await remove_file(saved_path)


if __name__ == '__main__':
    app.run()
