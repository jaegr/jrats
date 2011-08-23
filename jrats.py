# -*- coding: utf-8 -*-
import pygame
import random
import os

import glob
import tile
import weapons
import level
import rat
import sys
from collections import deque

#TODO       powerups
#TODO       bättre lösning för att spara banor
#TODO       vapen till leveleditor

black = (   0, 0, 0)
white = ( 255, 255, 255)
green = (   0, 255, 0)
red = ( 255, 0, 0)
blue = (   0, 0, 255)
yellow = ( 255, 255, 0)
corn_blue = (100, 149, 237)
pink = (251, 174, 210)
mustard = (255, 219, 88)
dark_gray = (139, 133, 137)
light_gray = 	(244, 240, 236)

pygame.init()
pygame.font.init() #initierar textutskrift
size = [800, 672]
screen = pygame.display.set_mode(size)
pygame.display.set_caption("jRats")
clock = pygame.time.Clock()

class GameStateStack(object):
    """Keeps track of game states and runs the states' event, update and draw methods"""
    def __init__(self):
        #Initializes the game stack and pushes the main menu state to the stack
        self.stack = []
        self.stack.append(MainMenu(self))

    def main(self):
        #Runs the basic methods of the last item on the stack
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                self.stack[-1].handle_event(event)
            self.stack[-1].update()
            self.stack[-1].draw()

    def push(self, state):
        """Pushes a state to the stack"""
        self.stack.append(state)

    def pop(self, **kwargs):
        """Pops a state from the stack"""
        self.stack.pop()
        #Handles values returned by a popped game state
        if kwargs:
            self.stack[-1].recieve_values(**kwargs)


