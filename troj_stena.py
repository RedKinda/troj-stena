import discord
import time
import asyncio
import requests
import re
import pickle
import lxml
import lxml.etree
from datetime import datetime
import shlex
#from aioconsole import ainput

commands = asyncio.Queue()

ready = False
client = discord.Client()

def log(message, type='info'):
	types = {
		'info'		:	'\033[0m',
		'ok'		:	'\033[92m',
		'proces'	:	'\033[95m',
		'error'		:	'\033[1;[91m',
		'warning'	:	''
	}
	try:
		print('{0}{1}{2}'.format(types[type],message,types['info']))
	except:
		print("{0}Type not found.{1}".format(types['error'],types['info']))

id_bank = {"botrole"			:	598502023079657483,
		   "zaujimave-ulohy"	:	598522778743734342,
		   "timeOut role"		:	598815157975515147,
		   "misko emoji"		:	598820789168373778,
		   "solved emoji"		:	598782166121316363,
		   "cheatalert emoji"	:	599242099207962635,
		   "moderating channel"	:	599249382038044703,
		   "questionable emoji"	:	599248755186728966,
		   "thup emoji"			:	598508913372954634,
		   "thdown emoji"		:	598509040540057600,
		   "badin emoji"		:	598483292034957312,
		   "ksprole"			:	600750067929841736,
		   "kspemoji"			:	600745214080188448,
		   "kmsrole"			:	600750035801604184,
		   "kmsemoji"			:	600745723650113571,
		   "fksrole"			:	600750477289848836,
		   "fksemoji"			:	600745115258060800,
		   "praskrole"			:	600750779447509002,
		   "praskemoji"			:	600744451861774356,
		   "uforole"			:	600750981483069458,
		   "ufoemoji"			:	600744527631745026,
		   "MvKal"				:	332935845004705793,
		   "voting channel"		:	600688938562093058,
		   "welcome channel"	:	600944280650907678,
		   "dev channel"		: 	598490170236338176,
		   "adminrole"			:	598478860824346624,
		   "veduckorole"		:	598517418968743957,
		   "admin channel"		:	600384787433259010,
		   "whiterole"			:	601106902398533632,
		   "orangerole"			:	601098919275135007,
		   "greenrole"			:	601099061696659456,
		   "bluerole"			:	601098701536231434,
		   "testing channel"	:	601160389736136737
		   }


@client.event
async def on_ready():
	global warnings
	global weird_messages
	global botrole
	global trojsten
	global timeouts
	global ready
	global seminars
	global filehandler
	global subscribes
	global udaje

	ready = True
	print("\033[1m I am ready as", client.user.name + "#" + str(client.user.discriminator))
	trojsten = client.get_guild(598476317758849024) #trojsten server
	botrole = trojsten.get_role(id_bank["botrole"])
	warnings = {}
	subscribes = {}
	timeouts = {}
	weird_messages = {}
	filehandler = open('information.dat', 'wb+')
	try:			#loading seminarsi
		reader = open('information.dat', 'rb')
		seminars = pickle.load(reader)
		reader.close()
	except EOFError: #if there is no file, create them
		seminars = [Seminar("kms", 598481957285920778, "https://kms.sk"),
					Seminar("ksp", 598481977938542603, "https://ksp.sk"),
					Seminar("fks", 598482014324129803, "https://fks.sk"),
					Seminar("ufo", 598482065708548126, "https://ufo.fks.sk"),
					Seminar("prask", 598482110616961054, "https://prask.ksp.sk")]
		#Debug web gathering --> print first contestant in result table for seminar x
		#print(seminars[1].result_table[0].print_contents())
		pickle.dump(seminars, filehandler)
	for sem in seminars:
		sem.m_channel = client.get_channel(sem.m_channel)
	#for s in seminars:
	#	await s.voting("release")
	udaje = {'pravidla' : ["Správame sa slušne, rešpektujeme ostatných, nespamujeme, nepoužívame zbytočne ‘@ everyone’ a všetko čo by rozum napovedal.",
				"Rešpektujeme pokyny adminov.",
				"O riešeniach úloh je povolené sa baviť až keď sú zverejnené vzoráky."],

	'faq' : [["Som prvýkrát na discorde o čom to tu je?","Skús pohľadať na internete, krátke: <https://www.youtube.com/watch?v=aYSQB0fUzv0>\nDlhšie: <https://www.youtube.com/watch?v=le_CE--Mnvs>"]]}
	f = open('content.dat', 'wb+')
	try:			#loading seminarsi
		reader = open('content.dat', 'rb')
		udaje = pickle.load(reader)
		reader.close()
	except EOFError: #if there is no file, create them
		pickle.dump(udaje,f)
	await welcome_message()
	await role_message()
	await color_message()
	await commandloop()


