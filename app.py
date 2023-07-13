import shutil
from pathlib import Path

import yt_dlp
from telegram import Update, Message
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes
from telegram.ext import filters, CommandHandler, \
    MessageHandler, Application

import config


# 下载命令处理函数
async def download(url: str, context: ContextTypes.DEFAULT_TYPE, tip: Message):
    # 选择视频+音频格式

    opt = {
        'outtmpl': '%(title)s.%(ext)s',
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]',
        'embedthumbnail': True,
        'rm_thumbnail': True,
        'merge_output_format': 'mp4',
    }

    with yt_dlp.YoutubeDL(opt) as ydl:
        info_dict = ydl.extract_info(url, download=True)
    title = info_dict.get('title', 'No title found')

    # 获取转换后的音频文件名
    filename = ydl.prepare_filename(info_dict)
    cur_path = Path(filename).absolute()
    if cur_path.parent != Path(config.download_path):
        shutil.move(cur_path, config.download_path)
    return title, filename


command_list = [('start', 'Starts the bot'),
                ]


async def init_menu(app: Application) -> None:
    """init menu commands"""
    await app.bot.set_my_commands(command_list)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> \
        None:
    reply_text = "Hi! I'm An Youtube Download Bot🤖\n\n Now you " \
                 "can send me a youtube link to download it."
    await update.message.reply_text(reply_text, parse_mode=ParseMode.HTML)


async def message_handler(update: Update,
                          context: ContextTypes.DEFAULT_TYPE) -> None:
    new_msg = await update.message.reply_text(
        text=update.message.text,
        disable_notification=True,
        disable_web_page_preview=True
    )
    await update.message.delete()
    tip_message = await context.bot.send_message(
        text="Download will start soon, please wait...",
        disable_notification=True,
        chat_id=update.message.chat_id, parse_mode=ParseMode.HTML)
    try:
        title, filename = await download(update.message.text, context,
                                         tip_message)
        await update.message.reply_text(
            text=f"Download success!  ✅\n"
                 f"\t <pre>{update.message.text} </pre>\n\n"
                 f"\t {title}\n",
            disable_notification=True,
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML
        )
        await new_msg.delete()
        await tip_message.delete()
    except Exception as e:
        await context.bot.edit_message_text(
            text=f"{update.message.text}\n\n"
                 f"Sorry, something went wrong.\n {e}",
            chat_id=update.message.chat_id,
            message_id=tip_message.message_id,
            disable_web_page_preview=True
        )


application = (
    ApplicationBuilder()
    .token(config.telegram_token)
    .post_init(init_menu)
    .build()
)


def main():
    if len(config.allowed_telegram_usernames) == 0:
        user_filter = filters.ALL
    else:
        user_filter = filters.User(username=config.allowed_telegram_usernames)
    application.add_handler(
        CommandHandler("start", start_handler, filters=user_filter))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & user_filter,
                       message_handler))
    application.run_polling()


if __name__ == '__main__':
    main()