class GameState(object):
    """Base class for game states"""

    def update(self):
        """Empty base class method"""
        pass

    def draw(self):
        """Method for filling the screen with black and drawing text objects"""
        screen.fill(black)
        self.draw_text()
        pygame.display.flip()

    def handle_event(self, event):
        """Handles mouse clicks and sends the mouse position to the handle_mouse method of the child class"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_mouse(event.pos[0], event.pos[1])


class MainMenu(GameState):
    """The main menu state gives the user access to the other available game states"""
    def __init__(self, stack):
        self.stack = stack
        self.menu_font = pygame.font.Font(None, 40)
        self.menu_text = {'Play': {'text': 'Play game', 'x': 630, 'y': 300},
                          'Editor' : {'text': 'Level editor', 'x': 630, 'y': 350},
                          'Options': {'text': 'Options', 'x': 630, 'y': 400},
                          'Help': {'text': 'Help', 'x': 630, 'y': 450},
                          'Exit': {'text': 'Exit', 'x': 630, 'y': 500}}
        #Default options
        self.options = {'Difficulty': 'Normal', 'Music': 'No', 'Music volume': '0.5', 'Sound volume': '0.5'}
        self.image = pygame.image.load(os.path.join('data', 'images', 'main.png')).convert_alpha()
        self.rect = self.image.get_rect()
        self.initialize_text()

    def initialize_text(self):
        """Gets a render and rect for every item in menu_text"""
        for menu_item in self.menu_text.values():
            render = self.menu_font.render(menu_item['text'], True, white)
            render_rect = render.get_rect(x=menu_item['x'], y=menu_item['y'])
            menu_item['render'] = render
            menu_item['rect'] = render_rect

    def draw_text(self):
        """Draws the items in menu_text"""
        for menu_item in self.menu_text.values():
            screen.blit(menu_item['render'], menu_item['rect'])

    def draw(self):
        """Draws the image and text"""
        screen.fill(black)
        screen.blit(self.image, self.rect)
        self.draw_text()
        pygame.display.flip()

    def recieve_values(self, **kwargs):
        """Handles the options returned from the options state"""
        for key, value in kwargs.items():
            if key == 'options':
                self.options = value

    def handle_mouse(self, mouse_x, mouse_y):
        """Checks if user clicked on an item in the menu and pushes the corresponding state to the game state stack"""
        for menu_item in self.menu_text.values():
            rect = menu_item['rect']
            if rect.collidepoint(mouse_x, mouse_y):
                if menu_item['text'] == 'Play game':
                    self.stack.push(Game(self.options, self.stack))
                elif menu_item['text'] == 'Level editor':
                    self.stack.push(LevelEditor(self.options, self.stack))
                elif menu_item['text'] == 'Options':
                    self.stack.push(OptionsScreen(self.options, self.stack))
                elif menu_item['text'] == 'Help':
                    self.stack.push(HelpScreen(self.stack))
                elif menu_item['text'] == 'Exit':
                    sys.exit()
                    
class HelpScreen(GameState):
    """Help screen game state"""
    def __init__(self, stack):
        self.stack = stack
        self.help_font = pygame.font.Font(None, 20)
        self.help_strings = ['The objective of jRats is to kill all the rats on the level. The game is over if the rat population reaches 50.',
                          'You have a number of weapons to help you fight the rats, which are randomly generated and given to you.',
                          '',
                          'Stop sign - Makes the rat change direction. Disappears after five hits.',
                          'Poison - Kills one rat before disappering.',
                          'Terminator rat - Acts like a regular rat, but will kill five rats upon collision.',
                          'Bomb - The bomb will explode five seconds after being placed, and the explosion will kill everything in its way.',
                          'Gender change - Will change the gender of one rat. Will also turn terminator rats into a regular rat.',
                          'Nuke - Sterilizes all rats who come in contact with the radiation. Sterilized rats can\'t have babies.',
                          'Toxic waste - All rats that come in contact with the toxic gas die.']
        self.back_button = {}
        self.initialize_text()

    def initialize_text(self):
        """Creates renders and rects from the text in help_strings and gets a render and rect for the back button"""
        renders = [self.help_font.render(line, True, white) for line in self.help_strings]
        rects = [render.get_rect(x = 50, y = 50 + 20 * i) for i, render in enumerate(renders)]
        self.help_text = zip(renders, rects)
        self.back_button['render'] = self.help_font.render('Back', True, white)
        self.back_button['rect'] = self.back_button['render'].get_rect(x = 50, y = 600)

    def draw_text(self):
        """Draws the help text and the back button text"""
        screen.blit(self.back_button['render'], self.back_button['rect'])
        for render, rect in self.help_text:
            screen.blit(render, rect)

    def handle_mouse(self, mouse_x, mouse_y):
        """Handles clicking on the back button"""
        if self.back_button['rect'].collidepoint(mouse_x, mouse_y):
            self.stack.pop()

class OptionsScreen(GameState):
    """Options screen game state"""
    def __init__(self, choices, stack):
        self.stack = stack
        #Gets current options from the main menu state
        self.choices = choices
        self.options_font = pygame.font.Font(None, 20)
        #All options have a descriptive label, as well as a sub-dictionary of the available choices
        self.options_text = {'Difficulty':
                                 {'text': 'Difficulty:', 'x': 100, 'y': 100, 'option': False, 'choices':
                                    {
                                    'Easy': {'text': 'Easy', 'x': 200, 'y': 100, 'option': True},
                                    'Normal': {'text': 'Normal', 'x': 200, 'y': 120, 'option': True},
                                    'Hard': {'text': 'Hard', 'x': 200, 'y': 140, 'option': True}}},

                                'Music': {'text': 'Music:', 'x': 100, 'y': 200, 'option': False, 'choices':
                                    {
                                    'Yes': {'text': 'Yes', 'x': 200, 'y': 200, 'option': True},
                                    'No': {'text': 'No', 'x': 200, 'y': 220, 'option': True}}},
                                'Music volume': {'text': 'Music volume:', 'x': 100, 'y': 280, 'option': False, 'choices':
                                    {
                                    'Increase': {'text': '+', 'x': 245, 'y': 280, 'option': True},
                                    'Value': {'text': self.choices['Music volume'], 'x': 220, 'y': 280, 'option': False},
                                    'Decrease': {'text': '-', 'x': 210, 'y': 280, 'option': True}}},
                                'Sound volume': {'text': 'Sound volume:', 'x': 100, 'y': 340, 'option': False, 'choices':
                                    {
                                    'Increase': {'text': '+', 'x': 245, 'y': 340, 'option': True},
                                    'Value': {'text': self.choices['Sound volume'], 'x': 220, 'y': 340, 'option': False},
                                    'Decrease': {'text': '-', 'x': 210, 'y': 340, 'option': True}}},
                                'Back': {'text': 'Back', 'x': 100, 'y': 400, 'choices': ''},
                                'Info': {'text': 'Add music to sounds/music folder. OGG is recommended, MP3-support limited.', 'x': 250, 'y': 200, 'choices': ''}}

        self.initialize_font()

    def initialize_font(self):
        """Initialize all the font objects by giving them a render and a rect"""
        for item in self.options_text:
            self.options_text[item]['render'], self.options_text[item]['rect'] = self.get_render_and_rect(self.options_text[item])
            for choice in self.options_text[item]['choices']:
                #Checks if the option is the selected option, and in that case make it red instead of white
                if self.choices[item] == self.options_text[item]['choices'][choice]['text'] and 'volume' not in item:
                    color = red
                else:
                    color = white
                self.options_text[item]['choices'][choice]['render'], self.options_text[item]['choices'][choice]['rect'] = self.get_render_and_rect(self.options_text[item]['choices'][choice], color)

    def set_color(self, item, choice, color):
        """Sets color of the choice to the given color"""
        self.options_text[item]['choices'][choice]['render'] = self.options_font.render(self.options_text[item]['choices'][choice]['text'], True, color)

    def set_volume(self, item, choice):
        """Handles changes volume options changes"""
        current_volume = float(self.options_text[item]['choices']['Value']['text'])
        if choice == 'Increase':
            #Only increase volume if current_volume < 1
            self.options_text[item]['choices']['Value']['text'] = str(1.0) if current_volume == 1.0 else str(current_volume + 0.1)
        else:
            #Only decrease volume if current_volume > 0
            self.options_text[item]['choices']['Value']['text'] = str(0.0) if current_volume == 0.0 else str(current_volume - 0.1)
        self.options_text[item]['choices']['Value']['render'] = self.get_render_and_rect(self.options_text[item]['choices']['Value'], set_rect=False)
        self.choices[item] = self.options_text[item]['choices']['Value']['text']
        
    def get_render_and_rect(self, text_item, color=white, set_render=True, set_rect=True):
        """Returns a render and/or a rect"""
        if set_render:
            render = self.options_font.render(text_item['text'], True, color)
            if not set_rect:
                return render
        if set_rect:
            rect = render.get_rect(x = text_item['x'], y = text_item['y'])
            if not set_render:
                return rect
        return render, rect


    def handle_mouse(self, mouse_x, mouse_y):
        """Handles clicks on options"""
        for item in self.options_text:
            if self.options_text['Back']['rect'].collidepoint(mouse_x, mouse_y) and item == 'Back':
                self.stack.pop(options=self.choices)
            for choice in self.options_text[item]['choices']:
                if self.options_text[item]['choices'][choice]['rect'].collidepoint(mouse_x, mouse_y):
                    if self.choices[item] == choice: #If the choice is the same as the previous, return
                        return
                    if item == 'Sound volume' or item == 'Music volume':
                        self.set_volume(item, choice)
                    else:
                        self.set_color(item, choice, red) #Change the color of the choice from black to red
                        self.set_color(item, self.choices[item], white) #Change color of the previous choice from red to black
                        self.choices[item] = choice #Set option to current choice

    def draw_text(self):
        """Draws all rendered fonts"""
        for item in self.options_text:
            screen.blit(self.options_text[item]['render'], self.options_text[item]['rect'])
            for choice in self.options_text[item]['choices']:
                screen.blit(self.options_text[item]['choices'][choice]['render'], self.options_text[item]['choices'][choice]['rect'])


class GameOverScreen(GameState):
    """The screen shown when the player either wins or loses"""
    def __init__(self, score, stack):
        #Takes the score from the gaming session as input
        self.stack = stack
        self.gameover_font = pygame.font.Font(None, 50)
        self.gameover_text = {'Total': {'text': 'Total number of rats killed:', 'x': 200, 'y': 200},
                            'Score': {'text': str(score), 'x': 400, 'y': 250 },
                            'Back': {'text': 'Main menu', 'x': 50, 'y': 600}}
        self.initialize_text()

    def initialize_text(self):
        """Gets renders and rects for items in gameover_text""" 
        for text_item in self.gameover_text.values():
            render = self.gameover_font.render(text_item['text'], True, white)
            rect = render.get_rect(x = text_item['x'], y = text_item['y'])
            text_item['render'] = render
            text_item['rect'] = rect

    def draw_text(self):
        """Draws items in gameover_text"""
        for text_item in self.gameover_text.values():
            screen.blit(text_item['render'], text_item['rect'])

    def handle_mouse(self, mouse_x, mouse_y):
        """Handles mouse clicks"""
        if self.gameover_text['Back']['rect'].collidepoint(mouse_x, mouse_y):
            self.stack.pop()


class LevelEditor(GameState):
    """Level editor for creating, testing and saving custom maps"""
    def __init__(self, options, stack):
        self.stack = stack
        self.map = []
        self.options = options
        self.done = False
        self.editor_font = pygame.font.Font(None, 20)
        self.editor_text = {'Play': {'text': 'Play', 'x': 700, 'y': 200},
                          'Save': {'text': 'Save', 'x': 700, 'y': 250},
                          'Clear': {'text': 'Clear', 'x': 700, 'y': 300},
                          'Exit': {'text': 'Exit', 'x': 700, 'y': 350}}
        self.tile_size = 32
        self.initialize_map()
        self.initialize_text()
        self.motion = False
        self.active_tile = None

    def initialize_text(self):
        """Gets renders and rects for items in editor_text"""
        for text_item in self.editor_text.values():
            render = self.editor_font.render(text_item['text'], True, white)
            rect = render.get_rect(x = text_item['x'], y = text_item['y'])
            text_item['render'] = render
            text_item['rect'] = rect

    def initialize_map(self):
        """Initializes an empty map array"""
        #Creates a 20x20 two dimensional array which consists of '.' inside a frame of '#'
        self.map = [['.' if x != 0 and y != 0 and x != 20 and y != 20 else '#' for x in range(21)] for y in range(21)]

    def save(self):
        #Saves the map to a textfile, which the user must manually add to the map.txt
        save_file = open(os.path.join('data', 'temp_map.txt'), 'w+')
        for row in self.map:
            save_file.write(''.join(row) + '\n')
        save_file.close()


    def draw_map(self):
        """Draws the map"""
        x = 0
        y = 0
        for i, row in enumerate(self.map):
            for n, col in enumerate(self.map):
                #For each item in self.map, draw either a light_gray or a dark_gray rectangle based on the item character
                color = light_gray if self.map[i][n] == '.' else dark_gray
                pygame.draw.rect(screen, color, pygame.Rect(x, y, self.tile_size, self.tile_size))
                x += self.tile_size
            y += self.tile_size
            x = 0

    def draw_text(self):
        """Draws the text in the menu"""
        for text_item in self.editor_text.values():
            screen.blit(text_item['render'], text_item['rect'])

    def handle_mouse(self, mouse_x, mouse_y):
        """Handles mouse clicks and clicks and drags"""
        #active_tile tracks which tile is currently being drawn 
        #You can draw either a path or a wall by clicking a tile of the opposite type.
        aligned_x = mouse_x / self.tile_size
        aligned_y = mouse_y / self.tile_size
        if aligned_x < 20 and aligned_y < 20 and aligned_x > 0 and aligned_y > 0:
            if not self.active_tile:
                self.active_tile = '.' if self.map[aligned_y][aligned_x] == '#' else '#'
            self.map[aligned_y][aligned_x] = self.active_tile
        for text_item in self.editor_text.values():
            rect = text_item['rect']
            if rect.collidepoint(mouse_x, mouse_y):
                self.action(text_item['text'])

    def action(self, key_action):
        """Executes an action based on which button is clicked"""
        if key_action == 'Play':
            self.stack.push(Game(self.options, self.stack, self.map))
        elif key_action == 'Save':
            self.save()
        elif key_action == 'Clear':
            self.initialize_map()
        elif key_action == 'Exit':
            self.stack.pop()

    def handle_event(self, event):
        """Handles mouse events"""
        #If the player is clicking and dragging to draw, set motion = True, which will keep drawing the acting tile where the user drags the cursor.
        #Once the user releases the mouse button, stop drawing and reset active_tile
        if event.type == pygame.MOUSEMOTION and event.buttons[0]:
            self.motion = True
            self.handle_mouse(event.pos[0], event.pos[1])
        elif self.motion or event.type == pygame.MOUSEBUTTONUP:
            self.active_tile = None
            self.motion = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_mouse(event.pos[0], event.pos[1])

    def draw(self):
        """Draw the graphics"""
        screen.fill(black)
        self.draw_map()
        self.draw_text()
        pygame.display.flip()


class Menu_items(pygame.sprite.DirtySprite): 
    """Class for handling the images in the game menu"""
    def __init__(self, game, name, x, y):
        pygame.sprite.DirtySprite.__init__(self)
        self.game = game
        self.name = name
        self.image = self.game.graphics[self.name]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.dirty = 1
        self.visible = 0


class Game(GameState):
    def __init__(self, options, stack, editor_map = None):
        self.stack = stack
        pygame.mixer.init() 
        self.graphics = {} 
        self.sounds = {}   
        self.options = options
        self.initialize_graphics() 
        self.initialize_sounds()   
        self.score = 0
        self.music_event = pygame.USEREVENT 
        if self.options['Music'] == 'Yes':
            self.initialize_music()
        self.editor_map = editor_map
        self.reset()               
        self.board_width = self.board_height = 20 * tile.tile_size #The board is 21 tiles high and wide, and each tile is 32 x 32

    def reset(self, level=1):
        self.menu_items = {} #For the weapon icons in the menu
        self.level = level   
        self.initialize_menu() 
        self.male_rat_sprites = pygame.sprite.LayeredDirty() 
        self.female_rat_sprites = pygame.sprite.LayeredDirty()
        self.child_rat_sprites = pygame.sprite.LayeredDirty()
        self.weapon_sprites = pygame.sprite.LayeredDirty()
        self.tile_sprites = pygame.sprite.LayeredDirty()
        self.dirty_tiles = pygame.sprite.LayeredDirty()

        self.done = False #Anger om spelet är slut
        self.num_levels = 0
        self.create_level() #Skapar banan
        self.initial_population()
        self.population_count = {'M': 0, 'F': 0}
        self.male_ui_rect = pygame.Rect(700, 650, 50, 0) #The population counter graphic
        self.female_ui_rect = pygame.Rect(700, 650, 50, 0) 
        self.population_frame = pygame.Rect(700, 650, 50, -200) #The population counter graphic frame
        self.menu_font = pygame.font.Font(None, 18) 
        self.win = False
        self.active_rectangle = pygame.Rect(0, 0, 0, 0) #Rectangle drawn around the active weapon
        self.active_weapon = None 
        self.last_generated_weapon = pygame.time.get_ticks() 
        self.generate_weapons() 
        self.collision_time = pygame.time.get_ticks()


    def initialize_music(self):
        """Imports the music files in the music directory and add them to a playlist"""
        self.music = deque()
        file_types = ['*.mp3', '*.ogg']
        for file_type in file_types:
            self.music.extend(glob.glob(os.path.join('data', 'sounds', 'music', file_type)))
        if not len(self.music):
            return
        random.shuffle(self.music)
        self.handle_music()

    def handle_music(self):
        """Runs when the music_event is generated. Loads the next song in the playlist, sets the volume and plays the song"""
        pygame.mixer.music.load(self.music[0])
        pygame.mixer.music.set_volume(float(self.options['Music volume']))
        pygame.mixer.music.play()
        pygame.mixer.music.set_endevent(self.music_event)
        self.music.rotate()

    def initial_population(self):
        """Initializes the initial rat population, which is based on the difficulty level"""
        difficulty = self.options['Difficulty']
        if difficulty == 'Easy':
            number_of_rats = 5
        elif difficulty == 'Normal':
            number_of_rats = 10
        else:
            number_of_rats = 15
        for i in range(number_of_rats):
            x = y = 0
            while self.leveltest.is_wall(x, y): #Keep generating coordinates until the position is not a wall
                x, y = random.randrange(21), random.randrange(21) 
            x *= tile.tile_size 
            y *= tile.tile_size
            self.create_rat(x, y, isAdult=True)

    def get_number_of_levels(self):
        """Gets the number of levels from the level instance"""
        self.num_levels = self.leveltest.number_of_levels()

    def create_level(self):
        """Create an instance of the level class, and loads the map and tileset"""
        self.leveltest = level.Level(self.level, self, self.editor_map)
        if not self.num_levels:
            self.get_number_of_levels()
        self.leveltest.load_map()
        self.load_tileset()
        self.leveltest.load_tile_map()
        for row in self.leveltest.tile_map:
            for col in row:
                self.tile_sprites.add(col)
        for row in self.leveltest.map:
            print ''.join(row)

    def load_tileset(self):
        """Get the current tileset from the level instance and load the graphics"""
        self.tileset = self.leveltest.tile_set
        self.graphics['Path'] = [pygame.image.load(os.path.join('data', 'images', self.tileset, '{0}.png'.format(i))).convert_alpha() for i in range(15)]
        self.graphics['Wall'] = [pygame.image.load(tile_path) for tile_path in glob.glob(os.path.join('data', 'images', self.tileset, 'wall*.png'))]
        self.graphics['Decorations'] = [pygame.image.load(tile_path) for tile_path in glob.glob(os.path.join('data', 'images', self.tileset, 'decoration*.png'))]

    def initialize_graphics(self):
        """Load all sprites"""
        self.graphics['Stop sign'] = pygame.image.load(os.path.join('data', 'images', 'stop.png')).convert_alpha()
        self.graphics['Poison'] = pygame.image.load(os.path.join('data', 'images', 'poison.png')).convert_alpha()
        self.graphics['Male rat'] = pygame.image.load(os.path.join('data', 'images', 'male.png')).convert_alpha()
        self.graphics['Female rat'] = pygame.image.load(os.path.join('data', 'images', 'female.png')).convert_alpha()
        self.graphics['Baby rat'] = pygame.image.load(os.path.join('data', 'images', 'baby_rat.png')).convert_alpha()
        self.graphics['Terminator'] = pygame.image.load(os.path.join('data', 'images', 'terminator.png')).convert_alpha()
        self.graphics['Bomb'] = pygame.image.load(os.path.join('data', 'images', 'bomb.png')).convert_alpha()
        self.graphics['Explosion'] = pygame.image.load(os.path.join('data', 'images', 'explosion.png')).convert_alpha()
        self.graphics['Change gender male'] = pygame.image.load(os.path.join('data', 'images', 'gender_male.png')).convert_alpha()
        self.graphics['Change gender female'] = pygame.image.load(os.path.join('data', 'images', 'gender_female.png')).convert_alpha()
        self.graphics['Nuke'] = pygame.image.load(os.path.join('data', 'images', 'nuke.png')).convert_alpha()
        self.graphics['Radiation'] = pygame.image.load(os.path.join('data', 'images', 'radiation.png')).convert_alpha()
        self.graphics['Gas'] = pygame.image.load(os.path.join('data', 'images', 'gas.png')).convert_alpha()
        self.graphics['Gas source'] = pygame.image.load(os.path.join('data', 'images', 'gas_source.png')).convert_alpha()

    def initialize_sounds(self):
        """Load all sounds"""
        self.sounds['Nuke'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'nuke.wav'))
        self.sounds['Mate'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'mate.wav'))
        self.sounds['Explosion'] = pygame.mixer.Sound(os.path.join('data','sounds', 'explosion.wav'))
        self.sounds['Birth'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'birth.wav'))
        self.sounds['Change gender'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'gender.wav'))
        self.sounds['Poison'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'poison.wav'))
        self.sounds['Terminator'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'terminator.wav'))
        self.sounds['Gas source'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'gas.wav'))
        self.sounds['Ding'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'ding.wav'))
        self.set_volume()

    def set_volume(self):
        """Sets the volume based on the user's choice"""
        for sound in self.sounds:
            self.sounds[sound].set_volume(float(self.options['Sound volume']))

    def initialize_menu(self):
	"""Assign (x,y) values and set the initial amount to every item in the menu, then add to a spritegroup."""
        self.menu_sprites = pygame.sprite.LayeredDirty() 
        #If player is testing a map from the level editor, give 100 of each weapon
        if self.editor_map:
            amount = 100
        else:
            amount = 0
        self.menu_items['Stop sign'] = {'x': 700, 'y': 120, 'amount': amount} 
        self.menu_items['Poison'] = {'x': 700, 'y': 160, 'amount': amount}
        self.menu_items['Terminator'] = {'x': 700, 'y': 200, 'amount': amount}
        self.menu_items['Bomb'] = {'x': 700, 'y': 240, 'amount': amount}
        self.menu_items['Change gender male'] = {'x': 700, 'y': 280, 'amount': amount}
        self.menu_items['Change gender female'] = {'x': 700, 'y': 320, 'amount': amount}
        self.menu_items['Nuke'] = {'x': 700, 'y': 360, 'amount': amount}
        self.menu_items['Gas source'] = {'x': 700, 'y': 400, 'amount': amount}
        for name, coords in self.menu_items.iteritems():
            self.menu_sprites.add(Menu_items(self, name, coords['x'], coords['y'])) 

    def generate_weapons(self):
	"""Generate a random weapon every 2-5 seconds"""
        if pygame.time.get_ticks() - self.last_generated_weapon > random.randint(2000, 5000): 
            self.menu_items[random.choice(self.menu_items.keys())]['amount'] += 1
            self.last_generated_weapon = pygame.time.get_ticks()
            self.play_sound('Ding')

    def get_dirty_tiles(self, obj, x, y):
	"""Finds all the tiles that rats currently are occupying"""
        self.dirty_tiles.empty()
        if isinstance(obj, rat.Rat) and obj.direction: #Rats without a direction are stuck on a single tile. Terminator rats are also rat instances.
            if obj.direction == 1: #North
                current_x = x - (x % 32)
                current_y = y - (y % 32)
                next_x = x - (x % 32)
                next_y = y - (y % 32) + 32
            elif obj.direction == -1: #South
                current_x = x - (x % 32)
                current_y = y - (y % 32) + 32
                next_x = x - (x % 32)
                next_y = y - (y % 32)
            elif obj.direction == 2: #East
                current_x = x - (x % 32) + 32
                current_y = y - (y % 32)
                next_x = x - (x % 32)
                next_y = y - (y % 32)
            elif obj.direction == -2: #West
                current_x = x - (x % 32) 
                current_y = y - (y % 32)
                next_x = x - (x % 32) + 32
                next_y = y - (y % 32)
            tile1 = self.leveltest.tile_map[next_y / 32][next_x / 32]
            tile2 = self.leveltest.tile_map[current_y / 32][current_x / 32]
            if not self.dirty_tiles.has(tile1):
                self.dirty_tiles.add(tile1)
            if not self.dirty_tiles.has(tile2):
                self.dirty_tiles.add(tile2)
        elif isinstance(obj, weapons.Nuke): #Nuke requires a special case because the radiation sprite occupies nine tiles
            for tile_y in range(y - 32, y + 64, 32):
                for tile_x in range(x - 32, x + 64, 32):
                    tile = self.leveltest.tile_map[tile_y / 32][tile_x / 32]
                    if not self.dirty_tiles.has(tile):
                        self.dirty_tiles.add(tile)
        else: #For weapons and stationary rats, which never move
            x = x - (x % 32)
            y = y - (x % 32)
            tile = self.leveltest.tile_map[y / 32][x / 32]
            if not self.dirty_tiles.has(tile):
                self.dirty_tiles.add(tile)
        
    def update_sprites(self):
	"""Update each sprite, get dirty tiles and get population count"""
        self.population_count['M'] = 0 
        self.population_count['F'] = 0
        for sprite in self.male_rat_sprites:
            sprite.update()
            self.population_count['M'] += 1
            self.get_dirty_tiles(sprite, sprite.rect.x, sprite.rect.y)
        for sprite in self.female_rat_sprites:
            sprite.update()
            self.population_count['F'] += 1
            self.get_dirty_tiles(sprite, sprite.rect.x, sprite.rect.y)
        for sprite in self.child_rat_sprites:
            sprite.update()
            self.population_count[sprite.gender] += 1
            self.get_dirty_tiles(sprite, sprite.rect.x, sprite.rect.y)
        for sprite in self.weapon_sprites: 
            sprite.update() 
            self.get_dirty_tiles(sprite, sprite.rect.x, sprite.rect.y)
            if sprite.name == 'Bomb' and sprite.exploded: 
                self.play_sound('Explosion')
                explosion_rects = self.leveltest.find_lanes(sprite.rect) 
                for explosion_rect in explosion_rects:
                    self.weapon_sprites.add(weapons.Explosion(self, explosion_rect.x, explosion_rect.y)) 


    def draw_ui(self): 
	"""Draws the population counter graphics and weapon icons"""
        self.male_ui_rect.h = -self.population_count['M'] * 4 
        pygame.draw.rect(screen, blue, self.male_ui_rect) 
        self.female_ui_rect.h = -self.population_count['F'] * 4
        self.female_ui_rect.top = self.male_ui_rect.top + self.male_ui_rect.h 
        pygame.draw.rect(screen, red, self.female_ui_rect)
        pygame.draw.rect(screen, green, self.population_frame, 2) 
        for icon in self.menu_sprites: 
            screen.blit(icon.image, icon.rect)
        if self.active_weapon: 
            pygame.draw.rect(screen, red, self.active_rectangle, 2)


    def process_text(self): 
	"""Updates and draws the ingame text"""
        text_items = {
            'Population': {'text': 'Number of rats: {0}'.format(self.population_count['M'] + self.population_count['F']), 'x': 680, 'y': 20},
            'Male population': {'text': 'Male: {0}'.format(self.population_count['M']), 'x': 680, 'y': 40},
            'Female population': {'text': 'Female: {0}'.format(self.population_count['F']), 'x': 680, 'y': 60},
            'Score' : {'text' : 'Score: {0}'.format(self.score), 'x' : 680, 'y' : 80}}
        for name, info in self.menu_items.iteritems():
            text_items[name] = {'text': str(self.menu_items[name]['amount']), 'x': self.menu_items[name]['x'] + 40, 'y': self.menu_items[name]['y'] + 10}
        for text_item in text_items.values():
            render = self.menu_font.render(text_item['text'], True, white, black)
            render_rect = render.get_rect(x=text_item['x'], y=text_item['y'])
            screen.blit(render, render_rect)

    def handle_mouse(self, mouse_x, mouse_y): 
	"""Handles clicks on weapon icon or the map"""
        for icon in self.menu_sprites:
            if icon.rect.collidepoint(mouse_x, mouse_y): 
                if self.menu_items[icon.name]['amount'] > 0: 
                    self.active_weapon = icon.name
                    self.active_rectangle = pygame.Rect(icon.rect.x, icon.rect.y, 32, 32) 
        mouse_aligned_x = (mouse_x - mouse_x % tile.tile_size) 
        mouse_aligned_y = (mouse_y - mouse_y % tile.tile_size)
        if mouse_x <= self.board_width and mouse_y <= self.board_height and not self.leveltest.is_wall(mouse_x / tile.tile_size, mouse_y / tile.tile_size) and self.active_weapon: 
            self.place_weapon(mouse_aligned_x, mouse_aligned_y) 

    def place_weapon(self, mouse_x, mouse_y):
	"""Places the active weapon on the map"""
        if self.active_weapon == 'Stop sign':
            self.weapon_sprites.add(weapons.StopSign(self, mouse_x, mouse_y)) #Lägg till vapnet i spritegroupen för vapen
        elif self.active_weapon == 'Poison':
            self.weapon_sprites.add(weapons.Poison(self, mouse_x, mouse_y))
        elif self.active_weapon == 'Bomb':
            self.weapon_sprites.add(weapons.Bomb(self, mouse_x, mouse_y))
        elif self.active_weapon == 'Change gender male':
            self.weapon_sprites.add(weapons.ChangeGender(self, mouse_x, mouse_y, 'Change gender male'))
        elif self.active_weapon == 'Change gender female':
            self.weapon_sprites.add(weapons.ChangeGender(self, mouse_x, mouse_y, 'Change gender female'))
        elif self.active_weapon == 'Terminator':
            self.weapon_sprites.add(weapons.Terminator(self, self.leveltest, mouse_x, mouse_y))
        elif self.active_weapon == 'Nuke':
            self.weapon_sprites.add(weapons.Nuke(self, mouse_x, mouse_y))
            self.weapon_sprites.add(weapons.Radiation(self, mouse_x - 32, mouse_y - 32))
        elif self.active_weapon == 'Gas source':
            self.weapon_sprites.add(weapons.GasSource(self, self.leveltest, mouse_x, mouse_y))
        self.menu_items[self.active_weapon]['amount'] -= 1 #Minska hur många vapen av den sorten som finns vkar
        if self.menu_items[self.active_weapon]['amount'] == 0: #Om det var det sista vapnet, så finns inte längre något aktivt vapen
            self.active_weapon = None

    def play_sound(self, sound):
	"""Plays the selected sound"""
        self.sounds[sound].play()

    def handle_event(self, event):
	"""Handles all events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_mouse(event.pos[0], event.pos[1])
        if event.type == self.music_event:
            self.handle_music()

    def update(self):
        """Updates game logic"""
        clock.tick(60)
        self.generate_weapons()
        self.update_sprites()
        self.collisions()
        self.check_game_over()
        if self.win and not self.editor_map:
            self.level += 1
            if self.level <= self.num_levels:
                self.reset(self.level)
            else:
                self.game_over()
        elif self.win and self.editor_map:
            self.stack.pop()

    def draw(self):
        """Draw all graphics"""
        screen.fill(black, pygame.Rect(672, 0, 800 - 672, 672))
        self.draw_ui()
        #            game_rects = []
        #            game_rects.append(self.male_rat_sprites.draw(screen))
        #            game_rects.append(self.female_rat_sprites.draw(screen))
        #            game_rects.append(self.child_rat_sprites.draw(screen))
        #            game_rects.append(self.weapon_sprites.draw(screen))
        #            game_rects.append(self.tile_sprites.draw(screen))
        tile_rects = self.tile_sprites.draw(screen)
    #    dirty_rects = self.dirty_tiles.draw(screen)
        weapon_rects = self.weapon_sprites.draw(screen)
        male_rects = self.male_rat_sprites.draw(screen) #Räkna ut alla sprite-rektanglar
        female_rects = self.female_rat_sprites.draw(screen)
        child_rects = self.child_rat_sprites.draw(screen)


        menu_rects = self.menu_sprites.draw(screen)
        self.process_text() #Hantera all text
        #            pygame.display.update(male_rects)
        #            pygame.display.update(female_rects)
        #            pygame.display.update(child_rects)
        #            pygame.display.update(weapon_rects)
        #            pygame.display.update(menu_rects)
        ##
        #            pygame.display.update(self.active_rectangle)
        pygame.display.update()



    def game_over(self):
	"""Handles game over condition"""
        pygame.mixer.music.stop()
        self.stack.pop()
        self.stack.push(GameOverScreen(self.score, self.stack))

    def check_game_over(self): 
	"""Checks if population exceeds the limit (player lost) or if population is zero (player won)"""
        population = self.population_count['M'] + self.population_count['F']
        if population > 50:
            self.game_over()
        elif population <= 0:
            self.win = True

    def create_rat(self, x=0, y=0, set_gender=None, isAdult=False, direction=None, sterile = False): 
	"""Method for creating a new rat. Position, gender, age, direction and sterility can be set"""
        if not direction: 
            x = x - (x % 32)
            y = y - (y % 32)
        new_rat = rat.EnemyRat(self, self.leveltest, x, y, isAdult, gender=set_gender, direction=direction, sterile = sterile)
        if not new_rat.adult: 
            self.child_rat_sprites.add(new_rat) 
            self.play_sound('Birth')
        elif new_rat.gender == 'M':
            self.male_rat_sprites.add(new_rat)
        else:
            self.female_rat_sprites.add(new_rat)

    def collisions(self): 
	"""Handles all collisions"""
	#Checks mating collisions, males -> females
        mate_hit = pygame.sprite.groupcollide(self.female_rat_sprites, self.male_rat_sprites, False, False) 
        for female, males in mate_hit.iteritems():
            for male in males:
                if female in self.female_rat_sprites and male in self.male_rat_sprites:
                    if female.check_mate(male): 
                        self.play_sound('Mate')

	#Checks weapons -> males
        weapon_male_hit = pygame.sprite.groupcollide(self.weapon_sprites, self.male_rat_sprites, False, False)
        for weapon, males in weapon_male_hit.iteritems(): 
            for male in males:
                if weapon in self.weapon_sprites and male in self.male_rat_sprites:
                    weapon.handle_collision(male)

	#Checks weapons -> females
        weapon_female_hit = pygame.sprite.groupcollide(self.weapon_sprites, self.female_rat_sprites, False, False) 
        for weapon, females in weapon_female_hit.iteritems():
            for female in females:
                if weapon in self.weapon_sprites and female in self.female_rat_sprites:
                    weapon.handle_collision(female)

	#Checks weapons -> children
        weapon_child_hit = pygame.sprite.groupcollide(self.weapon_sprites, self.child_rat_sprites, False, False)
        for weapon, children in weapon_child_hit.iteritems():
            for child in children:
                if weapon in self.weapon_sprites and child in self.child_rat_sprites:
                    weapon.handle_collision(child)
                    
        #Checks weapons -> weapons
        weapon_weapon_hit = pygame.sprite.groupcollide(self.weapon_sprites, self.weapon_sprites, False, False) 
        for weapon1, weapons2 in weapon_weapon_hit.iteritems():
            for weapon2 in weapons2:
                if weapon1 is weapon2 or weapon1 not in self.weapon_sprites or weapon2 not in self.weapon_sprites: 
                    continue
                if isinstance(weapon1, weapons.Explosion) and not isinstance(weapon2, weapons.Explosion) and not isinstance(weapon2, weapons.GasSource): 
                    weapon1.handle_collision(weapon2)
                elif isinstance(weapon1, weapons.Weapons) and isinstance(weapon2, weapons.Terminator):
                    if isinstance(weapon1, weapons.ChangeGender): 
                        gender = 'M' if weapon1.name == 'Change gender male' else 'F'
                        self.sounds['Change gender'].play()
                        self.create_rat(weapon2.rect.x, weapon2.rect.y, isAdult=True, direction=weapon2.direction, set_gender=gender)
                        weapon2.delete()
                        weapon1.delete()
                    else:
                        weapon1.handle_collision(weapon2)

game = GameStateStack()
game.main()
pygame.quit()
