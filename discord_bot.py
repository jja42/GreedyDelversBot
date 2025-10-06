import discord
from discord import app_commands
import random
import asyncio
from PIL import Image

#Bot token
with open("BotToken.txt", "r") as f:
    token = f.read().strip()
    
with open("ServerID.txt", "r") as f:
    serverID = f.read().strip()
 
intent = discord.Intents.default()

class bot(discord.Client):
	def __init__(self):
		super().__init__(intents=discord.Intents.default())
		self.synced = False
	#Synced to base server atm
	async def on_ready(self):
		await self.wait_until_ready()
		if not self.synced:
			await tree.sync(guild=discord.Object(id=serverID))
			self.synced = True
		print("Bot is Online")

#Two Buttons to Join or Start. Has Reference to Game ID
class join_menu(discord.ui.View):
	def __init__(self,game_id):
		super().__init__()
		self.game_id = game_id
  
    #Adds Players to a game if they're not already in the game and if the game has space. Updates the current message.
	@discord.ui.button(label = "Join Game", style = discord.ButtonStyle.gray)
	async def menu1(self,interaction: discord.Interaction,button: discord.ui.Button):
		current_game = games[self.game_id]
		if current_game.check_users(interaction.user.name):
			await interaction.response.send_message("You're already in this game!",ephemeral = True)
		else:
			if len(current_game.players) < 4:
				new_player = player(interaction.user.name)
				current_game.players.append(new_player)
				await interaction.response.edit_message(content = current_game.players[0].name + "Created a Game. Number of Players: " + str(len(current_game.players)))
				await interaction.followup.send("You Joined The Game",ephemeral = True)
			else:
				await interaction.response.send_message("Cannot Join! The Game Is Full!",ephemeral = True)
	
	#Starts Current Game and sends initial games state, if enough players. If not, sends warning.		
	@discord.ui.button(label = "Start Game", style = discord.ButtonStyle.gray)
	async def menu2(self,interaction: discord.Interaction,button: discord.ui.Button):
		current_game = games[self.game_id-1] 
		if len(current_game.players) > 4: #TEMPORARILY SET TO GREATER THAN INSTEAD OF LESS THAN FOR TESTING!
			await interaction.response.send_message("Cannot Start Game! Need More Players!",ephemeral = True)
		else:
			current_game.start_game()
			current_game.get_game_state()
			menu = draw_menu(current_game.id)
			await interaction.response.send_message(current_game.game_state, view = menu)

#Displays a button to draw for turn 
class draw_menu(discord.ui.View):
	def __init__(self,game_id):
		super().__init__()
		self.game_id = game_id
  
    #Draw Card to Player's hand
	@discord.ui.button(label = "Draw For Turn", style = discord.ButtonStyle.gray)
	async def menu1(self,interaction: discord.Interaction,button: discord.ui.Button):
		current_game = games[self.game_id]
		if current_game.check_users(interaction.user.name):
			if current_game.check_draw(interaction.user.name):
				 interaction.response.send_message("You've drawn already!",ephemeral = True)
			else:
				current_game.player_draw(interaction.user.name)
				picture = discord.File('GeneratedImage.png')
				menu = play_menu(current_game.id)
				await interaction.response.send_message(file=picture, view = menu, ephemeral = True)			
		else:
			await interaction.response.send_message("You're not in this game!",ephemeral = True)

