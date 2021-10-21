from telegram.ext import CommandHandler
from pmb.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from pmb import LOGGER, dispatcher
from pmb.helper.telegram_helper.message_utils import sendMessage, sendMarkup, editMessage
from pmb.helper.telegram_helper.filters import CustomFilters
import threading
from pmb.helper.telegram_helper.bot_commands import BotCommands

def list_drive(update,context):
    try:
        search = update.message.text.split(' ',maxsplit=1)[1]
        LOGGER.info(f"Searching: {search}")
        reply = sendMessage('🔍 Searching..... ✋ Please Wait!', context.bot, update)
        gdrive = GoogleDriveHelper(None)
        msg, button = gdrive.drive_list(search)

        if button:
            editMessage(msg, reply, button)
        else:
            editMessage('🚫 No results found', reply)

    except IndexError:
        sendMessage('Send a search key along with command', context.bot, update)


list_handler = CommandHandler(BotCommands.ListCommand, list_drive,filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
dispatcher.add_handler(list_handler)
