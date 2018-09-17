from datetime import datetime, timedelta
import db_functions as dbf
import extra_functions as ef
from telegram.ext import Updater, CommandHandler
from config import logging as log


f = open('token.txt', 'r')
updater = Updater(token=f.readline())
f.close()
dispatcher = updater.dispatcher

all_pl = dbf.db_select(table='players', dataframe=True)


def start(bot, update):

	bot.send_message(chat_id=update.message.chat_id, text="Iannelli suca")


def delete_not_conf_offers_by_user(user):

	try:
		old_id = dbf.db_select(
				table='offers',
				columns_in=['offer_id'],
				where='offer_user = "{}" '.format(user) +
					  'AND offer_status IS NULL')[0]

		dbf.db_delete(table='offers', where='offer_id = {}'.format(old_id))

	except IndexError:
		pass


def delete_not_conf_offers_by_others(player_id, user):

	try:
		old_ids = dbf.db_select(
				table='offers',
				columns_in=['offer_id'],
				where='offer_player_id = {} '.format(player_id) +
					  'AND offer_status IS NULL AND ' +
					  'offer_user != "{}"'.format(user))

		for old_id in old_ids:
			dbf.db_delete(table='offers', where='offer_id = {}'.format(old_id))

	except IndexError:
		pass


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


def too_late_to_offer(time_now, time_before):

	time_now = datetime.strptime(time_now, '%Y-%m-%d %H:%M:%S')
	time_before = datetime.strptime(time_before, '%Y-%m-%d %H:%M:%S')

	diff = time_now - time_before

	if diff.days > 0:
		return True
	else:
		return False


def check_offer_value(offer_id, player, dt):

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
		last_dt = '2030-01-01 00:00:00'

	if too_late_to_offer(dt, last_dt):
		dbf.db_delete(table='offers', where='offer_id = {}'.format(offer_id))

		dbf.db_update(
				table='offers',
				columns=['offer_status'],
				values=['Not Official'],
				where='offer_id = {}'.format(last_id))

		dbf.db_update(
				table='players',
				columns=['player_status'],
				values=[last_user],
				where='player_name = "{}"'.format(player))

		return ('Troppo tardi, 24 ore scadute. ' +
		        '{} acquistato da {}'.format(player, last_user))

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

	user = select_user(update)

	try:
		offer, pl, team = check_offer_format(args)
	except ValueError:
		message = check_offer_format(args)
		return bot.send_message(chat_id=update.message.chat_id, text=message)

	delete_not_conf_offers_by_user(user)

	temp = all_pl[all_pl['player_team'] == team.upper()]['player_name'].values
	if not len(temp):
		return bot.send_message(chat_id=update.message.chat_id,
		                        text='Squadra inesistente')

	pl = ef.jaccard_player(pl, temp)
	pl_id = all_pl[all_pl['player_name'] == pl].iloc[0]['player_id']
	team, roles, price = all_pl[all_pl['player_name'] == pl][
		all_pl.columns[2:-1]].values[0]

	dbf.db_insert(
			table='offers',
			columns=['offer_user', 'offer_player', 'offer_player_id',
			         'offer_price'],
			values=[user, pl, pl_id, offer])

	return bot.send_message(parse_mode='HTML',
	                        chat_id=update.message.chat_id,
							text='<i>{}</i> offre <b>{}</b> per:\n\n\t\t'.
							format(user, offer) +
							     '<b>{}   ({})   {}</b>'.
							format(pl, team, roles) +
							'\n\n/conferma')


def conferma(bot, update):

	user = select_user(update)
	dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

	try:
		of_id, pl = check_offer_to_confirm(user)
	except ValueError:
		return bot.send_message(chat_id=update.message.chat_id,
								text=check_offer_to_confirm(user))

	status = all_pl[all_pl['player_name'] == pl].iloc[0]['player_status']
	if status != 'FREE':
		dbf.db_delete(table='offers', where='offer_id = {}'.format(of_id))
		return bot.send_message(chat_id=update.message.chat_id,
								text='Giocatore non svincolato ({}).'.
								format(status))

	last_valid_offer = check_offer_value(of_id, pl, dt)
	if type(last_valid_offer) == str:
		return bot.send_message(chat_id=update.message.chat_id,
								text=last_valid_offer)

	pl_id = all_pl[all_pl['player_name'] == pl].iloc[0]['player_id']

	delete_not_conf_offers_by_others(pl_id, user)

	dbf.db_update(
			table='offers',
			columns=['offer_datetime', 'offer_status'],
			values=[dt, 'Winning'],
			where='offer_id = {}'.format(of_id))

	dbf.db_update(
			table='offers',
			columns=['offer_status'],
			values=['Lost'],
			where='offer_id = {}'.format(last_valid_offer))

	crea_riepilogo(bot, update, dt)


