# ！/usr/bin/env python
# encoding:utf-8
# Created by Andy at 2022/9/3
import time
from datetime import datetime
from pathlib import Path
import yt_dlp

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def parse_formats(title: str, formats: list) -> tuple:
    """get field from  extracted info"""
    video_list, video_tag = [], []
    audio_list, audio_tag = [], []

    fields = ['format_id', 'format_note', 'filesize', 'ext', 'quality', 'height', 'width', 'language',
              'downloader_options', 'title', 'url']
    for f in formats:
        if not f['vcodec'] or not f['acodec']:
            continue
        fl = dict(zip(fields, list(map(f.get, fields))))

        if not fl.get('filesize'):
            continue
        if not fl['format_id'].isdigit():
            continue
        f['title'] = title
        if fl['downloader_options']:
            fl['chunk_size'] = fl['downloader_options'].get('http_chunk_size', 0)
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

    video_list.sort(key=lambda x: x['filesize'], reverse=True)
    audio_list.sort(key=lambda x: x['filesize'], reverse=True)
    return video_list, audio_list


def get_info(url: str) -> tuple:
    with yt_dlp.YoutubeDL() as ydl:
        result = ydl.extract_info(url, download=False)
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
    except Exception:
        val = 0
    return val


def download_file(download_msg, url, format_id):
    """
    :param download_msg: client msg obj
    :param url: video url
    :param format_id: video: 199+154, audio: 155
    :return:
    """
    start = time.time()

    def progress_hook(data):
        speed = get_val_or_default(data, 'speed') / 1024 / 1024
        eta = get_val_or_default(data, 'eta')
        downloaded = get_val_or_default(data, 'downloaded_bytes') / 1024 / 1024
        total = get_val_or_default(data, 'total_bytes') / 1024 / 1024
        download_msg.edit(
            f"Download started: {datetime.now().strftime('%H:%m:%S.%f')[:-4]} \n"
            f"Total {total:.2f}M downloaded {downloaded:.2f}M \n"
            f"Elapsed {time.time() - start:.1f}s, speed {speed:.1f}m/s, eta {eta}s"
        )

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


if __name__ == '__main__':
    url = "https://youtu.be/lWQ4SsZQAhQ"
    videos, audios = get_info(url)