#Displays buttons for each playable card
class play_menu(discord.ui.View):
	def __init__(self,game_id):
		super().__init__()
		self.game_id = game_id
  
    #Play card 1
	@discord.ui.button(label = "Play 1st Card", style = discord.ButtonStyle.gray)
	async def menu1(self,interaction: discord.Interaction,button: discord.ui.Button):
		current_game = games[self.game_id]
		if current_game.check_users(interaction.user.name):
			if current_game.check_play(interaction.user.name):
				await interaction.response.send_message("You've already played a card!",ephemeral = True)
			else:
				if(current_game.check_cost(interaction.user.name,0)):
					current_game.player_play(interaction.user.name, 0)
					card = current_game.get_played_card(interaction.user.name)
					if(card.card_type == "Minion"):
						text = current_game.get_targets(interaction.user.name)
						menu = target_menu(current_game.id,interaction.user.name)
						await interaction.response.send_message(text,view = menu,ephemeral = True)
					else:
						current_game.player_done(interaction.user.name)
						if current_game.check_turn():
							current_game.calculate_game_state()
							current_game.get_game_state()
							menu = draw_menu(current_game.id)
							await interaction.response.send_message(current_game.game_state, view = menu)
						else:
							await interaction.response.send_message("Successfully played a card. Please wait for others to finish",ephemeral = True)
				else:
					await interaction.response.send_message("You don't have enough gold to play this card!",ephemeral = True)
	
	#Play card 2
	@discord.ui.button(label = "Play 2nd Card", style = discord.ButtonStyle.gray)
	async def menu2(self,interaction: discord.Interaction,button: discord.ui.Button):
		current_game = games[self.game_id]
		if current_game.check_users(interaction.user.name):
			if current_game.check_play(interaction.user.name):
				await interaction.response.send_message("You've already played a card!",ephemeral = True)
			else:
				if(current_game.check_cost(interaction.user.name, 1)):
					current_game.player_play(interaction.user.name, 1)
					card = current_game.get_played_card(interaction.user.name)
					if(card.card_type == "Minion"):
						text = current_game.get_targets(interaction.user.name)
						menu = target_menu(current_game.id,interaction.user.name)
						await interaction.response.send_message(text,view = menu,ephemeral = True)
					else:
						current_game.player_done(interaction.user.name)
						if current_game.check_turn():
							current_game.calculate_game_state()
							current_game.get_game_state()
							menu = draw_menu(current_game.id)
							await interaction.response.send_message(current_game.game_state, view = menu)
						else:
							await interaction.response.send_message("Successfully played a card. Please wait for others to finish",ephemeral = True)
				else:
					await interaction.response.send_message("You don't have enough gold to play this card!",ephemeral = True)
	
	#Play card 3
	@discord.ui.button(label = "Play 3rd Card", style = discord.ButtonStyle.gray)
	async def menu3(self,interaction: discord.Interaction,button: discord.ui.Button):
		current_game = games[self.game_id]
		if current_game.check_users(interaction.user.name):
			if current_game.check_play(interaction.user.name):
				await interaction.response.send_message("You've already played a card!",ephemeral = True)
			else:
				if(current_game.check_cost(interaction.user.name, 2)):
					current_game.player_play(interaction.user.name, 2)
					card = current_game.get_played_card(interaction.user.name)
					if(card.card_type == "Minion"):
						text = current_game.get_targets(interaction.user.name)
						menu = target_menu(current_game.id,interaction.user.name)
						await interaction.response.send_message(text,view = menu,ephemeral = True)
					else:
						current_game.player_done(interaction.user.name)
						if current_game.check_turn():
							current_game.calculate_game_state()
							current_game.get_game_state()
							menu = draw_menu(current_game.id)
							await interaction.response.send_message(current_game.game_state, view = menu)
						else:
							await interaction.response.send_message("Successfully played a card. Please wait for others to finish",ephemeral = True)
				else:
					await interaction.response.send_message("You don't have enough gold to play this card!",ephemeral = True)
		else:
			await interaction.response.send_message("You're not in this game!",ephemeral = True)
	
	#Play card 4
	@discord.ui.button(label = "Play 4th Card", style = discord.ButtonStyle.gray)
	async def menu4(self,interaction: discord.Interaction,button: discord.ui.Button):
		current_game = games[self.game_id]
		if current_game.check_users(interaction.user.name):
			if current_game.check_play(interaction.user.name):
				await interaction.response.send_message("You've already played a card!",ephemeral = True)
			else:
				if(current_game.check_cost(interaction.user.name, 3)):
					current_game.player_play(interaction.user.name, 3)
					card = current_game.get_played_card(interaction.user.name)
					if(card.card_type == "Minion"):
						text = current_game.get_targets(interaction.user.name)
						menu = target_menu(current_game.id,interaction.user.name)
						await interaction.response.send_message(text,view = menu,ephemeral = True)
					else:
						current_game.player_done(interaction.user.name)
						if current_game.check_turn():
							current_game.calculate_game_state()
							current_game.get_game_state()
							menu = draw_menu(current_game.id)
							await interaction.response.send_message(current_game.game_state, view = menu)
						else:
							await interaction.response.send_message("Successfully played a card. Please wait for others to finish",ephemeral = True)
				else:
					await interaction.response.send_message("You don't have enough gold to play this card!",ephemeral = True)
		else:
			await interaction.response.send_message("You're not in this game!",ephemeral = True)

