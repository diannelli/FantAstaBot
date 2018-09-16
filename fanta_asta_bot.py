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


def check_not_conf_offers_by_user(user):

    try:
        old_pl, old_offer = dbf.db_select(
                table='offers',
                columns_in=['offer_player', 'offer_price'],
                where='offer_user = "{}" '.format(user) +
                      'AND offer_status IS NULL')[0]

        team, roles = all_pl[all_pl['player_name'] == old_pl][
            all_pl.columns[2:4]].values[0]

        return ("{}, hai ancora un'offerta".format(user) +
                " in sospeso:\n\n\t\t" +
                "{}, {}    ({})    {}".format(old_offer, old_pl, team, roles) +
                "\n\n/conferma                /annulla")

    except IndexError:
        return False


def check_offer_format(args):

    message = 'Formato errato. Es: /offro 5, padoin, cag.'

    if not args:
        return 'Inserire giocatore e prezzo.'

    args = ''.join(args).split(',')

    if len(args) != 3:
        return message
    else:
        offer, pl, team = args
        try:
            int(offer)
        except ValueError:
            return message

        try:
            int(pl)
            return message
        except ValueError:
            pass

        try:
            int(team)
            return message
        except ValueError:
            pass

        return offer, pl, team


def check_offer_to_confirm(user):

    try:
        of_id, pl = dbf.db_select(
                table='offers',
                columns_in=['offer_id', 'offer_player'],
                where='offer_user = "{}" AND offer_datetime IS NULL'.
                      format(user))[0]

        return of_id, pl

    except IndexError:
        return 'Nulla da confermare per {}'.format(user)


def check_offer_value(offer_id, player):

    offer = dbf.db_select(
            table='offers',
            columns_in=['offer_price'],
            where='offer_id = {}'.format(offer_id))[0]

    price = all_pl[all_pl['player_name'] == player].iloc[0]['player_price']

    try:
        last_id, last_user, last_offer, last_dt = dbf.db_select(
                table='offers',
                columns_in=['offer_id', 'offer_user',
                            'offer_price', 'offer_datetime'],
                where='offer_player = "{}" AND '.format(player) +
                      'offer_status = "Winning"')[0]
    except IndexError:
        last_offer = 0
        last_user = ''
        last_id = 0

    if offer < last_offer:
        dbf.db_delete(table='offers', where='offer_id = {}'.format(offer_id))
        return ('Offerta troppo bassa. ' +
                'Ultimo rilancio: {}, {}'.format(last_offer, last_user))

    elif offer < price:
        dbf.db_delete(table='offers', where='offer_id = {}'.format(offer_id))
        return 'Offerta troppo bassa. Quotazione: {}'.format(price)

    else:
        return last_id


def offro(bot, update, args):

    user = select_user(bot, update)

    try:
        offer, pl, team = check_offer_format(args)
    except ValueError:
        message = check_offer_format(args)
        return bot.send_message(chat_id=update.message.chat_id, text=message)

    message = check_not_conf_offers_by_user(user)
    if message:
        return bot.send_message(chat_id=update.message.chat_id, text=message)

    temp = all_pl[all_pl['player_team'] == team.upper()]['player_name'].values
    pl = ef.jaccard_player(pl, temp)
    team, roles, price = all_pl[all_pl['player_name'] == pl][
        all_pl.columns[2:-1]].values[0]

    dbf.db_insert(
            table='offers',
            columns=['offer_user', 'offer_player', 'offer_price'],
            values=[user, pl, offer])

    return bot.send_message(chat_id=update.message.chat_id,
                            text='{} offre {} per:\n\n\t\t'.format(user,
                                                                   offer) +
                                 '{}   ({})   {}'.format(pl, team, roles) +
                            '\n\n/conferma                /annulla')


def conferma(bot, update):

    user = select_user(bot, update)
    dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        of_id, pl = check_offer_to_confirm(user)
    except ValueError:
        return check_offer_to_confirm(user)

    status = all_pl[all_pl['player_name'] == pl].iloc[0]['player_status']
    if status != 'FREE':
        return bot.send_message(chat_id=update.message.chat_id,
                                text='Giocatore non svincolato ({}).'.
                                format(status))

    last_valid_offer = check_offer_value(of_id, pl)
    if type(last_valid_offer) == str:
        return bot.send_message(chat_id=update.message.chat_id,
                                text=last_valid_offer)

    pl_id = all_pl[all_pl['player_name'] == pl].iloc[0]['player_id']
    dbf.db_update(
            table='offers',
            columns=['offer_player_id', 'offer_datetime', 'offer_status'],
            values=[pl_id, dt, 'Winning'],
            where='offer_id = {}'.format(of_id))

    dbf.db_update(
            table='offers',
            columns=['offer_status'],
            values=['Lost'],
            where='offer_id = {}'.format(last_valid_offer))


def riepilogo(bot, update):

    offers = dbf.db_select(
            table='offers',
            columns_in=['offer_user', 'offer_player',
                        'offer_price', 'offer_datetime'],
            where='offer_status = "Winning"')

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
