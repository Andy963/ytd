# -*- coding: utf-8 -*-
from enum import Enum

import requests, os, validators
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import api_id, api_hash, token, chunk_size, download_path

app = Client("Downloader", api_id, api_hash, bot_token=token, )
# proxy=dict(hostname="127.0.0.1", port=51837)
video_pattern = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"


class Quality:
    high = 1
    normal = 2


def download_file(url, quality):
    quality = int(quality)
    if quality == Quality.high:
        ydl_opts_start = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # This Method Need ffmpeg
            'outtmpl': f'{download_path}/%(id)s.%(ext)s',
            'no_warnings': True,
            'ignoreerrors': True,
            'noplaylist': True,
            'http_chunk_size': chunk_size,
            'writethumbnail': True

        }
        with yt_dlp.YoutubeDL(ydl_opts_start) as ydl:
            result = ydl.extract_info("{}".format(url))
            title = ydl.prepare_filename(result)
            ydl.download([url])
        return title

    if quality == Quality.normal:
        ydl_opts_start = {
            'format': 'best',  # This Method Don't Need ffmpeg , if you don't have ffmpeg use This
            'outtmpl': f'{download_path}/%(id)s.%(ext)s',
            'no_warnings': False,
            'logtostderr': False,
            'ignoreerrors': False,
            'noplaylist': True,
            'http_chunk_size': chunk_size,
            'writethumbnail': True
        }
        with yt_dlp.YoutubeDL(ydl_opts_start) as ydl:
            result = ydl.extract_info("{}".format(url))
            title = ydl.prepare_filename(result)
            ydl.download([url])
        return f'{title}'


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
        f"Just send Video url, and let me try to download.")
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
                            "HD (Recommended) - Need ffmpeg",
                            callback_data=f"{new_url}||{Quality.high}"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "HD - Don't Need ffmpeg",
                            callback_data=f"{new_url}||{Quality.normal}"
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
    path = download_file(url, quality)
    upload_msg = client.send_message(chat_id, 'Yeah😁 Uploading...')
    download_msg.delete()
    thumb = path.replace('.mp4', ".jpg", -1)
    if os.path.isfile(thumb):
        thumb = open(thumb, "rb")
        path = open(path, 'rb')
        client.send_photo(chat_id, thumb,
                          caption='Thumbnail of the video Downloaded')  # Edit it and add your Bot ID :)
        client.send_video(chat_id, path, caption='Downloaded',
                          file_name="andy", supports_streaming=True,
                          progress=progress)  # Edit it and add your Bot ID :)
        upload_msg.delete()
    else:
        path = open(path, 'rb')
        client.send_video(chat_id, path, caption='Downloaded by @yinshan_bot',
                          file_name="iLoader", supports_streaming=True, progress=progress)
        upload_msg.delete()


if __name__ == '__main__':
    app.run()
