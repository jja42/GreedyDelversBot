import discord
from discord import app_commands
import random
import asyncio
import string #TEMP
from PIL import Image

#Load Bot Token and Server ID
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
				 await interaction.response.send_message("You've drawn already!",ephemeral = True)
			else:
				current_game.player_draw(interaction.user.name)
				picture = discord.File('GeneratedImage.png')
				menu = play_menu(current_game.id)
				await interaction.response.send_message(file=picture, view = menu, ephemeral = True)			
		else:
			await interaction.response.send_message("You're not in this game!",ephemeral = True)

#Displays buttons for each playable card
class play_menu(discord.ui.View):
	def __init__(self, game_id, num_cards=4):
		super().__init__()
		self.game_id = game_id

		# Dynamically create buttons for however many cards are in the hand
		for i in range(num_cards):
			button = discord.ui.Button(
				label=f"Play Card {i+1}",
				style=discord.ButtonStyle.gray
			)
			button.callback = self.make_play_callback(i)
			self.add_item(button)

	def make_play_callback(self, index):
		async def callback(interaction: discord.Interaction):
			current_game = games[self.game_id]
			if current_game.check_users(interaction.user.name):
				if current_game.check_play(interaction.user.name):
					await interaction.response.send_message("You've already played a card!", ephemeral=True)
					return

				if current_game.check_cost(interaction.user.name, index):
					current_game.player_play(interaction.user.name, index)
					card = current_game.get_played_card(interaction.user.name)
					if card.card_type == "Minion":
						targets = current_game.get_targets(interaction.user.name)
						menu = target_menu(current_game.id, interaction.user.name, targets)
						await interaction.response.send_message("Select a Target for your Minion",view=menu, ephemeral=True)
					else:
						current_game.player_done(interaction.user.name)
						if current_game.check_turn():
							current_game.calculate_game_state()
							current_game.get_turn_resolution()
							current_game.finishTurn()
							current_game.get_game_state()
							menu = draw_menu(current_game.id)
							if(current_game.end):
								text = current_game.turn_state
								text += "\n\n"
								text += current_game.game_state
								text += "\n\nThe Game Has Ended.\n The Winner is: "
								text += current_game.get_winner().name
								await interaction.response.send_message(text)
							else:
								text = current_game.turn_state
								text += "\n\n"
								text += current_game.game_state
								await interaction.response.send_message(current_game.text, view=menu)
						else:
							await interaction.response.send_message("Successfully played a card. Please wait for others to finish", ephemeral=True)
				else:
					await interaction.response.send_message("You don't have enough gold to play this card!", ephemeral=True)
			else:
				await interaction.response.send_message("You're not in this game!", ephemeral=True)

		return callback

#Displays buttons for each targetable player, excluding self
class target_menu(discord.ui.View):
	def __init__(self, game_id, player, targets):
		super().__init__()
		self.game_id = game_id
		self.targets = targets

		# Dynamically add buttons based on the target list
		for i, t in enumerate(targets):
			button = discord.ui.Button(
				label=f"Target {t}",
				style=discord.ButtonStyle.gray
			)
			button.callback = self.make_target_callback(i)
			self.add_item(button)

	def make_target_callback(self, index):
		async def callback(interaction: discord.Interaction):
			current_game = games[self.game_id]
			if current_game.check_users(interaction.user.name):
				if current_game.check_target(interaction.user.name):
					await interaction.response.send_message("You've already selected a target!", ephemeral=True)
				else:
					current_game.player_target(interaction.user.name, index + 1)
					current_game.player_done(interaction.user.name)
					if current_game.check_turn():
						current_game.calculate_game_state()
						current_game.get_turn_resolution()
						current_game.finishTurn()
						current_game.get_game_state()
						menu = draw_menu(current_game.id)
						if(current_game.end):
							text = current_game.turn_state
							text += "\n\n"
							text += current_game.game_state
							text += "\n\nThe Game Has Ended.\n The Winner is: "
							text += current_game.get_winner().name
							await interaction.response.send_message(text)
						else:
							text = current_game.turn_state
							text += "\n\n"
							text += current_game.game_state
							await interaction.response.send_message(current_game.text, view=menu)
					else:
						await interaction.response.send_message("Successfully played a card. Please wait for others to finish", ephemeral=True)
			else:
				await interaction.response.send_message("You're not in this game!", ephemeral=True)
		return callback


