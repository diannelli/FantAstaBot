import pandas as pd
import os
import db_functions as dbf
from telegram import ReplyKeyboardMarkup
from telegram.ext import ConversationHandler
from telegram.ext import Updater, CommandHandler

from config import logging as log

SET_TASK, MAKE_OFFERS, CONSULT_OFFERS = range(3)

f = open('token.txt', 'r')
updater = Updater(token=f.readline())
f.close()
dispatcher = updater.dispatcher


def start(bot, update):
    """
    Start function. Displayed whenever the /start command is called.
    Start menu function.
    This will display the initial options.
    """
    keyboard = [['FAI OFFERTA', 'CONSULTA OFFERTE']]

    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard=True,
                                       resize_keyboard=True)
    update.message.reply_text(reply_markup=reply_markup)
    return SET_TASK


def main_menu(bot, update):

    user = update.message.from_user
    if update.message.text == 'FAI OFFERTA':
        return MAKE_OFFERS
    if update.message.text == 'CONSULTA OFFERTE':
        return CONSULT_OFFERS


def make_offers(bot, update):
    """
    Start function. Displayed whenever the /start command is called.
    Start menu function.
    This will display the initial options.
    """
    keyboard = [['Ruolo', 'squadra']]

    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard=True,
                                       resize_keyboard=True)
    update.message.reply_text(reply_markup=reply_markup)
    return


def consult_offers(bot, update):
    """
    Start function. Displayed whenever the /start command is called.
    Start menu function.
    This will display the initial options.
    """
    keyboard = [['sto cazzo', 'sto cazzo 2']]

    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard=True,
                                       resize_keyboard=True)
    update.message.reply_text(reply_markup=reply_markup)
    return


# def main():
#     f = open('token.txt', 'r')
#     updater = Updater(token=f.readline())
#     f.close()
#
#     # Get the dispatcher to register handlers:
#     dp = updater.dispatcher
#
#     # Add conversation handler with predefined states:
#     conv_handler = ConversationHandler(
#         entry_points=[CommandHandler('start', start)],
#
#         states={
#             SET_TASK : [CommandHandler('main_menu', main_menu)],
#
#             MAKE_OFFERS: [CommandHandler('make_offers', make_offers)],
#
#             CONSULT_OFFERS: [CommandHandler('make_offers', consult_offers)]
#         },
#
#         fallbacks=[CommandHandler('help', help)]
#     )
#
#     dp.add_handler(conv_handler)
#
#     # Log all errors:
#     # dp.add_error_handler(error)
#     logger = log.set_logging()
#
#     # Start DisAtBot:
#     updater.start_polling()
#
#     # Run the bot until the user presses Ctrl-C or the process
#     # receives SIGINT, SIGTERM or SIGABRT:
#     updater.idle()


# if __name__ == '__main__':
#     main()

updater.start_polling()
updater.idle()
