# -*- coding: utf-8 -*-
import time
from pathlib import Path

import requests, os, validators
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import (api_id, api_hash, token, chunk_size, download_path, BEST_VIDEO_FORMAT, VIDEO,
                    AUDIO, BEST_AUDIO_FORMAT)

app = Client("Downloader", api_id, api_hash, bot_token=token, )
# proxy=dict(hostname="127.0.0.1", port=51837)
video_pattern = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"


class Quality:
    best_video = 1
    best_audio = 2


def download_file(url, quality):
    quality = int(quality)
    ydl_opts_start = {
        'format': BEST_VIDEO_FORMAT,
        'outtmpl': f'{download_path}%(id)s.mp4',
        'no_warnings': False,
        'logtostderr': False,
        'ignoreerrors': False,
        'noplaylist': True,
        'http_chunk_size': chunk_size,
        'writethumbnail': True
    }
    if quality == Quality.best_audio:
        ydl_opts_start = {
            'format': BEST_AUDIO_FORMAT,
            'outtmpl': f'{download_path}%(id)s.m4a',
            'no_warnings': False,
            'logtostderr': False,
            'ignoreerrors': False,
            'noplaylist': True,
            'http_chunk_size': chunk_size,
            'writethumbnail': True
        }
    with yt_dlp.YoutubeDL(ydl_opts_start) as ydl:
        result = ydl.extract_info("{}".format(url))
        title = result.get('title', 'no_title')
        media_type = 'audio' if result.get('audio_ext') != 'none' else 'video'
        saved_path = ydl.prepare_filename(result)
        ydl.download([url])
        return saved_path, title, media_type


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
        sample_url = "https://da.gd/s?url={}".format(url)
        new_url = requests.get(sample_url).text
        chat_id = message.chat.id
        keys = client.send_message(
            chat_id,
            (f"Good! {url} is a valid video url.\n"
             f"now please select quality:\n"
             ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Best Video",
                            callback_data=f"{new_url}||{Quality.best_video}"
                        ),
                    ],

                    [
                        InlineKeyboardButton(
                            "Best Audio",
                            callback_data=f"{new_url}||{Quality.best_audio}"
                        ),
                    ]
                ]
            ), disable_web_page_preview=True
        )
    else:
        client.send_message(message.chat.id, "Send The Valid Url Please")


@app.on_callback_query()
def download(client, query):  # c Mean Client | q Mean Query
    global check_current
    check_current = 0

    def progress(current, total):  # Thanks to my dear friend Hassan Hoot for Progress Bar :)
        global check_current
        if ((current // 1024 // 1024) % 50) == 0:
            if check_current != (current // 1024 // 1024):
                check_current = (current // 1024 // 1024)
                upload_msg.edit(f"{current // 1024 // 1024}MB of {total // 1024 // 1024}MB Uploaded 😁")
        elif (current // 1024 // 1024) == (total // 1024 // 1024):
            upload_msg.delete()

    chat_id = query.message.chat.id
    data = query.data
    url, quality = data.split("||")
    download_msg = client.send_message(chat_id, 'Hmm!😋 Downloading...')
    saved_path, title, media_type = download_file(url, quality)
    upload_msg = client.send_message(chat_id, 'Yeah😁 Uploading...')
    download_msg.delete()
    with open(saved_path, 'rb') as fp:
        if media_type == VIDEO:
            upload_result = client.send_video(chat_id, fp, caption=title,
                                              file_name=title, supports_streaming=True,
                                              progress=progress)
        elif media_type == AUDIO:
            upload_result = client.send_audio(chat_id, fp, caption=title, title=title, progress=progress)
        upload_msg.delete()
        if upload_result:
            remove_msg = client.send_message(chat_id, f"file upload finish, remove from disk!")
        else:
            remove_msg = client.send_message(chat_id, f"file upload failed, please try again!")
        remove_file(saved_path)
        remove_msg.delete()


if __name__ == '__main__':
    app.run()
