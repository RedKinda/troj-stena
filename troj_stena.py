import discord
import time
import asyncio
import requests
import re
import pickle
import lxml
import lxml.etree
from aioconsole import ainput

commands = asyncio.Queue()

ready = False
client = discord.Client()

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

	ready = True
	timeouts = {}
	print("I am ready as", client.user.name + "#" + str(client.user.discriminator))
	trojsten = client.guilds[0]
	categories = []
	botrole = trojsten.get_role(598502023079657483)
	seminars = []
	warnings = {}
	weird_messages = {}
	try:			#loading seminars
		reader = open('information.dat', 'rb')
		seminars = pickle.load(reader)
	except EOFError: #if there is no file, create them
		filehandler = open('information.dat', 'wb+')
		seminars = [Seminar("kms", 598476702527651841, "https://kms.sk"),
					Seminar("ksp", 598479504595484683, "https://ksp.sk"),
					Seminar("fks", 598479519296389122, "https://fks.sk"),
					Seminar("ufo", 598479666205949952, "https://ufo.fks.sk"),
					Seminar("prask", 598479637093416973, "https://prask.ksp.sk")]
		#Debug web gathering --> print first contestant in result table for seminar x
		#print(seminars[1].result_table[0].print_contents())
		pickle.dump(seminars, filehandler)
	for sem in seminars:
		sem.cat_channel = client.get_channel(sem.cat_channel)
	filehandler = open('information.dat', 'wb')
	#for s in seminars:
	#	await s.voting("release")
	await commandloop()

	
async def commandloop():
	while True:
		inp = await commands.get()
		print(inp[0] + inp[1].content)
		coms = {"new":		new_interesting,
				"purge":	admin_purge,
				}
		#if inp.content.startswith("new"):
		#	await new_interesting(inp)
		await coms[inp[0]](inp[1])


async def new_interesting(message):
	if message.channel.name == "zaujimave-ulohy" or message.channel.name == "ad min":
		if message.channel.name == "ad min":
			message.channel = client.get_channel(598522778743734342)
		await message.channel.send("Hey guys, " + message.author.name + " just posted a problem! Author can mark this problem " 
			+ "<:solved:598782166121316363> once it is solved.")
		await message.pin()
async def admin_purge(msg):
	#purges server
	if msg.author == "MvKal":
		for ch in trojsten.channels:
			if ch.type == "text":
				print("Inquisiting " + ch.name)
				await ch.purge(limit = None)
				
async def permaloop():
	global last_update
	intervals = 900
	while True:
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
		if message.author.name=="MvKal":
			if " " in message.content:
				words = message.content[1:].split(" ")
				message.content = " ".join(words[1:])
				message.channel.name = "ad min"
				await commands.put((words[0], message))
			else:
				await commands.put((message.content[1:], None))
		else:
			await message.channel.send("Sorry, I have no functionality relating DM channels yet.. Enjoy my presence on Trojsten server instead :)")
		return


	slowmode = 10
	if message.author in trojsten.get_role(598815157975515147).members: #timeOut role
		if message.author.name not in timeouts:
			timeouts.update({message.author.name: time.time()})
		elif timeouts[message.author.name] + slowmode > time.time():
			await message.delete()
			return
		else:
			timeouts[message.author.name] = time.time()

	if message.author.name=="Girl Jesus":
		await message.add_reaction(client.get_emoji(598820789168373778)) #misko emoji

	if message.content.startswith("$"):
		if " " in message.content:
			words = message.content[1:].split(" ")
			message.content = " ".join(words[1:])
			await commands.put((words[0], message))
		else:
			await commands.put((message.content[1:], None))

	



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
	if react.message.channel.name == "zaujimave-ulohy"  and react.emoji == client.get_emoji(598782166121316363) and await react_iter(react.message.author, react.users) and react.message.pinned and react.message.content.startswith("$new"):
		await react.message.channel.send("WOW, somebody has solved " + react.message.author.name + "'s problem: " + react.message.content[5:] + "! Congrats!")
		await react.message.unpin()
	elif react.emoji == client.get_emoji(599242099207962635):
		if react.message.channel == trojsten.get_channel(599249382038044703):
			react.message = await react.message.author.fetch_message(weird_messages[react.message.id])
			await react.message.author.dm_channel.send(react.message.author + ". Moderators decided, that your message (details below) violated rules, and is now deleted. Please respect server rules. You get an official warning, and on 3-rd warning, you will be banned.")
			await react.message.author.dm_channel.send("Message details:\nCreated at: " + react.message.created_at + "UTC" +
														"\nSent to: " + react.message.channel +
														"\nContents: " + react.message.content)
		if user in trojsten.get_role(598517418968743957).members and react.messae.channel != trojsten.get_channel(599249382038044703):
			await react.message.channel.send(react.message.author + "!!! Your message was deleted because of serious rules violation. You now get an official warning. You get server ban on 3-rd warning.")
		await react.message.delete()
		if react.message.author.name not in warnings:
			warnings.update({react.message.author.name: [warnings[react.message.author.name], "CHEAT alert emoji"]})
		else:
			warnings[react.message.author.name][0] += 1
			warnings[react.message.author.name].append("CHEAT alert emoji")

		
	elif react.emoji == client.get_emoji(599248755186728966):
		chan = trojsten.get_channel(599249382038044703)
		newmsg = await chan.send("Questionable message in " + react.message.channel.name + ": " + react.message.content)
		weird_messages.update({newmsg.id: react.message.id})
	
	

'''
check nove zadania
vzoraky
check vysledkoviek
ratingy na ulohy

'''



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
	def __init__(self, name, category_channel,url):
		self.name = name
		self.cat_channel = category_channel
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
			vote_channel = None
			for chan in self.cat_channel.text_channels:
				if chan.name == "voting":
					vote_channel = chan
					break
			if vote_channel == None:
				overwrites = {
					trojsten.default_role: discord.PermissionOverwrite(send_messages = False, add_reactions = False),
					botrole: discord.PermissionOverwrite(send_messages=True, add_reactions = True)
				}
				vote_channel = await self.cat_channel.create_text_channel("voting", overwrites = overwrites)

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
				await msg.add_reaction(client.get_emoji(598508913372954634))
				await msg.add_reaction(client.get_emoji(598509040540057600))
				await msg.add_reaction(client.get_emoji(598483292034957312))
	
	def set_result_table(self, dict):
		self.result_table = dict

	async def update_on_results(self):
		await self.cat_channel.text_channels[0].send("Hey guys, some random veducko added some points! Go and check it out on " + self.url + "/vysledky/")
	
	async def end_message(self):
		await self.cat_channel.text_channels[0].send("The round of " + self.name + " has officialy ended. Congratulations to every sucessful participant!")
	
	

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
				self.results_table = results	
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

		'''
async def console_input():
	global trojsten
	global botrole
	global seminars
	while True:
		try:
			inp = await ainput("")
			exec(inp)
		except Exception as e: 
			print(e)
		asyncio.sleep(0.5)
			'''


client.run("NTk4NDc3MjI2NTg0OTY1MTIy.XSXTWg.IgQkQwMI-4KV-gHoz7aDXguq6U8")