def save():
	global filehandler
	global seminars
	pickle.dump(seminars, filehandler)

async def welcome_message():
	general = trojsten.get_channel(id_bank["welcome channel"])
	_pravidla = ""
	_faq = ""
	for i in range(len(udaje['pravidla'])):
		_pravidla += "{0}. {1}\n".format(i+1,udaje['pravidla'][i])
	for i in udaje['faq']:
		_faq += "- {0}\n{1}\n".format(i[0],i[1])
	_message = """**Vitaj na oficiálnom Discord serveri Trojstenu!**\n\nToto je miesto kde sa stretávajú účastníci a vedúci aby sa zabavili. Ak poznáš niekoho, kto by tu tiež mal byť, neváhaj ho pozvať: https://discord.gg/F9HZP9b\n\nPravidlá:\n{0}\nFaq:\n{1}""".format(_pravidla,_faq)
	found = False
	log("searching for welcome message ...",'proces')
	async for message in general.history():
		if message.author.bot and message.content.startswith("**Vitaj na oficiálnom Discord serveri Trojstenu!**"):
			log("Found",'ok')
			found = True
			if (message.content != _message):
				await message.edit(content=_message)
				log("Changed",'ok')
				pickle.dump(udaje, open('content.dat', 'wb'))
				log("Saved",'ok')
			break
	if not found:
		log("Generating new",'proces')
		msg = await general.send(_message)
	else:
		log("Welcome msg stat - OK",'ok')

_M=None
async def role_message():
	global _M
	general = trojsten.get_channel(id_bank["welcome channel"])
	found = False
	_message = "Nižšie si môžeš vybrať zo seminárov, ktoré riešiš alebo ťa zaujímajú:"
	log("Searching for role message ...",'proces')
	async for message in general.history():
		if message.author.bot and message.content == _message:
			log("Found",'ok')
			_M = message
			found = True
			break

	if not found:
		log("Generating new",'proces')
		msg = await general.send(_message)
		_M = msg
		await msg.add_reaction(client.get_emoji(id_bank['kmsemoji']))
		await msg.add_reaction(client.get_emoji(id_bank['fksemoji']))
		await msg.add_reaction(client.get_emoji(id_bank['kspemoji']))
		await msg.add_reaction(client.get_emoji(id_bank['ufoemoji']))
		await msg.add_reaction(client.get_emoji(id_bank['praskemoji']))
	else:
		log("React msg stat - OK",'ok')
		for react in message.reactions:
			async for reactor in react.users():
				if react.emoji == client.get_emoji(id_bank["kspemoji"]):
					ksp_r = trojsten.get_role(id_bank["ksprole"])
					if ksp_r not in reactor.roles:
						await reactor.add_roles(ksp_r)
				elif react.emoji == client.get_emoji(id_bank["kmsemoji"]):
					kms_r = trojsten.get_role(id_bank["kmsrole"])
					if kms_r not in reactor.roles:
						await reactor.add_roles(kms_r)
				elif react.emoji == client.get_emoji(id_bank["fksemoji"]):
					fks_r = trojsten.get_role(id_bank["fksrole"])
					if fks_r not in reactor.roles:
						await reactor.add_roles(fks_r)
				elif react.emoji == client.get_emoji(id_bank["praskemoji"]):
					prask_r = trojsten.get_role(id_bank["praskrole"])
					if prask_r not in reactor.roles:
						await reactor.add_roles(prask_r)
				elif react.emoji == client.get_emoji(id_bank["ufoemoji"]):
					ufo_r = trojsten.get_role(id_bank["uforole"])
					if ufo_r not in reactor.roles:
						await reactor.add_roles(ufo_r)
		log("React <-> Role sync - OK",'ok')
