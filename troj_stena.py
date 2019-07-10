import discord

client = discord.Client()

@client.event
async def on_ready():
	global botrole
	global trojsten
	print("I am ready as", client.user.name + "#" + str(client.user.discriminator))
	trojsten = client.guilds[0]
	categories = []
	botrole = trojsten.get_role(598485979669463041)
	seminars = [Seminar("httkms", client.get_channel(598476702527651841), "https://kms.sk", 10),
				Seminar("ksp", client.get_channel(598479504595484683), "https://ksp.sk", 8),
				Seminar("fks", client.get_channel(598479519296389122), "https://fks.sk", 7),
				Seminar("ufo", client.get_channel(598479666205949952), "https://ufo.fks.sk", 5),
				Seminar("prask", client.get_channel(598479637093416973), "https://prask.ksp.sk", 5)]
	await seminars[0].voting("release")
				




#@client.property
#async def on_message():




'''
check nove zadania
vzoraky
check vysledkoviek
ratingy na ulohy

'''





class Seminar:
	def __init__(self, name, category_channel, url, number_of_problems):
		self.name = name
		self.cat_channel = category_channel
		self.url = url
		self.n_of_problems = number_of_problems


	async def voting(self, type):
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
				trojsten.get_role(598485979669463041): discord.PermissionOverwrite(send_messages=True, add_reactions = True)
			}
			vote_channel = await self.cat_channel.create_text_channel("voting", overwrites = overwrites)

		if type=="release":
			await vote_channel.send("Hello, new problems are released!! You may now vote for each problem here <:badin:598483292034957312>")
		elif type == "ideal solutions":
			await vote_channel.send("Hello, ideal solutions are released by our mighty leaders! You may now vote for each solution here <:badin:598483292034957312>")
		await vote_channel.send("You can find them on website: " + self.url + "/ulohy")


		for problem in adamova_kul_funkcia():
			msg = await vote_channel.send(problem)
			
			#reacty = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "keycap_ten"]
			#for r in range(self.zadani):
			#	msg.add_reaction
			await msg.add_reaction(client.get_emoji(598508913372954634))
			await msg.add_reaction(client.get_emoji(598509040540057600))
			await msg.add_reaction(client.get_emoji(598483292034957312))


def adamova_kul_funkcia():
	return ["1. pokus", "2. Misko ma autizmus"]





client.run("NTk4NDc3MjI2NTg0OTY1MTIy.XSXTWg.IgQkQwMI-4KV-gHoz7aDXguq6U8")