def crea_riepilogo(bot, update, dt_now):

	dt_now = datetime.strptime(dt_now, '%Y-%m-%d %H:%M:%S')
	message1 = 'Aste APERTE, Tempo Rimanente:\n'
	message2 = 'Aste CONCLUSE, NON Ufficializzate:\n'

	offers_win = dbf.db_select(
			table='offers',
			columns_in=['offer_id', 'offer_user', 'offer_player',
						'offer_price', 'offer_datetime'],
			where='offer_status = "Winning"')

	offers_no = dbf.db_select(
			table='offers',
			columns_in=['offer_id', 'offer_user', 'offer_player',
			            'offer_price', 'offer_datetime'],
			where='offer_status = "Not Official"')

	for of_id, tm, pl, pr, dt in offers_win:
		dt2 = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
		diff = dt_now - dt2
		if diff.days > 0:
			offers_no.append((of_id, tm, pl, pr, dt))
			dbf.db_update(
					table='offers',
					columns=['offer_status'],
					values=['Not Official'],
					where='offer_id = {}'.format(of_id))

	offers_win = [(el[0], el[1], el[2], el[3],
	               datetime.strptime(el[4], '%Y-%m-%d %H:%M:%S')) for el in
	              offers_win if el not in offers_no]

	offers_no = [(el[0], el[1], el[2], el[3],
	              datetime.strptime(el[4], '%Y-%m-%d %H:%M:%S')) for el in
	             offers_no]

	for _, tm, pl, pr, dt in offers_win:
		team, roles = dbf.db_select(
				table='players',
				columns_in=['player_team', 'player_roles'],
				where='player_name = "{}"'.format(pl))[0]
		dt_plus_one = dt + timedelta(days=1)
		diff = (dt_plus_one - dt_now).total_seconds()
		hh = diff // 3600
		mm = (diff % 3600) // 60

		message1 += ('\n\t\t- <b>{}</b> ({}) {}:'.format(pl, team, roles) +
		             ' {}, <i>{}</i>  '.format(pr, tm) +
					 ' <b>{}h:{}m</b>'.format(int(hh), int(mm)))

	for _, tm, pl, pr, dt in offers_no:
		team, roles = dbf.db_select(
				table='players',
				columns_in=['player_team', 'player_roles'],
				where='player_name = "{}"'.format(pl))[0]
		dt_plus_two = dt + timedelta(days=2)
		diff = (dt_plus_two - dt_now).total_seconds()
		hh = diff // 3600
		mm = (diff % 3600) // 60

		message2 += ('\n\t\t- <b>{}</b> ({}) {}:'.format(pl, team, roles) +
		             ' {}, <i>{}</i>  '.format(pr, tm) +
					 ' <b>{}h:{}m</b>'.format(int(hh), int(mm)))

	bot.send_message(parse_mode='HTML', chat_id=update.message.chat_id,
	                 text=message1)
	return bot.send_message(parse_mode='HTML', chat_id=update.message.chat_id,
	                        text=message2)


def riepilogo(bot, update):

	dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

	return crea_riepilogo(bot, update, dt)


def select_user(update):

	try:
		user = dbf.db_select(
				table='teams',
				columns_in=['team_name'],
				where='team_member = "{}"'.format(
						update.message.from_user.first_name))[0]
		return user

	except IndexError:
		return False


conferma_handler = CommandHandler('conferma', conferma)
offro_handler = CommandHandler('offro', offro, pass_args=True)
riepilogo_handler = CommandHandler('riepilogo', riepilogo)

dispatcher.add_handler(conferma_handler)
dispatcher.add_handler(offro_handler)
dispatcher.add_handler(riepilogo_handler)

updater.start_polling()
updater.idle()