_C=None
async def color_message():
	global _C
	general = trojsten.get_channel(id_bank["welcome channel"])
	found = False
	_message = "A farbu tvojho mena:"
	log("Searching for color message ...",'proces')
	async for message in general.history():
		if message.author.bot and message.content == _message:
			print("\033[92mFound")
			_C = message
			found = True
			break

	if not found:
		log("Generating new ...",'proces')
		msg = await general.send(_message)
		_C = msg
		reactions = ['⬜','🔶','💚','🔵']
		for emoji in reactions: 
			await msg.add_reaction(emoji=emoji)
	else:
		log("Color msg stat - OK",'ok')
		for react in message.reactions:
			white = trojsten.get_role(id_bank["whiterole"])
			orange = trojsten.get_role(id_bank["orangerole"])
			green = trojsten.get_role(id_bank["greenrole"])
			blue = trojsten.get_role(id_bank["bluerole"])
			async for reactor in react.users():
				if white not in reactor.roles and orange not in reactor.roles and green not in reactor.roles and blue not in reactor.roles:
					if react.emoji == '⬜':
						await reactor.add_roles(white)
					elif react.emoji == '🔶':
						await reactor.add_roles(orange)
					elif react.emoji == '💚':
						await reactor.add_roles(green)
					elif react.emoji == '🔵':
						await reactor.add_roles(blue)
		log("React <-> Role sync - OK",'ok')


		
@client.event
async def on_raw_reaction_add(payload):
	if payload.channel_id == id_bank["welcome channel"] and _M.id == payload.message_id and _M.author.bot:
		user = trojsten.get_member(payload.user_id)
		if payload.emoji == client.get_emoji(id_bank["kspemoji"]):
			await user.add_roles(trojsten.get_role(id_bank["ksprole"]))
		elif payload.emoji == client.get_emoji(id_bank["kmsemoji"]):
			await user.add_roles(trojsten.get_role(id_bank["kmsrole"]))
		elif payload.emoji == client.get_emoji(id_bank["fksemoji"]):
			await user.add_roles(trojsten.get_role(id_bank["fksrole"]))
		elif payload.emoji == client.get_emoji(id_bank["praskemoji"]):
			await user.add_roles(trojsten.get_role(id_bank["praskrole"]))
		elif payload.emoji == client.get_emoji(id_bank["ufoemoji"]):
			await user.add_roles(trojsten.get_role(id_bank["uforole"]))
	elif payload.channel_id == id_bank["welcome channel"] and _C.id == payload.message_id and _C.author.bot:
		user = trojsten.get_member(payload.user_id)
		white = trojsten.get_role(id_bank["whiterole"])
		orange = trojsten.get_role(id_bank["orangerole"])
		green = trojsten.get_role(id_bank["greenrole"])
		blue = trojsten.get_role(id_bank["bluerole"])
		if white not in user.roles and orange not in user.roles and green not in user.roles and blue not in user.roles:
			if payload.emoji.name == '⬜':
				await user.add_roles(white)
			elif payload.emoji.name == '🔶':
				await user.add_roles(orange)
			elif payload.emoji.name == '💚':
				await user.add_roles(green)
			elif payload.emoji.name == '🔵':
				await user.add_roles(blue)

