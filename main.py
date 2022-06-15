# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor
import validators
from pyrogram import Client, filters
from config import config,log
from server import  download_video

app = Client("Downloader", config["app_id"], config["app_hash"], bot_token=config["token"] )
video_pattern = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
pool = ThreadPoolExecutor(max_workers=4)
future_msg_map = {}


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


class UrlObj:
    def __init__(self, message, client, url):
        self.message = message
        self.client = client
        self.url = url
        self.status = 'pending'

def remove_tips(future):
    info = future_msg_map.get(future)
    tips = info.get("tips")
    if tips:
        tips.delete()
    future_msg_map.pop(future)


@app.on_message(filters.regex(video_pattern))
def webpage(client, message):
    url = message.text
    if validators.url(url):
        log.info(f"start downloading url:{url}")
        url_obj = UrlObj(message, client, url)
        tips = client.send_message(message.chat.id, "you task is in line,please wait!")
        video_future = pool.submit(download_video,url_obj)
        future_msg_map[video_future] = {"tips":tips}
        video_future.add_done_callback(remove_tips)
    else:
        # get real url failed, response with err.
        log.error(f"Invalid url:{url}")
        client.send_message(message.chat.id, f"invalid url")


if __name__ == '__main__':
    app.run()
