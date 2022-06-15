from pathlib import Path

import yt_dlp

from config import config,log


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
                if pt.name in str(file):
                    file.unlink()
        log.info(f"remove {file_path} success")
        return True
    except Exception as err:
        log.error(f"remove {file_path} with err: {err}")
        return False



def download_video(url_obj):
    log.info("start download video")
    with yt_dlp.YoutubeDL(config["video_options"]) as ydl:
        try:
            result = ydl.extract_info("{}".format(url_obj.url))
            title = result.get('title', 'no_title')
            saved_path = ydl.prepare_filename(result)
            ydl.download([url_obj.url])
            with open(saved_path, 'rb') as fp:
                upload_result = url_obj.client.send_video(url_obj.message.chat.id, fp, caption=title,
                                                      file_name=title, supports_streaming=True,
                                                      )
            log.info(f"upload {title} success")
            remove_file(saved_path)
        except Exception as err:
            log.error(f"extract_info with err:{err}")