@client.event
async def on_raw_reaction_remove(payload):
	if payload.channel_id == id_bank["welcome channel"] and _M.id == payload.message_id and _M.author.bot:
		user = trojsten.get_member(payload.user_id)
		if payload.emoji == client.get_emoji(id_bank["kspemoji"]):
			ksp_r = trojsten.get_role(id_bank["ksprole"])
			if ksp_r in user.roles:
				await user.remove_roles(ksp_r)
		elif payload.emoji == client.get_emoji(id_bank["kmsemoji"]):
			kms_r = trojsten.get_role(id_bank["kmsrole"])
			if kms_r in user.roles:
				await user.remove_roles(kms_r)
		elif payload.emoji == client.get_emoji(id_bank["fksemoji"]):
			fks_r = trojsten.get_role(id_bank["fksrole"])
			if fks_r in user.roles:
				await user.remove_roles(fks_r)
		elif payload.emoji == client.get_emoji(id_bank["praskemoji"]):
			prask_r = trojsten.get_role(id_bank["praskrole"])
			if prask_r in user.roles:
				await user.remove_roles(prask_r)
		elif payload.emoji == client.get_emoji(id_bank["ufoemoji"]):
			ufo_r = trojsten.get_role(id_bank["uforole"])
			if ufo_r in user.roles:
				await user.remove_roles(ufo_r)
	elif payload.channel_id == id_bank["welcome channel"] and _C.id == payload.message_id and _C.author.bot:
		user = trojsten.get_member(payload.user_id)
		white = trojsten.get_role(id_bank["whiterole"])
		orange = trojsten.get_role(id_bank["orangerole"])
		green = trojsten.get_role(id_bank["greenrole"])
		blue = trojsten.get_role(id_bank["bluerole"])
		if payload.emoji.name == '⬜':
			if white in user.roles:
				await user.remove_roles(white)
		elif payload.emoji.name == '🔶':
			if orange in user.roles:
				await user.remove_roles(orange)
		elif payload.emoji.name == '💚':
			if green in user.roles:
				await user.remove_roles(green)
		elif payload.emoji.name == '🔵':
			if blue in user.roles:
				await user.remove_roles(blue)


class Command:
	def __init__(self, command, is_dm, rest_of_message):
		self.command = command
		self.is_from_dm = is_dm
		self.msg = rest_of_message

async def commandloop():
	while True:
		inp = await commands.get()
		if inp.msg != '':
			try:
				log(str(inp.msg.author.name) + " used command " + str(inp.command) + " with arguments " + str(inp.msg.content))
			except:
				log("Command log failed",'error')
		else:
			log(str(inp.msg.author.name) + " used command " + str(inp.command))

		coms = {"new":		new_interesting,
				"purge":	admin_purge,
				"subscribe":sub,
				"exit":		quyeet,
				"rule":		admin_rule,
				"faq":		admin_faq,
				}
		#if inp.content.startswith("new"):
		#	await new_interesting(inp)
		try:
			await coms[inp.command](inp)
		except:
			await inp.msg.channel.send("Príkaz nebol nájdený")

async def new_interesting(command):
	if command.msg.channel.name == "zaujimave-ulohy" or command.msg.channel.name == "ad min":
		if command.msg.channel.name == "ad min":
			command.msg.channel = client.get_channel(id_bank["zaujimave-ulohy"])
		await command.msg.channel.send("Hey guys, " + command.msg.author.name + " just posted a problem! Author can mark this problem " 
			+ "<:solved:598782166121316363> once it is solved.")
		await command.msg.pin()

async def admin_purge(command):
	#purges server
	if command.msg.author == client.get_user(id_bank["MvKal"]):
		if command.msg.content != None:
			await trojsten.get_channel(int(command.msg.content)).purge(limit = None)
		else:
			print("specify channel")
		#for ch in trojsten.channels:
		#	if ch.type == "text":
		#		print("Inquisiting " + ch.name)
		#		await ch.purge(limit = None)