#Displays buttons for each targetable player, excluding self
class target_menu(discord.ui.View):
	def __init__(self,game_id,player):
		super().__init__()
		self.game_id = game_id

	#Target 1st Player
	@discord.ui.button(label = "Target Player 1", style = discord.ButtonStyle.gray)
	async def menu1(self,interaction: discord.Interaction,button: discord.ui.Button):
		current_game = games[self.game_id]
		if current_game.check_users(interaction.user.name):
			if current_game.check_target(interaction.user.name):
				await interaction.response.send_message("You've already selected a target!",ephemeral = True)
			else:
				current_game.player_target(interaction.user.name,1)
				current_game.player_done(interaction.user.name)
				if current_game.check_turn():
					current_game.calculate_game_state()
					current_game.get_game_state()
					menu = draw_menu(current_game.id)
					await interaction.response.send_message(current_game.game_state, view = menu)
				else:
					await interaction.response.send_message("Successfully played a card. Please wait for others to finish",ephemeral = True)
		else:
			await interaction.response.send_message("You're not in this game!",ephemeral = True)
	
	#Target 2nd Player
	@discord.ui.button(label = "Target Player 2", style = discord.ButtonStyle.gray)
	async def menu2(self,interaction: discord.Interaction,button: discord.ui.Button):
		current_game = games[self.game_id]
		if current_game.check_users(interaction.user.name):
			if current_game.check_target(interaction.user.name):
				await interaction.response.send_message("You've already selected a target!",ephemeral = True)
			else:
				current_game.player_target(interaction.user.name,2)
				current_game.player_done(interaction.user.name)
				if current_game.check_turn():
					current_game.calculate_game_state()
					current_game.get_game_state()
					menu = draw_menu(current_game.id)
					await interaction.response.send_message(current_game.game_state, view = menu)
				else:
					await interaction.response.send_message("Successfully played a card. Please wait for others to finish",ephemeral = True)
		else:
			await interaction.response.send_message("You're not in this game!",ephemeral = True)
	
	#Target 3rd Player
	@discord.ui.button(label = "Target Player 3", style = discord.ButtonStyle.gray)
	async def menu3(self,interaction: discord.Interaction,button: discord.ui.Button):
		current_game = games[self.game_id]
		if current_game.check_users(interaction.user.name):
			if current_game.check_target(interaction.user.name):
				await interaction.response.send_message("You've already selected a target!",ephemeral = True)
			else:
				current_game.player_target(interaction.user.name,3)
				current_game.player_done(interaction.user.name)
				if current_game.check_turn():
					current_game.calculate_game_state()
					current_game.get_game_state()
					menu = draw_menu(current_game.id)
					await interaction.response.send_message(current_game.game_state, view = menu)
				else:
					await interaction.response.send_message("Successfully played a card. Please wait for others to finish",ephemeral = True)
		else:
			await interaction.response.send_message("You're not in this game!",ephemeral = True)

