from telegram.ext import Updater
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, bot, update,ReplyKeyboardMarkup
import logging
import logging.config
import yaml

def set_logging():
    '''Logging configuration with a YAML format configuration file.
    flogger writes on logs/bet_bot.log file
    and RotatingFileHandler allows to rollover file
    at a predetermined size (maxBytes)'''

    flogger = get_flogger()
    return flogger

def get_flogger():
    '''Returns a flogger instance'''
    flogger = logging.getLogger('flogger')
    return flogger

def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu

f = open('token.txt', 'r')
updater = Updater(token=f.readline())
f.close()
#
# dispatcher = updater.dispatcher
#
# logger = set_logging()
# updater.start_polling()
# logger.info('Bet_Bot started.')
# updater.idle()
chat_id = update.Message.chat_id

custom_keyboard = [["top-left", "top-right"],
                   ["bottom-left", "bottom-right"]]
reply_markup = ReplyKeyboardMarkup(custom_keyboard)
updater.bot.send_message(chat_id=chat_id,
                 text="Custom Keyboard Test",
                 reply_markup=reply_markup)