async def admin_rule(command):
	global udaje
	if trojsten.get_role(id_bank['adminrole']) in command.msg.author.roles or trojsten.get_role(id_bank['veduckorole']) in command.msg.author.roles:
		if command.msg.channel == trojsten.get_channel(id_bank["dev channel"]) or command.msg.channel == trojsten.get_channel(id_bank["admin channel"]) or command.msg.channel == trojsten.get_channel(id_bank["testing channel"]):
			if command.msg.content != '$rule':
				parts = shlex.split(command.msg.content)
				if parts[0] == "add" and len(parts) == 2:
					udaje['pravidla'].append(parts[1])
					await welcome_message()
					await command.msg.add_reaction(emoji='✅')
				elif parts[0] == "remove" and len(parts) == 2:
					try:
						del udaje['pravidla'][int(parts[1])-1]
						await welcome_message()
						await command.msg.add_reaction(emoji='✅')
					except:
						await command.msg.channel.send("Pravidlo nebolo nájdené")
				elif parts[0] == "edit" and len(parts) == 3:
					try:
						udaje['pravidla'][int(parts[1])-1] = parts[2]
						await welcome_message()
						await command.msg.add_reaction(emoji='✅')
					except:
						await command.msg.channel.send("Pravidlo nebolo nájdené")
			else:
				await command.msg.channel.send('```Použitie príkazu ${0}:\n-------------------\n - ${0} add "pravidlo"\n - ${0} remove číslo_pravidla\n - ${0} edit číslo_pravidla "Nové pravidlo"```'.format(command.command))
		else:
			await command.msg.channel.send('`${0} sa dá použiť len v administrátorských chatoch`'.format(command.command))
	else:
		await command.msg.channel.send('`Nedostatočné práva na použitie: ${0}`'.format(command.command))

async def admin_faq(command):
	global udaje
	if trojsten.get_role(id_bank['adminrole']) in command.msg.author.roles or trojsten.get_role(id_bank['veduckorole']) in command.msg.author.roles:
		if command.msg.channel == trojsten.get_channel(id_bank["dev channel"]) or command.msg.channel == trojsten.get_channel(id_bank["admin channel"]) or command.msg.channel == trojsten.get_channel(id_bank["testing channel"]):
			if command.msg.content != '$faq':
				parts = shlex.split(command.msg.content)
				if parts[0] == "add" and len(parts) == 3:
					udaje['faq'].append([parts[1],parts[2]])
					await welcome_message()
					await command.msg.add_reaction(emoji='✅')
				elif parts[0] == "remove" and len(parts) == 2:
					try:
						del udaje['faq'][int(parts[1])-1]
						await welcome_message()
						await command.msg.add_reaction(emoji='✅')
					except:
						await command.msg.channel.send("FAQ nebolo nájdené")
				elif parts[0] == "edit" and len(parts) == 4:
					try:
						udaje['faq'][int(parts[1])-1] = [parts[2] if parts[2] != "-" else udaje['faq'][int(parts[1])-1][0],parts[3] if parts[3] != "-" else udaje['faq'][int(parts[1])-1][1]]
						await welcome_message()
						await command.msg.add_reaction(emoji='✅')
					except:
						await command.msg.channel.send("FAQ nebolo nájdené")
			else:
				await command.msg.channel.send('```Použitie príkazu ${0}:\n-------------------\n - ${0} add "otázka" "odpoveď"\n - ${0} remove číslo_faq_v_poradí\n - ${0} edit číslo_faq_v_poradí "Nová otázka" "Nová odpoveď"\n * pri použití edit "-" zachová pôvodnú otázku/odpoveď```'.format(command.command))
		else:
			await command.msg.channel.send('`${0} sa dá použiť len v administrátorských chatoch`'.format(command.command))
	else:
		await command.msg.channel.send('`Nedostatočné práva na použitie: ${0}`'.format(command.command))

async def sub(command):
	global subscribes
	if command.is_from_dm:
		subscribes[command.msg.content.lower()] = command.msg.author.id
		await command.msg.channel.send("Great! You will now get notifications, whenever something relating " + command.msg.content + " happens!")

async def quyeet(command):
	if command.is_from_dm and command.msg.author == client.get_user(id_bank["MvKal"]):
		save()
		await client.close()
		exit()


async def permaloop():
	#global last_update

	intervals = 900
	last_update = 0
	while True:
		await asyncio.sleep(2)
		if last_update + 900 < time.time():
			last_update = time.time()
			for s in seminars:
				res = s.get_info()
				for change in res:
					if change == "new problems":
						s.newroundmessage()
						s.voting("release")
					elif change == "new solutions":
						s.voting("ideal solutions")
					elif change == "new results":
						s.update_on_results()
					elif change == "end of turn":
						s.end_message()