class game():
	def __init__(self, host):
		self.id = len(games)
		self.players = []
		self.players.append(host)
		self.game_state = ""
		self.deck = init_deck()
		self.deck = shuffle(self.deck)
		self.played_cards = {}
	
	#Check if the user name is included in the game's player list
	def check_users(self, user_name):
		user_names = []
		for p in self.players:
			user_names.append(p.name)
		return user_name in user_names
	
	#Check if a player has already drawn this turn
	def check_draw(self, user_name):
		for p in self.players:
			if p.name == user_name:
				return p.draw
		return False
		
	#Check if a player has already played a card this turn
	def check_play(self, user_name):
		for p in self.players:
			if p.name == user_name:
				if not p.played_card:
					return False
		return True
	
	#Check if a player has already selected a target this turn
	def check_target(self, user_name):
		for p in self.players:
			if p.name == user_name:
				if not p.target:
					return False
		return True
	
	#Check if a player has enough gold to play a specific card
	def check_cost(self, user_name,index):
		for p in self.players:
			if p.name == user_name:
				c = p.hand[index]
		card_cost = c.cost
		if(card_cost > p.gold): 
			return False
		else:
			return True
	
	#Draws a card for the player and creates their hand (image)
	def player_draw(self, user_name):
		for p in self.players:
			if p.name == user_name:
				p.turn_draw(self.deck)
				p.show_hand()
		
	#Plays a card for the player at specific index in their hand, appends to played cards
	def player_play(self, user_name, index):
		for p in self.players:
			if p.name == user_name:
				p.play_card(index)
				self.played_cards[p.name] = p.played_card
	
	#Mark that a player is done with their turn
	def player_done(self, user_name):
		for p in self.players:
			if p.name == user_name:
				p.turn_done = True
	
	#Sets a target for a player when a minion is played			
	def player_target(self, user_name, num):
		i = 0
		for p in self.players:
			if p.name == user_name:
				for t in self.players:
					if t.name != user_name:
						i += 1
						if i == num:
							p.target = t.name
	
	#Clears Turn Parameters for Players and Game		
	def turn_clear(self):
		for p in self.players:
			p.played_card = None
			p.draw = False
			p.target = None
			p.turn_done = False
		self.played_cards = {}
	
	def next_turn(self):
		for p in self.players:
			p.floor += 1
			p.ore += 3
	
	#Initializes the starting hands for each player
	def start_game(self):
		for p in self.players:
			p.hand = init_hand(self.deck)
			
	#Parses the stats of each player and displays them on a line by line basis
	def get_game_state(self):
		s = ""
		for p in self.players:
			s += "Player: " + p.name + " - Floor: B" + str(p.floor) + "F  - Gold: " + str(p.gold) + " - Ore: " + str(p.ore) + "\n"
		self.game_state = s
	
	#Gets available targets for player and presents stats
	def get_targets(self, user_name):
		s = ""
		i = 0
		for p in self.players:
			if p.name != user_name:
				i += 1
				s += "Player" + i + ": " + p.name + " - Floor: B" + str(p.floor) + "F  - Gold: " + str(p.gold) + " - Ore: " + str(p.ore) + "\n"
		return s
	
	#Checks if all players have finished playing a card this turn
	def check_turn(self):
		for p in self.players:
			if not p.turn_done:
				return False
		return True	
		
	#After all players have played a card, this will process the effects of the cards and update the player stats
	def calculate_game_state(self):
		exchange_players = []
		exchange_counter = 0
		for key in self.played_cards:
			if self.played_cards[key].name == "Rush":
				player = get_player(key)
				player.floor += 3
				player.ore += 9
			if self.played_cards[key].name == "Exchange":
				player = get_player(key)
				exchange_players.append(player)
				exchange_counter += 1
		for p in exchange_players:
			if exchange_counter == 1:
				p.gold += p.ore
				p.ore = 0
			if exchange_counter == 2:
				p.gold += p.ore
				p.ore = p.ore // 3
			if exchange_counter == 3:
				p.gold += p.ore * 2
				p.ore = p.ore // 3
			if exchange_counter == 4:
				p.ore = 0
		#for key in self.played_cards:
			#if self.played_cards[key].name == "Goblin":
		turn_clear()
		next_turn()

