# ！/usr/bin/env python
# encoding:utf-8
# Created by Andy at 2022/9/3
import random
import re
import asyncio

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yt_dlp
from pyrogram import enums
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton

_executor = ThreadPoolExecutor(max_workers=6)
loop = asyncio.get_event_loop()


def parse_formats(title: str, formats: list) -> tuple:
    """get field from  extracted info"""
    video_list, video_tag = [], []
    audio_list, audio_tag = [], []

    fields = ['format_id', 'format_note', 'filesize', 'ext', 'quality', 'height', 'width', 'language',
              'downloader_options', 'title', 'url']
    for f in formats:
        if not f.get('vcodec') or not f.get('acodec'):
            continue
        fl = dict(zip(fields, list(map(f.get, fields))))

        if not fl.get('filesize'):
            continue
        if not fl.get('format_id').isdigit():
            continue
        f['title'] = title
        if fl.get('downloader_options'):
            fl['chunk_size'] = fl.get('downloader_options').get('http_chunk_size', 0)
        # if two 1080p will only keep one
        if not fl.get('height') and not fl.get('width'):
            if fl.get('format_note') not in audio_tag:
                audio_list.append(fl)
                audio_tag.append(fl.get('format_note'))
        elif fl.get('height') and fl.get('width'):
            f_note = fl.get('format_note')
            f_note = f_note.lower()
            f_note = f_note.split('p')[0] + 'p'
            if f_note not in video_tag:
                video_tag.append(f_note)
                fl['format_note'] = f_note
                video_list.append(fl)

    video_list.sort(key=lambda x: x.get('filesize'), reverse=True)
    audio_list.sort(key=lambda x: x.get('filesize'), reverse=True)
    return video_list, audio_list


async def get_info(url: str) -> tuple:
    opts = {
        "sleep_interval_requests": random.random()
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        result = await loop.run_in_executor(_executor, ydl.extract_info, url, False)
        if "formats" in result.keys():
            title = result.get('title')
            return parse_formats(title, result.get("formats"))


def render_btn_list(url: str, videos: list, audios: list, num=5):
    video_btn = []
    audio_btn = []
    audio_dic = {}
    for a in audios:
        if a.get('ext') not in audio_dic:
            audio_dic[a.get('ext')] = a.get('format_id')
    if len(videos) > num:
        videos = videos[:num]
    for dic in videos:
        v_id = dic.get('format_id')
        a_id = audio_dic.get(dic.get('ext'))
        if not a_id:
            a_id = audios[0].get('format_id')
        video_btn.append(InlineKeyboardButton(dic['format_note'], callback_data=f"{url}||{v_id}+{a_id}"))

    if len(audios) > num - 2:
        audios = audios[:num - 2]
    for a in audios:
        a_id = a.get("format_id")
        audio_btn.append(InlineKeyboardButton(a['format_note'], callback_data=f"{url}||{a_id}"))
    return video_btn, audio_btn


def get_val_or_default(data, key):
    val = data.get(key)
    try:
        val = int(val)
    except ValueError:
        val = 0
    return val


async def download_file(download_msg=None, url='', format_id='best'):
    """
    :param download_msg: client msg obj
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
        "final_ext": f"%(ext)s",
        "trim_file_name": 50,
        "windowsfilenames": True,
        "sleep_interval": random.random()
    }
    with yt_dlp.YoutubeDL(opt) as ydl:
        result = await loop.run_in_executor(_executor, ydl.extract_info, url, True)
        saved_path = await loop.run_in_executor(_executor, ydl.prepare_filename, result)
        title = result.get('title')
        return saved_path, title


async def upload_file(saved_path, client, chat_id, title):
    bar = '=' * 20

    async def progress(current, total):
        if current != total:
            symbol = re.sub('=', '>', bar, int(current * 20 / total))

            if int(current * 100 / total) % 10 == 0:
                await asyncio.sleep(1)
                try:
                    await upload_f_msg.edit(f"{symbol} {current * 100 / total:.1f}%")
                    await client.send_chat_action(chat_id, enums.ChatAction.UPLOAD_VIDEO)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
        else:
            await upload_f_msg.delete()

    upload_f_msg = await client.send_message(chat_id, bar + " upload will start soon")
    await client.send_video(chat_id, saved_path, caption=title,
                            file_name=title, supports_streaming=True,
                            progress=progress, reply_to_message_id=chat_id
                            )


async def remove_file(file_path: str) -> bool:
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
    except FileNotFoundError as e:
        return False