@client.event
async def on_message(message):
	global ready
	global trojsten
	global timeouts
	if not ready or message.author == trojsten.me:
		return

	if message.author.dm_channel == message.channel:
		if message.author == client.get_user(id_bank["MvKal"]):
			if " " in message.content:
				words = message.content[1:].split(" ")
				message.content = " ".join(words[1:])
				await commands.put(Command(words[0], True, message))
			else:
				await commands.put(Command(message.content[1:], True, message))
		else:
			await message.channel.send("Sorry, I have no functionality relating DM channels yet.. Enjoy my presence on Trojsten server instead :)")
		return


	'''slowmode = 10
	if message.author in trojsten.get_role(id_bank["timeOut role"]).members: #timeOut role
		if message.author.name not in timeouts:
			timeouts[message.author.name] = time.time()
		elif timeouts[message.author.name] + slowmode > time.time():
			await message.delete()
			return
		else:
			timeouts[message.author.name] = time.time()

	if message.author.name=="Girl Jesus":
		await message.add_reaction(client.get_emoji(id_bank["misko emoji"])) #misko emoji'''

	if message.content.startswith("$"):
		if " " in message.content:
			words = message.content[1:].split(" ")
			message.content = " ".join(words[1:])
			await commands.put(Command(words[0], False, message))
		else:
			await commands.put(Command(message.content[1:], False, message))

	

async def add_warning(user, reason):
	warnings_to_ban = 3
	if user.name not in warnings:
		warnings[user.name] = [1, reason]
	else:
		warnings[user.name][0] += 1
		warnings[user.name].append(reason)
		log(user.name + " got warning because of " + reason + ". He has " + str(warnings[user.name][0]) + " warnings.",'warning')
	if warnings[user.name][0] >= warnings_to_ban:
		try:
			await trojsten.ban(user, reason = ", ".join(warnings[user.name][1:]) + " --banned by bot." , delete_message_days = 0)
			await user.dm_channel.send("Number of warnings have reached " + str(warnings_to_ban) + ". You are now banned from Trojsten server.")
		except Exception as e:
			await user.dm_channel.send("You have reached maximum number of warnings, but I am unable to ban you for some reason. High lord MvKal is notified about this and will deal with you accordingly.")
			await trojsten.owner.dm_channel.send("I am unable to ban " + user.name + ", but he has reached maximum warnings. Handle this situation accordingly.\nException in console")
			log(e,'error')
	else:
		await user.dm_channel.send("You now get an official warning. You now have " + str(warnings[user.name][0]) + " warnings. Once this number reaches " + str(warnings_to_ban) + ", you will get a server ban. Contact moderators for further information.\n\n\n-Troj-stena")



async def react_iter(look, iterator):
	async for user in iterator():
		if user == look:
			return True

	return False

@client.event
async def on_reaction_add(react, user):
	global trojsten
	global warnings
	global weird_messages

	if react.message.channel.name == "zaujimave-ulohy"  and react.emoji == client.get_emoji(id_bank["solved emoji"]) and await react_iter(react.message.author, react.users) and react.message.pinned and react.message.content.startswith("$new"):
		await react.message.channel.send("WOW, somebody has solved " + react.message.author.name + "'s problem: " + react.message.content[5:] + "! Congrats!")
		await react.message.unpin()
	elif react.emoji == client.get_emoji(id_bank["cheatalert emoji"]): #cheat alert
		if react.message.channel == trojsten.get_channel(id_bank["moderating channel"]): #moderating channel
			nafetch = weird_messages[react.message.id]
			react.message = await trojsten.get_channel(nafetch[1]).fetch_message(nafetch[0])
			if react.message.author.dm_channel == None:
				await react.message.author.create_dm()
			await react.message.author.dm_channel.send(react.message.author.name + ". Moderators decided, that your message (details below) violated rules, and is now deleted. Please respect server rules.")
			sent = datetime.time(hour = react.message.created_at.time().hour + 2, minute = react.message.created_at.time().minute, second = react.message.created_at.time().second)
			#react.message.created_at.time().hour += 2
			await react.message.author.dm_channel.send("Message details:\nCreated at: " + sent.isoformat(timespec="seconds") + " of UTC+2" +
														"\nSent to: " + react.message.channel.name +
														"\nContents: " + react.message.content)
		#elif user in trojsten.get_role(598517418968743957).members and react.message.channel != trojsten.get_channel(599249382038044703): #role: Veducko, channel: isnt #moderating
		#	await react.message.channel.send(react.message.author + "!!! Your message was deleted because of serious rules violation.")
		await react.message.delete()
		await add_warning(react.message.author, "CHEAT alert emoji")

		
	elif react.emoji == client.get_emoji(id_bank["questionable emoji"]):
		chan = trojsten.get_channel(id_bank["moderating channel"])
		newmsg = await chan.send("Questionable message in " + react.message.channel.name + ": " + react.message.content + "\nLink: " + react.message.jump_url)
		weird_messages[newmsg.id] = (react.message.id, react.message.channel.id)
	
