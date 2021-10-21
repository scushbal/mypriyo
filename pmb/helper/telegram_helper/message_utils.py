from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from telegram.message import Message
from telegram.update import Update
import time
import psutil
import shutil
from pmb import dispatcher, AUTO_DELETE_MESSAGE_DURATION, LOGGER, bot, \
    status_reply_dict, status_reply_dict_lock, download_dict, download_dict_lock
from pmb.helper.ext_utils.bot_utils import get_readable_message, get_readable_file_size, MirrorStatus
from telegram.error import TimedOut, BadRequest

def sendMessage(text: str, bot, update: Update):
    try:
        return bot.send_message(update.message.chat_id,
                            reply_to_message_id=update.message.message_id,
                            text=text, parse_mode='HTMl')
    except Exception as e:
        LOGGER.error(str(e))


def sendMarkup(text: str, bot, update: Update, reply_markup: InlineKeyboardMarkup):
    try:
        return bot.send_message(update.message.chat_id,
                             reply_to_message_id=update.message.message_id,
                             text=text, reply_markup=reply_markup, parse_mode='HTMl')
    except Exception as e:
        LOGGER.error(str(e))


def editMessage(text: str, message: Message, reply_markup=None):
    try:
        bot.edit_message_text(text=text, message_id=message.message_id,
                              chat_id=message.chat.id,reply_markup=reply_markup,
                              parse_mode='HTMl')
    except Exception as e:
        LOGGER.error(str(e))


def deleteMessage(bot, message: Message):
    try:
        bot.delete_message(chat_id=message.chat.id,
                           message_id=message.message_id)
    except Exception as e:
        LOGGER.error(str(e))


def sendLogFile(bot, update: Update):
    with open('log.txt', 'rb') as f:
        bot.send_document(document=f, filename=f.name,
                          reply_to_message_id=update.message.message_id,
                          chat_id=update.message.chat_id)


def auto_delete_message(bot, cmd_message: Message, bot_message: Message):
    if AUTO_DELETE_MESSAGE_DURATION != -1:
        time.sleep(AUTO_DELETE_MESSAGE_DURATION)
        try:
            # Skip if None is passed meaning we don't want to delete bot xor cmd message
            deleteMessage(bot, cmd_message)
            deleteMessage(bot, bot_message)
        except AttributeError:
            pass


def delete_all_messages():
    with status_reply_dict_lock:
        for message in list(status_reply_dict.values()):
            try:
                deleteMessage(bot, message)
                del status_reply_dict[message.chat.id]
            except Exception as e:
                LOGGER.error(str(e))


def update_all_messages():
    total, used, free = shutil.disk_usage('.')
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    msg = get_readable_message()
    msg += f"<b>🖥️ CPU:</b> {psutil.cpu_percent()}%" \
           f"<b>🚀 RAM:</b> {psutil.virtual_memory().percent}%" \
           f"<b>📦 DISK:</b> {psutil.disk_usage('/').percent}%"
    with download_dict_lock:
        dlspeed_bytes = 0
        uldl_bytes = 0
        for download in list(download_dict.values()):
            speedy = download.speed()
            if download.status() == MirrorStatus.STATUS_DOWNLOADING:
                if 'KiB/s' in speedy:
                    dlspeed_bytes += float(speedy.split('K')[0]) * 1024
                elif 'MiB/s' in speedy:
                    dlspeed_bytes += float(speedy.split('M')[0]) * 1048576 
            if download.status() == MirrorStatus.STATUS_UPLOADING:
                if 'KB/s' in speedy:
            	    uldl_bytes += float(speedy.split('K')[0]) * 1024
                elif 'MB/s' in speedy:
                    uldl_bytes += float(speedy.split('M')[0]) * 1048576
        dlspeed = get_readable_file_size(dlspeed_bytes)
        ulspeed = get_readable_file_size(uldl_bytes)
        msg += f"\n<b>USED:</b> {used} | <b>FREE:</b> {free}\n<b>DL:</b> {dlspeed}ps 🔻 | <b>UL:</b> {ulspeed}ps 🔺\n"
    with status_reply_dict_lock:
        for chat_id in list(status_reply_dict.keys()):
            if status_reply_dict[chat_id] and msg != status_reply_dict[chat_id].text:
                if len(msg) == 0:
                    msg = "Starting DL"
                try:
                    keyboard = [[InlineKeyboardButton("🔄 REFRESH 🔄", callback_data=str(ONE)),
                                 InlineKeyboardButton("❌ CLOSE ❌", callback_data=str(TWO)),]]
                    editMessage(msg, status_reply_dict[chat_id], reply_markup=InlineKeyboardMarkup(keyboard))
                except Exception as e:
                    LOGGER.error(str(e))
                status_reply_dict[chat_id].text = msg
                
                
ONE, TWO = range(2)

def refresh(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="Refreshing...")
    time.sleep(2)
    update_all_messages()

def close(update, context):
    query = update.callback_query
    query.answer()
    delete_all_messages()


def sendStatusMessage(msg, bot):
    total, used, free = shutil.disk_usage('.')
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    progress = get_readable_message()
    progress += f"<b>🖥 CPU:</b> {psutil.cpu_percent()}%\n" \
                f"<b>🚀 RAM:</b> {psutil.virtual_memory().percent}%\n" \
                f"<b>📦 DISK:</b> {psutil.disk_usage('/').percent}%\n"
    with download_dict_lock:
        dlspeed_bytes = 0
        uldl_bytes = 0
        for download in list(download_dict.values()):
            speedy = download.speed()
            if download.status() == MirrorStatus.STATUS_DOWNLOADING:
                if 'KiB/s' in speedy:
                    dlspeed_bytes += float(speedy.split('K')[0]) * 1024
                elif 'MiB/s' in speedy:
                    dlspeed_bytes += float(speedy.split('M')[0]) * 1048576 
            if download.status() == MirrorStatus.STATUS_UPLOADING:
                if 'KB/s' in speedy:
            	    uldl_bytes += float(speedy.split('K')[0]) * 1024
                elif 'MB/s' in speedy:
                    uldl_bytes += float(speedy.split('M')[0]) * 1048576
        dlspeed = get_readable_file_size(dlspeed_bytes)
        ulspeed = get_readable_file_size(uldl_bytes)
        progress += f"\n<b>USED:</b> {used} | <b>FREE:</b> {free}\n<b>DL:</b> {dlspeed}ps 🔻 | <b>UL:</b> {ulspeed}ps 🔺\n"
    with status_reply_dict_lock:
        if msg.message.chat.id in list(status_reply_dict.keys()):
            try:
                message = status_reply_dict[msg.message.chat.id]
                deleteMessage(bot, message)
                del status_reply_dict[msg.message.chat.id]
            except Exception as e:
                LOGGER.error(str(e))
                del status_reply_dict[msg.message.chat.id]
        message = sendMessage(progress, bot, msg)
        status_reply_dict[msg.message.chat.id] = message
        
dispatcher.add_handler(CallbackQueryHandler(refresh, pattern='^' + str(ONE) + '$'))
dispatcher.add_handler(CallbackQueryHandler(close, pattern='^' + str(TWO) + '$'))         