class player():
	def __init__(self,name):
		self.name = name
		self.gold = 0
		self.ore = 3
		self.floor = 1
		self.hand = []
		self.played_card = None
		self.draw = False
		self.target = None
		self.turn_done = False
		
	#When a player clicks to play a card, the card they played is logged and removed from their hand
	def play_card(self, index):
		self.played_card = self.hand[index]
		self.hand.remove(self.hand[index])
	
	#Draws a new card at the start of a turn
	def turn_draw(self, deck):
		draw_card(self.hand, deck)
		self.draw = True
	
	#Gets image files from cards in hand and merges them
	def show_hand(self):
		files = []
		for c in self.hand:
			files.append(c.image)
		merge_all(files)

class card():
	def __init__ (self,name,card_type,cost,image):
		self.name = name
		self.card_type = card_type
		self.cost = cost
		self.image = image

#Combines two image files side by side
def merge_images(file1, file2):
	image1 = Image.open(file1)
	image2 = Image.open(file2)

	(width1, height1) = image1.size
	(width2, height2) = image2.size
    
	width_buffer = 10
    
	result_width = width1 + width2 + width_buffer
	result_height = max(height1, height2)

	result = Image.new('RGBA', (result_width, result_height))
	result.paste(im=image1, box=(0, 0))
	result.paste(im=image2, box=(width1 + width_buffer, 0))
	return result
	
#Combines all provided image files side by side
def merge_all(files):
	length = len(files)
	img_file = files[0]
	files.remove(img_file)
	for f in files:
		img_file = merge_images(img_file,f)
		img_file.save('GeneratedImage.png')
		img_file = 'GeneratedImage.png'

#Generates a standard deck with set ratios of cards
def init_deck():
	deck = []
	#init card and append to deck
	exchange_card = card("Exchange","Stack",0,"Exchange.png")
	for x in range(30):
		deck.append(exchange_card)
	goblin_card = card("Goblin","Minion",0,"Goblin.png")
	for x in range(10):
		deck.append(goblin_card)
	hitman_card = card("Hitman","Minion",2,"Hitman.png")
	for x in range(5):
		deck.append(hitman_card)
	savage_card = card("Savage","Minion",4,"Savage.png")
	for x in range(5):
		deck.append(savage_card)
	rush_card = card("Rush","Standard",0,"Rush.png")
	for x in range(10):
		deck.append(rush_card)
	return deck

#Shuffles the indexes of all cards within the deck
def shuffle(deck):
	for x in range(len(deck)):
		temp = deck[x]
		index = random.randint(0,len(deck)-1)
		deck[x] = deck[index]
		deck[index] = temp
	return deck

#Draws three cards from the deck for a beginning hand (4th drawn separately)
def init_hand(deck):
	hand = []
	for x in range(3):
		draw_card(hand,deck)
	return hand

#Draw a card from the deck, remove that card from the deck and add to hand
def draw_card(hand,deck):
	if len(deck) < 1:
		deck = init_deck()
		deck = shuffle(deck)
	hand.append(deck[0])
	deck.remove(deck[0])

client = bot()

#Cache
games = [] #id, list of players, game state, deck, played cards


#Slash Commands
tree = app_commands.CommandTree(client)

#Creates a game and adds host to game. Displays Join Menu
@tree.command(guild=discord.Object(id=451230209602093058), name='create-game', description='Create a Game Instance')
async def test_game(interaction: discord.Interaction):
	host = player(interaction.user.name)
	new_game = game(host)
	games.append(new_game)
	menu = join_menu(new_game.id)
	await interaction.response.send_message(new_game.players[0].name + "Created a Game. Number of Players: 1",view = menu)

#RUN
client.run(token)