@client.event
async def on_reaction_remove(react, user):
	#nothing .. for now
	return


class problem:
	def __init__(self,name,link,points):
		self.name = name
		self.link = link
		self.points = points
	def print_contents(self):
		log([self.name,self.link,self.points])


class person:
	def __init__(self,stat,name,year,school,level,points_bf,points,points_sum):
		self.stat = stat
		self.name = name
		self.year = year
		self.school = school
		self.level = level
		self.points_bf = points_bf
		self.points = points
		self.points_sum = points_sum
	def print_contents(self):
		log([self.stat,self.name,self.year,self.school,self.level,self.points_bf,self.points,self.points_sum])

class GatheringException(Exception):
	def __init__(self, seminar, message):
		self.seminar = seminar
		self.message = message



class Seminar:
	def __init__(self, name, outchan, url):
		global trojsten
		
		self.name = name
		self.m_channel = outchan
		self.url = url 
		self.active = False
		self.year = 0
		self.round = 0
		self.part = 0
		self.problems = []
		self.result_table = []
		self.get_info()
		self.p_length = len(self.problems)

	async def newroundmessage(self):
		msg = "**New round of {0.mention} started!** \n You can start solving now -> {1}".format(trojsten.get_role(id_bank[self.name+"role"]),self.url+"/ulohy")
		await  self.outchan.send(msg)

	async def voting(self, type):
		self.get_info()
		if self.active:
			global botrole
			global trojsten
			vote_channel = trojsten.get_channel(id_bank["voting channel"])
		

			if type=="release":
				await vote_channel.send("Hello, new problems are released!! You may now vote for each problem here <:badin:598483292034957312>")
			elif type == "ideal solutions":
				await vote_channel.send("Hello, ideal solutions are released by our mighty leaders! You may now vote for each solution here <:badin:598483292034957312>")
			await vote_channel.send("You can find them on website: " + self.url + "/ulohy")


			for n in range(self.p_length):
				msg = await vote_channel.send(str(n+1) + ". " + self.problems[n].name)
			
				#reacty = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "keycap_ten"]
				#for r in range(self.zadani):
				#	msg.add_reaction
				await msg.add_reaction(client.get_emoji(id_bank["thup emoji"]))
				await msg.add_reaction(client.get_emoji(id_bank["thdown emoji"]))
				await msg.add_reaction(client.get_emoji(id_bank["badin emoji"]))
	
	def set_result_table(self, dict):
		self.last_results = self.result_table
		self.result_table = dict

	async def update_on_results(self):
		#await self.m_channel.send("Hey guys, some random veducko added some points! Go and check it out on " + self.url + "/vysledky/")
		global subscribes
		for key in subscribes:
			try:
				if self.result_table.index(key) != self.last_results.index(key):
					await client.get_user(subscribes[key]).dm_channel.send("HEY, " + key + " has changed his position! Go check it out on "+ self.url + "/vysledky")
			except Exception as e:
				print("Couldn't notify " + client.get_user.name + " about change in results table about " + subscribes[key])
				print(e)
				
	
	async def end_message(self):
		await self.m_channel.send("The round of " + self.name + " has officialy ended. Congratulations to every sucessful participant!")
	
	

	def get_info(self):
		try:
			responseP = requests.get(self.url+'/ulohy', allow_redirects = True)
			responseR = requests.get(self.url+'/vysledky/', allow_redirects = True)
			sourceCodeP = responseP.content
			sourceCodeR = responseR.content
		except:
			raise GatheringException(self.name,"Conectivity error occured")
		try:
			treeP = lxml.etree.HTML(sourceCodeP)
			treeR = lxml.etree.HTML(sourceCodeR)
		except:
			raise GatheringException(self.name,"Web parsing error occured")
		try:
			task_list = treeP.find('.//table')
			result_list = treeR.find('.//table[@class="table table-hover table-condensed results-table"]')
		except:
			raise GatheringException(self.name,"Web not compatible")
		try:
			output = []
			def get_results():
				rows = result_list.findall('.//tr')
				row_type = rows[0].findall('.//th')		
				results = []		
				for per in rows[1:]:
					state,name,year,school,level,points_before,pointers,points_sum = None, None, None, None, None, None, None, None
					clovek = per.findall('.//td')
					pointers = []
					for i in range(len(clovek)):
						rt = str(row_type[i].text).strip()
						if rt == None or rt == '':
							rt = str(row_type[i][0].text).strip()
						if '#' in rt:
							cLass = clovek[i].find('.//span').attrib['class']
							if 'glyphicon-asterisk' in cLass:
								state = 'new'
							elif 'glyphicon-chevron-down' in cLass:
								state = 'dropped'
							elif 'glyphicon-chevron-up' in cLass:
								state = 'advanced'
							elif 'glyphicon-pushpin' in cLass:
								state = 'pinned'
							else:
								state = 'none'
						elif 'Meno' in rt:
							name = clovek[i].text.strip()
						elif 'kola' in rt:
							school = clovek[i][0].text.strip()
						elif 'R' in rt:
							year = clovek[i].text.strip()
						elif 'Level' in rt or 'K' in rt:
							level = clovek[i][0].text.strip()
						elif 'P' in rt:
							points_before = clovek[i][0].text.strip()
						elif '∑' in rt:
							points_sum = clovek[i][0].text.strip()
						elif re.match(r'[1-9]',rt):
							pointers.append(None if clovek[i][0].text == None else clovek[i][0].text.strip())
					results.append(person(state,name,year,school,level,points_before,pointers,points_sum))
				if (self.result_table != results): output.append("new results")
				self.set_result_table(results)	
			if('task-list' in task_list.attrib['class']):
				self.active = True
				round_info = treeP.find('.//small').text.replace('\n','').replace(' ','').split(',')
				# check for changes
				round = round_info[0].split('.')[0]
				part = round_info[1].split('.')[0]
				year = round_info[2].split('.')[0]
				self.problems = []
				for node in task_list.findall('tr'):
					pointers = []
					for pointer in node[2].findall('span'):
						pointers.append(pointer.text.replace('\xa0','').split(':')[1])
					self.problems.append(problem(node[1][0].text,self.url+node[1][0].attrib['href'],pointers))
				self.p_length = len(self.problems)
				get_results()
				if ((self.round != round or self.part != part or self.year != year) and len(self.problems) > 0): output.append('new problems')
				self.round = round
				self.part = part
				self.year = year
				self.remaining = treeP.find(".//div[@class='progress-bar progress-bar-info']").text
				self.r_datetime = datetime.strptime(treeP.find(".//em").text[12:],"%d. %B %Y %H:%M")
				return output
			else:				
				if (self.active != False): output.append('end of round')
				self.active = False
				self.remaining = "Round not active"
				get_results()
				return output
		except:
			raise GatheringException(self.name,"Gathering error occured")

#TODO: mergenut voting channely do jedneho, lebo je to moc zaspamovane

client.run("NTk4NDc3MjI2NTg0OTY1MTIy.XSXTWg.IgQkQwMI-4KV-gHoz7aDXguq6U8")
