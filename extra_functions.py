import os
import pandas as pd
import db_functions as dbf
from pandas import ExcelWriter
from nltk.metrics.distance import jaccard_distance
from nltk.util import ngrams


def jaccard_player(input_player, all_players):

	"""
	Trova il giocatore corrispondente a quello inserito dall'user.

	:param input_player: str

	:param all_players: list of str


	:return jac_player: str

	"""

	dist = 10
	tri_guess = set(ngrams(input_player.upper(), 3))
	jac_player = ''

	for pl in all_players:
		p = pl.replace(' ', '')
		trit = set(ngrams(p, 3))
		jd = jaccard_distance(tri_guess, trit)
		if not jd:
			return pl
		elif jd < dist:
			dist = jd
			jac_player = pl

	return jac_player


def jaccard_team(input_team, all_teams):

	"""
	Trova il giocatore corrispondente a quello inserito dall'user.

	:param input_player: str

	:param all_players: list of str


	:return jac_player: str

	"""

	dist = 10
	tri_guess = set(ngrams(input_team[:3].upper(), 2))
	jac_team = ''

	for tm in all_teams:
		p = tm.replace(' ', '')
		trit = set(ngrams(p, 2))
		jd = jaccard_distance(tri_guess, trit)
		if not jd:
			return tm
		elif jd < dist:
			dist = jd
			jac_team = tm

	return jac_team


def correggi_file_asta():

	"""
	Crea una copia del file originale contenente le rose definite il giorno
	dell'asta ma con i nomi dei calciatori corretti secondo il formato di
	Fantagazzetta.

	"""

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


def quotazioni_iniziali():

	"""
	Dopo averla svuotata, riempie la tabella "players" del db con tutti i dati
	relativi a ciascun giocatore ad inizio campionato.

	"""

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


def aggiorna_status_calciatori():

	"""
	Aggiorna lo status di ogni calciatore nella tabella "players" del db.
	Lo status sarà la fantasquadra proprietaria del giocatore mentre ogni
	giocatore svincolato avrà status = FREE.

	"""

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


def aggiorna_db_con_nuove_quotazioni():

	"""
	Aggiorna tutte le quotazioni dei calciatori prima di ogni mercato.
	Gestisce anche i trasferimenti interni alla Serie A aggiornando la
	squadra di appartenenza e l'arrivo di nuovi calciatori.

	"""

	mercati = ['PrimoMercato', 'SecondoMercato', 'TerzoMercato']

	last = ''

	for i in mercati:
		name = os.getcwd() + '/Quotazioni_' + i + '.xlsx'
		if os.path.isfile(name):
			last = name

	players = pd.read_excel(last, sheet_name="Tutti", usecols=[1, 2, 3, 4])

	for x in range(len(players)):
		role, pl, team, price = players.iloc[x].values

		if pl in players['Nome'].values:
			dbf.db_update(
					table='players',
					columns=['player_team', 'player_price'],
					values=[team[:3].upper(), price],
					where='player_name = "{}"'.format(pl))
		else:
			dbf.db_insert(
					table='players',
					columns=['player_name', 'player_team',
					         'player_roles', 'player_price'],
					values=[pl, team[:3].upper(), role, price])

	del players


# 1) Scaricare le quotazioni di tutti i giocatori dal sito di Fantagazzetta e
#    salvarle all'interno della cartella del bot con il nome "Quotazioni.xlsx".


# 2) Ad asta conclusa, salvare il file con tutte le rose all'interno della
#    cartella del bot con il nome "Asta2018.xlsx". Aggiornare inoltre il db con
#    i corretti nomi delle 8 squadre partecipanti ed accertarsi siano uguali a
#    quelli presenti nel file "Asta2018.xlsx". Aggiornare anche i budgets
#    post-asta di ciascuna squadra all'interno del db.


# 3) Lanciare le funzioni:
# quotazioni_iniziali()
# correggi_file_asta()


# 4) A questo punto nella cartella ci sarà un nuovo file chiamato
#    "Asta2018_2.xlsx". Copiare la tabella in esso contenuta ed incollarla in
#    un secondo Foglio di calcolo appositamente creato nel file originale
#    "Asta2018.xlsx". Il nuovo Foglio di calcolo dovrà chiamarsi "Foglio1-1".


# 5) Lanciare la funzione:
# aggiorna_status_calciatori()


# 6) Prima di ogni mercato, scaricare il nuovo Excel con le quotazioni
#    aggiornate, salvarlo con il nome relativo al mercato in questione (Esempio
#    "Quotazioni_PrimoMercato.xlsx") e lanciare la funzione:
# aggiorna_db_con_nuove_quotazioni()


# 7) Utilizzare il bot per il mercato.
