# -*- coding: utf-8 -*-

import re
import time

import validators

from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import (api_id, api_hash, token, )
from utils import get_info, render_btn_list, download_file, remove_file

app = Client("Downloader", api_id, api_hash, bot_token=token, )
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
def webpage(client, message):
    url = message.text
    if validators.url(url):
        videos, audios = get_info(url)
        if not videos:
            saved_path, title = download_file(url=url)
            upload_file(saved_path, client, message.chat.id, title)
            remove_file(saved_path)
        else:
            video_btn, audio_btn = render_btn_list(url, videos, audios)
            chat_id = message.chat.id
            client.send_message(
                chat_id,
                (f"Good! {url} is a valid video url.\n"
                 f"Now please select quality:\n"
                 ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        video_btn,
                        audio_btn
                    ]
                ), disable_web_page_preview=True
            )
    else:
        client.send_message(message.chat.id, "Send The Valid Url Please")


@app.on_callback_query()
def download(client, query):  # c Mean Client | q Mean Query
    chat_id = query.message.chat.id
    data = query.data
    url, opts = data.split("||")
    download_msg = client.send_message(chat_id, 'Start Downloading...')
    saved_path, title = download_file(download_msg, url, opts)
    download_msg.delete()
    upload_file(saved_path, client, chat_id, title)
    remove_file(saved_path)


def upload_file(saved_path, client, chat_id, title):
    bar = '=' * 20

    def progress(current, total):
        if current != total:
            symbol = re.sub('=', '>', bar, int(current * 20 / total))
            upload_msg.edit(f"{symbol}{current * 100 / total:.1f}%")
        else:
            upload_msg.delete()
        time.sleep(1)

    with open(saved_path, 'rb') as fp:
        upload_msg = client.send_message(chat_id, bar + " upload will start soon")
        client.send_video(chat_id, fp, caption=title,
                          file_name=title, supports_streaming=True,
                          progress=progress
                          )
        client.send_chat_action(chat_id, enums.ChatAction.UPLOAD_VIDEO)


if __name__ == '__main__':
    app.run()