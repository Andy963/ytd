# -*- coding: utf-8 -*-

from pathlib import Path

import validators
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import (api_id, api_hash, token, )
from utils import get_info, render_btn_list

app = Client("Downloader", api_id, api_hash, bot_token=token, )
# proxy=dict(hostname="127.0.0.1", port=51837)
video_pattern = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"


def download_file(url, format_id):
    """
    :param url: video url
    :param format_id: video: 199+154, audio: 155
    :return:
    """
    opt = {
        "format": format_id,
        "format_id": format_id,
        "outtmpl": f"%(title)s.%(ext)s",
        "noplaylist": True,
        "writethumbnail": False,
        "final_ext": f"%(ext)s"
    }
    print('opt', opt)
    with yt_dlp.YoutubeDL(opt) as ydl:
        result = ydl.extract_info(url, download=True)
        title = result.get('title')
        saved_path = ydl.prepare_filename(result)
        return saved_path, title


def remove_file(file_path: str) -> bool:
    """
    Func: remove uploaded file, with file_name pattern
    Args:
    Example: remove_file('/opt/test.mp4')
    Return: True/False
    Author: Andy
    Version: 1.0
    Created: 2022/4/4 下午7:08
    Modified: 2022/4/4 下午7:08
    """
    pt = Path(file_path)
    try:
        if pt.exists():
            for file in pt.parent.iterdir():
                if pt.stem in str(file):
                    file.unlink()
        return True
    except Exception as e:
        return False


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
        video_btn, audio_btn = render_btn_list(url, videos, audios)
        chat_id = message.chat.id
        client.send_message(
            chat_id,
            (f"Good! {url} is a valid video url.\n"
             f"now please select quality:\n"
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
    download_msg = client.send_message(chat_id, 'Hmm!😋 Downloading...')
    saved_path, title = download_file(url, opts)
    with open(saved_path, 'rb') as fp:
        upload_result = client.send_video(chat_id, fp, caption=title,
                                          file_name=title, supports_streaming=True,
                                          )
    remove_file(saved_path)
    download_msg.delete()


if __name__ == '__main__':
    app.run()
