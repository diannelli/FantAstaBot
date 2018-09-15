import pandas as pd
import os
from datetime import datetime
import db_functions as dbf
import extra_functions as ef
from telegram import ReplyKeyboardMarkup
from telegram.ext import ConversationHandler
from telegram.ext import Updater, CommandHandler
from config import logging as log

SET_TASK, MAKE_OFFERS, CONSULT_OFFERS = range(3)

f = open('token.txt', 'r')
updater = Updater(token=f.readline())
f.close()
dispatcher = updater.dispatcher

all_pl = dbf.db_select(table='players', dataframe=True)


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


def offro(bot, update, args):

    message = 'Formato errato. Es: /offro 5, padoin, cag.'
    user = select_user(bot, update)

    if not args:
        return bot.send_message(chat_id=update.message.chat_id,
                                text='Inserire giocatore e prezzo.')

    args = ''.join(args).split(',')

    if len(args) != 3:
        return bot.send_message(chat_id=update.message.chat_id,
                                text=message)
    else:
        offer, pl, team = args
        try:
            offer = int(offer)
        except ValueError:
            return bot.send_message(chat_id=update.message.chat_id,
                                    text=message)

        try:
            pl = int(pl)
            return bot.send_message(chat_id=update.message.chat_id,
                                    text=message)
        except ValueError:
            pass

        try:
            team = int(team)
            return bot.send_message(chat_id=update.message.chat_id,
                                    text=message)
        except ValueError:
            pass

        temp = all_pl[all_pl['player_team'] == team.upper()]
        pl = ef.jaccard_player(pl, temp['player_name'].values)
        team, roles, price = all_pl[all_pl['player_name'] == pl][
            all_pl.columns[2:-1]].values[0]

        dbf.db_insert(
                table='offers',
                columns=['offer_user', 'offer_player', 'offer_price'],
                values=[user, pl, offer])

        return bot.send_message(chat_id=update.message.chat_id,
                                text='{}   ({})   {}'.format(pl, team, roles) +
                                '\n\n/conferma                /annulla')


def conferma(bot, update):

    user = select_user(bot, update)

    try:
        of_id, pl = dbf.db_select(
            table='offers',
            columns_in=['offer_id', 'offer_player'],
            where='offer_user = "{}" AND offer_datetime IS NULL'.
            format(user))[0]
    except IndexError:
        return bot.send_message(chat_id=update.message.chat_id,
                                text='Non ci sono offerte da confermare ' +
                                'per {}'.format(user))

    status = all_pl[all_pl['player_name'] == pl].iloc[0]['player_status']
    if status != 'FREE':
        return bot.send_message(chat_id=update.message.chat_id,
                                text='Giocatore non svincolato ({}).'.
                                format(status))

    offer = dbf.db_select(
            table='offers',
            columns_in=['offer_price'],
            where='offer_id = {}'.format(of_id))[0]

    price = all_pl[all_pl['player_name'] == pl].iloc[0]['player_price']
    if offer < price:
        return bot.send_message(chat_id=update.message.chat_id,
                                text='Offerta troppo bassa. ' +
                                     'Quotazione: {}'.format(price))
    else:
        pl_id = all_pl[all_pl['player_name'] == pl].iloc[0]['player_id']
        dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        dbf.db_update(
                table='offers',
                columns=['offer_player_id', 'offer_datetime', 'offer_status'],
                values=[pl_id, dt, 'Open'],
                where='offer_id = {}'.format(of_id))


def riepilogo(bot, update):

    offers = dbf.db_select(
            table='offers',
            columns_in=['offer_user', 'offer_player',
                        'offer_price', 'offer_datetime'],
            where='offer_status = "Open"')

    return


def select_user(bot, update):

    try:
        user = dbf.db_select(
                table='teams',
                columns_in=['team_name'],
                where='team_member = "{}"'.format(
                        update.message.from_user.first_name))[0]
        return user

    except IndexError:
        return False


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


conferma_handler = CommandHandler('conferma', conferma)
offro_handler = CommandHandler('offro', offro, pass_args=True)
riepilogo_handler = CommandHandler('riepilogo', riepilogo)

dispatcher.add_handler(conferma_handler)
dispatcher.add_handler(offro_handler)
dispatcher.add_handler(riepilogo_handler)

updater.start_polling()
updater.idle()
