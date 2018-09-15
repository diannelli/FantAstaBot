import pandas as pd
from pandas import ExcelWriter
import os
import db_functions as dbf
from nltk.metrics.distance import jaccard_distance
from nltk.util import ngrams


def jaccard_player(input_player, all_players):

	"""
	Find the most similar team in the db in case it is misspelled by the user.

	:param input_player: str

	:param all_players: list of str


	:return: str
	"""

	dist = 10
	tri_guess = set(ngrams(input_player.upper(), 3))
	jac_player = ''

	for pl in all_players:
		trit = set(ngrams(pl, 3))
		jd = jaccard_distance(tri_guess, trit)
		if not jd:
			return pl
		elif jd < dist:
			dist = jd
			jac_player = pl

	return jac_player


def map_file_asta():

	asta = pd.read_excel(os.getcwd() + '/Asta2018.xlsx',
	                     header=0, sheet_name="Foglio1")
	players = dbf.db_select(
			table='players',
			columns_in=['player_name', 'player_team'],
			dataframe=True)

	for i in range(0, len(asta.columns), 3):
		temp_pl = asta[asta.columns[i:i+3]].dropna()
		for j in range(len(temp_pl)):
			pl, tm = temp_pl.loc[j, temp_pl.columns[0:2]]
			flt_df = players[players['player_team'] == tm.upper()]
			names = flt_df['player_name'].values
			correct_pl = jaccard_player(pl, names)
			asta.loc[j, [asta.columns[i],
			             asta.columns[i+1]]] = correct_pl, tm.upper()
		pass

	writer = ExcelWriter('Asta2018_2.xlsx', engine='openpyxl')
	asta.to_excel(writer, sheet_name='Foglio1')
	writer.save()
	writer.close()


def update_quotazioni():

	dbf.empty_table('players')

	players = pd.read_excel(os.getcwd() + '/Quotazioni.xlsx',
	                        sheet_name="Tutti", usecols=[1, 2, 3, 4])

	for i in range(len(players)):
		role, name, team, price = players.iloc[i].values
		dbf.db_insert(
				table='players',
				columns=['player_name', 'player_team',
				         'player_roles', 'player_price'],
				values=[name, team[:3].upper(), role, price])

	del players

	asta = pd.read_excel(os.getcwd() + '/Asta2018.xlsx',
	                     sheet_name="Foglio1-1", usecols=range(0, 24, 3))

	for team in asta.columns:
		pls = asta[team].dropna()
		for pl in pls:
			dbf.db_update(
					table='players',
					columns=['player_status'],
					values=[team], where='player_name = "{}"'.format(pl))

	dbf.db_update(
			table='players',
			columns=['player_status'],
			values=['FREE'], where='player_status IS NULL')
	return


update_quotazioni()
