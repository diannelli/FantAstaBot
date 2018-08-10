from telegram.ext import Updater, CommandHandler, MessageHandler, RegexHandler
from telegram.ext import ConversationHandler, CallbackQueryHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import logging
import logging.config

MAKE_OFFERS, READ_OFFERS = range(2)


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


def start(bot, update):
    """
    Start function. Displayed whenever the /start command is called.
    This function sets the language of the bot.
    """
    # Create buttons to slect language:
    keyboard = [['FAI OFFERTA', 'CONSULTA OFFERTE']]

    # Create initial message:
    message = "Hey, I'm FantAstaBot"

    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard=True,
                                       resize_keyboard=True)
    update.message.reply_text(message, reply_markup=reply_markup)

    return SET_LANG


def set_lang(bot, update):
    """
    First handler with received data to set language globally.
    """
    # Set language:
    global LANG
    LANG = update.message.text
    user = update.message.from_user

    # logger.info("Language set by {} to {}.".format(user.first_name, LANG))
    update.message.reply_text(lang_selected[LANG],
                            reply_markup=ReplyKeyboardRemove())

    return MENU


f = open('token.txt', 'r')
updater = Updater(token=f.readline())
f.close()

# Get the dispatcher to register handlers:
dp = updater.dispatcher

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],

    states={
        SET_LANG: [CommandHandler('set_lang', set_lang)]
    },

    fallbacks=[CommandHandler('cancel', set_lang),
               CommandHandler('help', help)]
)

dp.add_handler(conv_handler)

# Log all errors:
# dp.add_error_handler(error)

# Start DisAtBot:
updater.start_polling()

# Run the bot until the user presses Ctrl-C or the process
# receives SIGINT, SIGTERM or SIGABRT:
updater.idle()