class game():
	def __init__(self, host):
		self.id = len(games)
		self.players = []
		self.players.append(host)
		self.game_state = ""
		self.turn_state = ""
		self.deck = init_deck()
		self.deck = shuffle(self.deck)
		self.played_cards = {}
		self.turnCount = 1
		self.endZone = []
		self.end = False 
	
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
				return c.cost <= p.gold
		return False
	
	#Draws a card for the player and creates their hand (image)
	#Card Pre-drawn to fix issues with clicking wrong buttons
	def player_draw(self, user_name):
		for p in self.players:
			if p.name == user_name:
				p.show_hand()
				p.draw = True
		
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
							p.target = t
							t.targetedBy.append(p)
	
	#Clears Turn Parameters for Players and Game		
	def turn_clear(self):
		for p in self.players:
			p.played_card = None
			p.draw = False
			p.target = None
			p.targetedBy = []
			p.turn_done = False
			p.minionFactor = 1
			p.minionNegated = False
			p.minionGain = 0
			p.goldGain = 0
			p.floorGain = 0
			p.played_cards = {}
	
	#Progress Game State to Next Turn
	#Also Handle Reaching the End
	def next_turn(self):
		self.turnCount += 1
		players_to_remove = []
		for p in self.players:
			p.floor += 1
			if p.floor >= 30:
				p.floor = 30
				self.endZone.append(p)
				players_to_remove.append(p)
			else:
				p.ore += 3
				p.turn_draw(self.deck)
		# remove end-zone players from player list
		for p in players_to_remove:
			self.players.remove(p)
		
		if(len(self.players) == 0):
			self.end = True
	
	#Initializes the starting hands for each player
	def start_game(self):
		while(len(self.players) <4):
			new_player = player(''.join(random.choice(string.ascii_letters) for _ in range(5)))
			self.players.append(new_player)
		for p in self.players:
			p.hand = init_hand(self.deck)
			
	#Parses the stats of each player and displays them on a line by line basis
	def get_game_state(self):
		s = "Turn: " + str(self.turnCount) + "\n"
		for p in self.players:
			s += "Player: " + p.name + " - Floor: B" + str(p.floor) + "F  - Gold: " + str(p.gold) + " - Ore: " + str(p.ore) + "\n"
		self.game_state = s
		
	#Get the turnout of each turn and log it	
	def get_turn_resolution(self):
		s = "Turn Results\n"
		for p in self.players:
			s += "Player: " + p.name + "Played: " + p.played_card.name + "\n"
			if(p.floorGain > 0):
				s += p.name + " Rushed Forward 3 Floors. Gaining 9 Ore."
			if(p.target != None):
				s += p.name + " Targeted " + p.target.name + "\n"
				if(p.minionNegated):
					s += p.name + "'s Minion Was Negated!"
				else:
					s += p.name + " Minion Roll Result = " + p.minionRoll + "\n"
					if(p.minionSuccess):
						s += p.name + "'s Minion Stole " + p.minionGold + "Gold!\n"
					else:
						s += p.name + "'s Minion was Unsuccessful.\n"
			s += "Player: " + p.name + " Gained " + str(p.goldGain) +" Gold\n\n"
		s += "Players Delve Deeper into the Mines, Progressing Forward 1 Floor and Gaining 3 Gold\n\n"
	
	#Gets available targets for player
	def get_targets(self, user_name):
		targets = []
		for p in self.players:
			if p.name != user_name:
				targets.append(p.name)
		return targets

		
	#Gets card played by player
	def get_played_card(self, user_name):
		for p in self.players:
			if p.name == user_name:
				return self.played_cards[p.name]
				
	#Gets a player in the game 
	def get_player(self, user_name):
		for p in self.players:
			if p.name == user_name:
				return p
		
	
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
		minion_players = []
		minions = []
		for key in self.played_cards:
			if self.played_cards[key].name == "Rush":
				player = self.get_player(key)
				player.floor += 3
				player.ore += 9
			if self.played_cards[key].name == "Exchange":
				player = self.get_player(key)
				exchange_players.append(player)
				exchange_counter += 1
			if 	self.played_cards[key].card_type == "Minion":
				player = self.get_player(key)
				player.gold -= player.played_card.cost
				minion_players.append(player)
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
		self.resolveMinions(minion_players)
		
	#Figure out the Winner
	def get_winner(self):
		wealth = 0
		winner = None
		for p in self.endZone:
			if p.gold > wealth:
				weatlh = p.gold
				winner = p
		return winner
		
	#Handle Minion Resolution
	def resolveMinions(self, minionPlayers):
		if(len(minionPlayers) == 0): 
			return 
		
		#Build target map
		target_map = {}
		for p in minionPlayers:
			target_map.setdefault(p.target, []).append(p)

		#If 3 or more minions used, each targeting a different player, all are negated
		if len(minionPlayers) >= 3 and len(target_map) == len(minionPlayers):
			for p in minionPlayers:
				p.minionNegated = True
			return  # All minions negated

		#If 4 minions played and 1 player is untargeted
		if len(minionPlayers) == 4 and len(target_map) == 3:
			for p in minionPlayers:
				p.minionNegated = True
				if p not in target_map:
					p.minionNegated = False #Only untargeted resolves
		
		#If 4 minions are played, two pairs targeting 2 targets ie: (1,2 -> 3 & 3,4 -> 2)
		if(len(minionPlayers) == 4 and len(target_map) == 2):
			targets = list(target_map.keys())
			t1, t2 = targets[0], targets[1]

			#Check target pairs targeting each other
			if t1.target == t2 and t2.target == t1:
				#Negate the minions of the target
				t1.minionNegated = True
				t2.minionNegated = True
		
		#If multiple players target one player with a minion and are untargeted
		for victim, attackers in target_map.items():
			if len(attackers) >= 2:
				untargeted_attackers = 0
				for attacker in attackers:
					if attacker not in target_map:
						untargeted_attackers += 1
				if(untargeted_attackers == len(attackers)):
					victim.minionNegated = True
					for attacker in attackers:
						attacker.minionFactor = 0.5
						
		#Check Remaining Minion Negation
		for victim, attackers in target_map.items():
			if(victim in minionPlayers and not victim.minionNegated):
				for attacker in attackers:
					attacker.minionNegated = True
				victim.minionNegated = True
				
		for p in minionPlayers:
			if p.minionNegated == False:
				self.resolveMinion(p) 
			
	
	def resolveMinion(self,player):
		dieRoll = random.randint(1,6)
		stolen = 0
		if player.played_card.name == "Goblin":
			if dieRoll >= 4:
				stolen = player.target.steal_gold(2 * player.minionFactor)
				player.minionSuccess = True
		if player.played_card.name == "Hitman":
			if dieRoll >= 3:
				stolen = player.target.steal_gold(6 * player.minionFactor)
				player.minionSuccess = True
		if player.played_card.name == "Savage":
			if dieRoll >= 4:
				stolen = player.target.steal_gold(12 * player.minionFactor)
				player.minionSuccess = True
		player.gold += stolen
		player.minionGain = stolen
		player.minionRoll = dieRoll
	
	#Quick Wrapper for Clearing Turn and Moving Forward
	def finishTurn(self):
		self.turn_clear()
		self.next_turn()
			

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
		self.minionFactor = 0.5
		self.minionNegated = False
		self.minionRoll = 0
		self.minionSuccess = False
		self.minionGain = 0
		self.goldGain = 0
		self.floorGain = 0
		self.targetedBy = []
		
	#When a player clicks to play a card, the card they played is logged and removed from their hand
	def play_card(self, index):
		self.played_card = self.hand[index]
		self.hand.remove(self.hand[index])
	
	#Draws a new card at the start of a turn
	def turn_draw(self, deck):
		draw_card(self.hand, deck)
	
	#Gets image files from cards in hand and merges them
	def show_hand(self):
		files = []
		for c in self.hand:
			files.append(c.image)
		merge_all(files)
	
	#Attempt to take as much gold as possible
	def steal_gold(self, amount):
		stolen = 0
		if self.gold >= amount:
			self.gold -= amount
			return amount
		else:
			stolen = self.gold
			self.gold = 0
			return stolen

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

#Draws three cards from the deck for a beginning hand
def init_hand(deck):
	hand = []
	for x in range(4):
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
