import discord
import time
import asyncio
import requests
import re
import pickle
import lxml
import lxml.etree
import datetime
#from aioconsole import ainput

commands = asyncio.Queue()

ready = False
client = discord.Client()


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
		   "MvKal"				:	332935845004705793,
		   "voting channel"		:	600688938562093058


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

	ready = True
	print("I am ready as", client.user.name + "#" + str(client.user.discriminator))
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
	
	await commandloop()
	

def save():
	global filehandler
	global seminars
	pickle.dump(seminars, filehandler)

	
class Command:
	def __init__(self, command, is_dm, rest_of_message):
		self.command = command
		self.is_from_dm = is_dm
		self.msg = rest_of_message

async def commandloop():
	while True:
		inp = await commands.get()
		print(inp.command + " with " + inp.msg.content)
		coms = {"new":		new_interesting,
				"purge":	admin_purge,
				"subscribe":sub,
				"exit":		quyeet,
				}
		#if inp.content.startswith("new"):
		#	await new_interesting(inp)
		await coms[inp.command](inp)


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
				await commands.put(Command(words[0], True, None))
		else:
			await message.channel.send("Sorry, I have no functionality relating DM channels yet.. Enjoy my presence on Trojsten server instead :)")
		return


	slowmode = 10
	if message.author in trojsten.get_role(id_bank["timeOut role"]).members: #timeOut role
		if message.author.name not in timeouts:
			timeouts[message.author.name] = time.time()
		elif timeouts[message.author.name] + slowmode > time.time():
			await message.delete()
			return
		else:
			timeouts[message.author.name] = time.time()

	if message.author.name=="Girl Jesus":
		await message.add_reaction(client.get_emoji(id_bank["misko emoji"])) #misko emoji

	if message.content.startswith("$"):
		if " " in message.content:
			words = message.content[1:].split(" ")
			message.content = " ".join(words[1:])
			await commands.put(Command(words[0], False, message))
		else:
			await commands.put(Command(words[0], False, None))

	

async def add_warning(user, reason):
	warnings_to_ban = 3
	if user.name not in warnings:
		warnings[user.name] = [1, reason]
	else:
		warnings[user.name][0] += 1
		warnings[user.name].append(reason)
	print(user.name + " got warning because of " + reason + ". He has " + str(warnings[user.name][0]) + " warnings.")
	if warnings[user.name][0] >= warnings_to_ban:
		try:
			await trojsten.ban(user, reason = ", ".join(warnings[user.name][1:]) + " --banned by bot." , delete_message_days = 0)
			await user.dm_channel.send("Number of warnings have reached " + str(warnings_to_ban) + ". You are now banned from Trojsten server.")
		except Exception as e:
			await user.dm_channel.send("You have reached maximum number of warnings, but I am unable to ban you for some reason. High lord MvKal is notified about this and will deal with you accordingly.")
			await trojsten.owner.dm_channel.send("I am unable to ban " + user.name + ", but he has reached maximum warnings. Handle this situation accordingly.\nException in console")
			print (e)
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
	
	


class problem:
	def __init__(self,name,link,points):
		self.name = name
		self.link = link
		self.points = points
	def print_contents(self):
		print([self.name,self.link,self.points])


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
		print([self.stat,self.name,self.year,self.school,self.level,self.points_bf,self.points,self.points_sum])

class GatheringException(Exception):
	def __init__(self, seminar, message):
		self.seminar = seminar
		self.message = message



class Seminar:
	def __init__(self, name, outchan,url):
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
