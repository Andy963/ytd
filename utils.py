# ！/usr/bin/env python
# encoding:utf-8
# Created by Andy at 2022/9/3
import asyncio
import math
import os
import random
import re
from pathlib import Path

import yt_dlp
from pyrogram import enums
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton

start = 0
prev = 0
upload_loop = None


def parse_formats(title: str, formats: list) -> tuple:
    """get field from  extracted info"""
    hight_v = ['4320p', '2160p', '1440p']
    video_list, video_tag = [], []
    audio_list, audio_tag = [], []

    fields = ['format_id', 'format_note', 'filesize', 'ext', 'quality', 'height', 'width', 'language',
              'downloader_options', 'title', 'acodec', 'vcodec']
    format_infos = [dict(zip(fields, list(map(f.get, fields)))) for f in formats]

    for fl in format_infos:
        if not fl.get('filesize') or not str(fl.get('filesize')).isdigit():
            continue
        fl['filesize'] = math.ceil(fl.get('filesize') / 1000 / 1000)
        if fl.get('filesize') > 2000:
            continue
        if fl.get('ext') not in ['mp4', 'mkv', 'webm', 'm4a', 'mp3', 'wav']:
            continue
        # audio has no height and width
        if not fl.get('height') and not fl.get('width'):
            if fl.get('format_note') not in audio_tag:
                audio_list.append(fl)
                audio_tag.append(fl.get('format_note'))
        elif fl.get('height') and fl.get('width'):
            f_note = fl.get('format_note')
            f_note = f_note.lower()
            if f_note.endswith('p'):
                f_note = f_note.split('p')[0] + 'p'
            if f_note not in video_tag:
                video_tag.append(f_note)
                fl['format_note'] = f_note
                video_list.append(fl)
            else:
                if fl.get('quality') > video_list[video_tag.index(f_note)].get('quality'):
                    video_list[video_tag.index(f_note)] = fl

    video_list.sort(key=lambda x: x.get('quality'), reverse=True)
    audio_list.sort(key=lambda x: x.get('filesize'), reverse=True)
    return video_list, audio_list


async def get_info(url: str) -> tuple:
    opts = {
        "sleep_interval_requests": random.random()
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, ydl.extract_info, url, False)
        if "formats" in result.keys():
            title = result.get('title')
            return parse_formats(title, result.get("formats"))


def render_btn_list(url: str, videos: list, audios: list, num=3):
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
        video_btn.append(
            InlineKeyboardButton(f"{dic['format_note']}({dic['filesize']}M)", callback_data=f"{url}||{v_id}+{a_id}"))

    if len(audios) > num:
        audios = audios[:num]
    for a in audios:
        a_id = a.get("format_id")
        audio_btn.append(InlineKeyboardButton(f"{a['format_note']}({a['filesize']}M)", callback_data=f"{url}||{a_id}"))
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

    loop = asyncio.get_event_loop()

    opt = {
        "username": '',
        "password": '',
        "format": format_id,
        "format_id": format_id,
        "outtmpl": "%(title)s.%(ext)s",
        "noplaylist": True,
        "writethumbnail": False,
        "final_ext": "%(ext)s",
        "trim_file_name": 50,
        "windowsfilenames": True,
        "sleep_interval": random.random(),
    }
    with yt_dlp.YoutubeDL(opt) as ydl:
        result = await loop.run_in_executor(None, ydl.extract_info, url, True)
        saved_path = await loop.run_in_executor(None, ydl.prepare_filename, result)
        title = result.get('title')
        return saved_path, title


async def upload_file(saved_path, client, chat_id, title):
    bar = '=' * 20
    upload_loop = asyncio.get_event_loop()
    start = upload_loop.time()
    prev = 0

    async def progress(current, total):
        global start, prev
        if current != total:
            symbol = re.sub('=', '>', bar, int(current * 20 / total))

            if int(current * 100 / total) % 10 == 0:
                await asyncio.sleep(0.1)
                upload_loop = asyncio.get_event_loop()
                try:
                    speed = ((current - prev) / (1024 * 1024)) / (upload_loop.time() - start)
                    await upload_f_msg.edit(
                        f"{symbol} {current * 100 / total:.2f}% {speed:.2f}MB/s Total {total / 1024 / 1024:.2f}MB")
                    await client.send_chat_action(chat_id, enums.ChatAction.UPLOAD_VIDEO)
                    prev = current
                    start = upload_loop.time()
                except FloodWait as e:
                    await asyncio.sleep(e.value)
        else:
            await upload_f_msg.delete()

    upload_f_msg = await client.send_message(chat_id, bar + " upload will start soon", disable_notification=True)
    _, ext = os.path.splitext(saved_path)
    await client.send_video(chat_id, saved_path, caption=title,
                            file_name=f"{title}{ext}", supports_streaming=True,
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
