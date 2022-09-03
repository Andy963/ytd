# -*- coding: utf-8 -*-

import re
import time
from pathlib import Path

import validators
import yt_dlp
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import (api_id, api_hash, token, )
from utils import get_info, render_btn_list

app = Client("Downloader", api_id, api_hash, bot_token=token, )
# proxy=dict(hostname="127.0.0.1", port=51837)
video_pattern = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"


def download_file(download_msg, url, format_id):
    """
    :param download_msg: client msg obj
    :param url: video url
    :param format_id: video: 199+154, audio: 155
    :return:
    """
    start = time.time()
    global video_finish
    video_finish = False

    def progress_hook(data):
        global video_finish
        msg = data['_percent_str']
        per = re.search(r'\d+\.\d+%', msg, )
        if per:
            percent = per.group(0)
            msg = f"downloading video: {percent} used time: {time.time() - start:.1f}s"
            if percent == '100':
                video_finish = True
            if not video_finish:
                download_msg.edit(msg)
            else:
                msg = msg + f'\n downloading audio: {percent} total time: {time.time() - start:.1f}s'
                download_msg.edit(msg)

    opt = {
        "format": format_id,
        "format_id": format_id,
        "outtmpl": f"%(title)s.%(ext)s",
        "noplaylist": True,
        "writethumbnail": False,
        "final_ext": f"%(ext)s",
        'progress_hooks': [progress_hook]
    }
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

    bar = '=' * 20

    def progress(current, total):

        if current != total:
            symbol = re.sub('=', '>', bar, int(current * 20 / total))
            upload_msg.edit(f"{symbol}{current * 100 / total:.1f}%")
        else:
            upload_msg.delete()

    chat_id = query.message.chat.id
    data = query.data
    url, opts = data.split("||")
    download_msg = client.send_message(chat_id, 'Start Downloading...')
    saved_path, title = download_file(download_msg, url, opts)
    upload_msg = client.send_message(chat_id, bar + "0% uploaded")
    with open(saved_path, 'rb') as fp:
        client.send_chat_action(chat_id, enums.ChatAction.UPLOAD_VIDEO)
        upload_result = client.send_video(chat_id, fp, caption=title,
                                          file_name=title, supports_streaming=True,
                                          progress=progress
                                          )
    download_msg.delete()
    remove_file(saved_path)


if __name__ == '__main__':
    app.run()
