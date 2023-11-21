# -*- coding: utf-8 -*-
import shutil
from pathlib import Path

import uvloop
import validators
import yt_dlp
from pyrogram import Client, filters, enums

from config import api_id, api_hash, token, download_path

uvloop.install()
app = Client(
    "ytd",
    api_id,
    api_hash,
    bot_token=token,
)
video_pattern = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"


@app.on_message(filters.command("start", "/"))
def start(_, message):
    message.reply_text(
        (
            f"Welcome to ytd-dl!\n"
            f"Just send Video or Audio url, and let me try to download."
        )
    )


def download(url: str):
    """
    use yt-dlp to download video
    """
    video_filename, audio_filename = None, None
    if "youtu.be" in url:
        video_opt = {
            "outtmpl": "%(title)sv.%(ext)s",
            "format": "bestvideo+bestaudio",
        }
        audio_opt = {
            "outtmpl": "%(title)sa.%(ext)s",
            "format": "bestaudio",
        }
        with yt_dlp.YoutubeDL(video_opt) as ydl_video:
            info_dict_video = ydl_video.extract_info(url, download=True)
            video_filename = ydl_video.prepare_filename(info_dict_video)

        with yt_dlp.YoutubeDL(audio_opt) as ydl_audio:
            info_dict_audio = ydl_audio.extract_info(url, download=True)
            audio_filename = ydl_audio.prepare_filename(info_dict_audio)
    else:
        with yt_dlp.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_filename = ydl.prepare_filename(info_dict)
    return video_filename, audio_filename


@app.on_message()
async def webpage(client, message):
    url = message.text.strip()
    is_upload = False
    if "/upload" in url:
        url = url.split("/upload")[1].strip()
        is_upload = True

    if validators.url(url):
        message_id = message.id
        chat_id = message.chat.id
        tip = await message.reply_text("url is valid & download will start...")
        video_filename, audio_filename = download(url)
        await tip.delete()
        if is_upload:
            tip1 = await message.reply_text("media will start upload...")
            if audio_filename:
                await client.send_chat_action(chat_id, enums.ChatAction.UPLOAD_AUDIO)
                await client.send_video(
                    chat_id, audio_filename, supports_streaming=True
                )
                Path(audio_filename).unlink()
            if video_filename:
                await client.send_chat_action(chat_id, enums.ChatAction.UPLOAD_VIDEO)
                await client.send_video(
                    chat_id,
                    video_filename,
                    supports_streaming=True,
                )
                Path(video_filename).unlink()
            await tip1.delete()
            await message.reply_text(
                text="url solved.",
                disable_notification=True,
                reply_to_message_id=message_id,
            )
            return
        p_v = Path(download_path) / video_filename
        a_v = Path(download_path) / audio_filename
        if not p_v.exists() and video_filename != p_v:
            shutil.move(str(video_filename), download_path)
        if not a_v.exists() and audio_filename != a_v:
            shutil.move(str(audio_filename), download_path)
        await message.reply_text(
            text="url solved.",
            disable_notification=True,
            reply_to_message_id=message_id,
        )
    else:
        await message.reply_text("Invalid URL")


if __name__ == "__main__":
    app.run()
