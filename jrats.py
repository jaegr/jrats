# -*- coding: utf-8 -*-
import pygame
import random
import os

import glob
import tile
import weapons
import level
import rat

#TODO       win-conditions
#TODO       egna vapen
#TODO       balancera svårighetsgrad
#TODO       svårighetsgrader (easy/normal/hard)?
#TODO       Font caching, dictionary?, rendera inte fonten varje tick
#TODO       Game states - main menu, game over screen, win screen.
#TODO       optimera kollisionsdetektering?
#TODO       powerups
#TODO       egen musik? glob.glob(os.path.join('data', 'sounds', 'music', '*')) ?
#TODO       ost?
#TODO       bättre lösning för att spara banor
#TODO       sommartileset
#TODO       http://archives.seul.org/pygame/users/Jul-2010/msg00063.html
#BUG        dubbla stoppskyltar - orsakas av att råttan kolliderar med fler en en stoppskylt
#BUG        leveleditor - placera väggar och väg

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
pygame.display.set_caption("j&R")
clock = pygame.time.Clock()

class MainMenu(object):
    def __init__(self):
        self.menu_font = pygame.font.Font(None, 40)
        #        self.help_item = {'text' : self.help_text, 'x' : 100, 'y': 100}
        self.menu_text = {'Play': {'text': 'Play game', 'x': 630, 'y': 300},
                          'Highscore': {'text': 'Highscore', 'x': 630, 'y': 350},
                          'Editor' : {'text': 'Level editor', 'x': 630, 'y': 400},
                          'Exit': {'text': 'Exit', 'x': 630, 'y': 450}}

        self.done = False
        self.image = pygame.image.load(os.path.join('data', 'images', 'main.png')).convert_alpha()
        self.rect = self.image.get_rect()
        self.initialize_text()
#        pygame.mixer.music.load(os.path.join('data', 'sounds', 'sarabande.ogg'))
#        pygame.mixer.music.set_volume(0.2)
#        pygame.mixer.music.play(-1)

    def initialize_text(self):
    #        render = self.help_font.render(self.help_text, True, black)
    #        render_rect = render.get_rect(x = self.help_item['x'], y = self.help_item['y'])
    #        self.help_item['render'] = render
    #        self.help_item['rect'] = render_rect
        for menu_item in self.menu_text.values():
            render = self.menu_font.render(menu_item['text'], True, white)
            render_rect = render.get_rect(x=menu_item['x'], y=menu_item['y'])
            menu_item['render'] = render
            menu_item['rect'] = render_rect
    #    HighScoreScreen()

    def main(self):
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse(event.pos[0], event.pos[1])
            screen.fill(black)
            screen.blit(self.image, self.rect)
            for menu_item in self.menu_text.values():
                screen.blit(menu_item['render'], menu_item['rect'])
                #      screen.blit(self.help_item['render'], self.help_item['rect'])
            pygame.display.flip()

    def handle_mouse(self, mouse_x, mouse_y):
        for menu_item in self.menu_text.values():
            rect = menu_item['rect']
            if rect.x <= mouse_x <= rect.x + rect.x and rect.y <= mouse_y <= rect.y + rect.h:
                if menu_item['text'] == 'Play game':
   #                 pygame.mixer.music.stop()
                    rats = Game()
                    rats.main_loop()
  #                  pygame.mixer.music.play(-1)
                elif menu_item['text'] == 'Level editor':
                    editor = LevelEditor()
                    editor.main()
                elif menu_item['text'] == 'Exit':
                    self.done = True


class HighScoreScreen(object):
#    try:
#        with open(os.path.join('data', 'highscore.txt')) as highscore_file:
#            pass
#    except IOError:
#        with open(os.path.join('data', 'highscore.txt')) as new_file:
#            for i in range(1,11):
#                new_file.write('{0}. Empty - 0 points')
    def __init__(self):
        with open(os.path.join('data', 'highscore.txt')) as hs_file:
            self.hs_txttable = [line.strip() for line in hs_file]
        self.hs_font = pygame.font.Font(None, 70)
        self.hs_font_properties = {}
        self.hs_font_items = {}
        self.main()

    def initialize_text(self):
        text_x = 170
        text_y = 20
        screen.fill(black)
        for n, line in enumerate(self.hs_txttable):
            render = self.hs_font.render(self.hs_txttable[n], True, white)
            rect = render.get_rect(x = text_x, y = text_y * (n + 1) * 3)
        #    print line, render, rect, self.hs_txttable[n]
            screen.blit(render, rect)
        pygame.display.flip()

    def main(self):
        while True:
            self.initialize_text()

class LevelEditor(object):
    def __init__(self):
        self.map = []
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
        for text_item in self.editor_text.values():
            render = self.editor_font.render(text_item['text'], True, white)
            rect = render.get_rect(x = text_item['x'], y = text_item['y'])
            text_item['render'] = render
            text_item['rect'] = rect

    def initialize_map(self):
        self.map = [['.' if x != 0 and y != 0 and x != 20 and y != 20 else '#' for x in range(21)] for y in range(21)]

    def save(self):
        save_file = open(os.path.join('data', 'temp_map.txt'), 'w+')
        for row in self.map:
            save_file.write(''.join(row) + '\n')
        save_file.close()


    def draw_map(self):
        x = 0
        y = 0
        for i, row in enumerate(self.map):
            for n, col in enumerate(self.map):
                color = light_gray if self.map[i][n] == '.' else dark_gray
                pygame.draw.rect(screen, color, pygame.Rect(x, y, self.tile_size, self.tile_size))
                x += self.tile_size
            y += self.tile_size
            x = 0

    def draw_text(self):
        for text_item in self.editor_text.values():
            screen.blit(text_item['render'], text_item['rect'])

    def handle_mouse(self, mouse_x, mouse_y):
        aligned_x = mouse_x / self.tile_size
        aligned_y = mouse_y / self.tile_size
        if aligned_x < 20 and aligned_y < 20 and aligned_x > 0 and aligned_y > 0:
            if not self.active_tile:
                self.active_tile = '.' if self.map[aligned_y][aligned_x] == '#' else '#'
            self.map[aligned_y][aligned_x] = self.active_tile
        for text_item in self.editor_text.values():
            rect = text_item['rect']
            if rect.x <= mouse_x <= rect.x + rect.w and rect.y <= mouse_y <= rect.y + rect.h:
                self.action(text_item['text'])

    def action(self, key_action):
        if key_action == 'Play':
            game = Game(self.map)
            game.main_loop()
        elif key_action == 'Save':
            self.save()
        elif key_action == 'Clear':
            self.initialize_map()
        elif key_action == 'Exit':
            self.done = True

    def main(self):
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True

                if event.type == pygame.MOUSEMOTION and event.buttons[0]:
                    self.motion = True
                    self.handle_mouse(event.pos[0], event.pos[1])
                elif self.motion:
                    self.active_tile = None
                    self.motion = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse(event.pos[0], event.pos[1])
            screen.fill(black)
            self.draw_map()
            self.draw_text()
            pygame.display.flip()


class Menu_items(pygame.sprite.DirtySprite): #Skapar bilderna i menyn
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


class Game(object):
    def __init__(self, editor_map = None):
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=4096) #Initierar ljuder
        self.graphics = {} #Kommer innehålla all grafik
        self.sounds = {}   #Och allt ljud
        self.initialize_graphics() #Metod för att ladda in all grafik
        self.initialize_sounds()   #Metod för att ladda in allt ljud
        self.editor_map = editor_map
        self.reset()               #reset innehåller alla som ska återställas vid omstart eller ny bana
  #      pygame.mixer.music.load(os.path.join('data', 'sounds', 'Goof2.ogg'))
  #      pygame.mixer.music.set_volume(0.2)
  #      pygame.mixer.music.play(-1)
        self.board_width = self.board_height = 20 * tile.tile_size #Brädet är 21 tiles högt och brett, och varje tile är 32 x 32 pixlar

    def reset(self, level=1):
        self.menu_items = {} #Ett dictionary som kommer innehålla information om vapenikonerna i menyn
        self.level = level   #Vilken nivå
        self.initialize_menu() #Initiera menyn genom att tilldela menu_items värden
        self.male_rat_sprites = pygame.sprite.LayeredDirty() #Skapa spritegroups (för dirtysprites) för de olika sprite:arna
        self.female_rat_sprites = pygame.sprite.LayeredDirty()
        self.child_rat_sprites = pygame.sprite.LayeredDirty()
        self.weapon_sprites = pygame.sprite.LayeredDirty()
        self.tile_sprites = pygame.sprite.LayeredDirty()
        self.dirty_tiles = pygame.sprite.LayeredDirty()
        self.score = 0
        self.done = False #Anger om spelet är slut
        self.num_levels = 0
        self.create_level() #Skapar banan
        self.initial_population()
        self.population_count = {'M': 0, 'F': 0}
        self.male_ui_rect = pygame.Rect(700, 650, 50, 0) #Initierar mätaren för manliga råttor
        self.female_ui_rect = pygame.Rect(700, 650, 50, 0) #och mätaren för kvinnliga råttorr
        self.population_frame = pygame.Rect(700, 650, 50, -200) #Ramen runt mätaren
        # font = pygame.font.match_font('arial')
        self.menu_font = pygame.font.Font(None, 18) #Initierar texten i menyn
        self.win = False
        self.active_rectangle = pygame.Rect(0, 0, 0, 0) #Rektangeln som ritas ut runt det aktiva vapnet
        self.lost = False
        self.active_weapon = None #Inget vapen är aktivt i början
        self.last_generated_weapon = pygame.time.get_ticks() #När ett vapen senast skapades
        self.generate_weapons() #Kör metoden för att generera vapen
        self.collision_time = pygame.time.get_ticks()

    def initial_population(self):
        for i in range(7):
            self.create_rat(init=True)

    def get_number_of_levels(self):
        self.num_levels = self.leveltest.number_of_levels()

    def create_level(self): #Skapa en instans av Level, ladda kartan, rita ut blommor
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
        self.tileset = self.leveltest.tile_set
        self.graphics['Path'] = [pygame.image.load(os.path.join('data', 'images', self.tileset, '{0}.png'.format(i))).convert_alpha() for i in range(15)]
        self.graphics['Wall'] = [pygame.image.load(tile_path) for tile_path in glob.glob(os.path.join('data', 'images', self.tileset, 'wall*.png'))]
        self.graphics['Decorations'] = [pygame.image.load(tile_path) for tile_path in glob.glob(os.path.join('data', 'images', self.tileset, 'decoration*.png'))]

    def initialize_graphics(self): #Ladda in all grafik
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

    def initialize_sounds(self): #ladda in allt ljud
        self.sounds['Nuke'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'nuke.wav'))
        self.sounds['Mate'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'mate.wav'))
        self.sounds['Explosion'] = pygame.mixer.Sound(os.path.join('data','sounds', 'explosion.wav'))
        self.sounds['Birth'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'birth.wav'))
        self.sounds['Change gender'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'gender.wav'))
        self.sounds['Poison'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'poison.wav'))
        self.sounds['Terminator'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'terminator.wav'))
        self.sounds['Gas source'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'gas.wav'))
        self.sounds['Ding'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'ding.wav'))

    def initialize_menu(self):
        self.menu_sprites = pygame.sprite.LayeredDirty() #Alla menysprites läggs in i en spritegroup
        self.menu_items['Stop sign'] = {'x': 700, 'y': 120, 'amount': 100} #Alla vapen i menyn får ett x och y-värde, och hur stort antal av det vapnet som användaren har
        self.menu_items['Poison'] = {'x': 700, 'y': 160, 'amount': 100}
        self.menu_items['Terminator'] = {'x': 700, 'y': 200, 'amount': 100}
        self.menu_items['Bomb'] = {'x': 700, 'y': 240, 'amount': 100}
        self.menu_items['Change gender male'] = {'x': 700, 'y': 280, 'amount': 100}
        self.menu_items['Change gender female'] = {'x': 700, 'y': 320, 'amount': 100}
        self.menu_items['Nuke'] = {'x': 700, 'y': 360, 'amount': 100}
        self.menu_items['Gas source'] = {'x': 700, 'y': 400, 'amount': 100}
        #     self.menu_items['Restart'] = { 'x' : 700, 'y' : 500, 'amount': 'Restart'}
        for name, coords in self.menu_items.iteritems():
            self.menu_sprites.add(Menu_items(self, name, coords['x'], coords['y'])) #Skapa sprites av alla vapen och lägg till i spritegroupen

    def generate_weapons(self):
        if pygame.time.get_ticks() - self.last_generated_weapon > random.randint(3000, 7000): #Mellan var 3:e och var 7:e sekunder, skapa ett slumpat vapen
            self.menu_items[random.choice(self.menu_items.keys())]['amount'] += 1
            self.last_generated_weapon = pygame.time.get_ticks()
            self.play_sound('Ding')

    def get_dirty_tiles(self, obj, x, y):
        self.dirty_tiles.empty()
        if isinstance(obj, rat.Rat) and obj.direction: #kolla direction utifall råttan skulle vara fast i en enskild tile
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
        elif isinstance(obj, weapons.Nuke):
            for tile_y in range(y - 32, y + 64, 32):
                for tile_x in range(x - 32, x + 64, 32):
                    tile = self.leveltest.tile_map[tile_y / 32][tile_x / 32]
                    if not self.dirty_tiles.has(tile):
                        self.dirty_tiles.add(tile)
        else:
            x = x - (x % 32)
            y = y - (x % 32)
            tile = self.leveltest.tile_map[y / 32][x / 32]
            if not self.dirty_tiles.has(tile):
                self.dirty_tiles.add(tile)
        

    def update_sprites(self):
        self.dirty_tiles.empty()
        self.population_count['M'] = 0 #Återställ räkningen av råttor
        self.population_count['F'] = 0
        for sprite in self.male_rat_sprites: #För alla råttor, kör deras update-metod och öka på räkningen
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
        for sprite in self.weapon_sprites: #För varje vapen
            sprite.update() #Kör deras update-metod
            self.get_dirty_tiles(sprite, sprite.rect.x, sprite.rect.y)
            if sprite.name == 'Bomb' and sprite.exploded: #Om vapnet är en bomb, och det har exploderat
                self.play_sound('Explosion')
                explosion_rects = self.leveltest.find_lanes(sprite.rect) #Hitta alla rutor som explosionen kan expandera till
                for explosion_rect in explosion_rects:
                    self.weapon_sprites.add(weapons.Explosion(self, explosion_rect.x, explosion_rect.y)) #Skapa explosionssprites på dessa rutor


    def draw_ui(self): #Ritar ut användarinterfacet
        self.male_ui_rect.h = -self.population_count['M'] * 5 #Höjden på mätaren som visar antal manliga råttor får höjden: antal manliga råttor * 5
        pygame.draw.rect(screen, blue, self.male_ui_rect) #Rita ut mätaren
        self.female_ui_rect.h = -self.population_count['F'] * 5
        self.female_ui_rect.top = self.male_ui_rect.top + self.male_ui_rect.h #Mätaren för kvinnliga råttor ritas ut ovanför den manliga
        pygame.draw.rect(screen, red, self.female_ui_rect)
        pygame.draw.rect(screen, green, self.population_frame, 2) #Rita ut ramen runt mätarna
        for icon in self.menu_sprites: #Rita ut alla ikoner i menyn
            screen.blit(icon.image, icon.rect)
        if self.active_weapon: #Rita ut en rektangel runt det aktiva vapnet i menyn
            pygame.draw.rect(screen, red, self.active_rectangle, 2)


    def process_text(self): #Hanterar all text
        text_items = {
            'Population': {'text': 'Number of rats: {0}'.format(self.population_count['M'] + self.population_count['F']), 'x': 680, 'y': 20},
            'Male population': {'text': 'Male: {0}'.format(self.population_count['M']), 'x': 680, 'y': 40},
            'Female population': {'text': 'Female: {0}'.format(self.population_count['F']), 'x': 680, 'y': 60},
            'Score' : {'text' : 'Score: {0}'.format(self.score), 'x' : 680, 'y' : 80}}
        for name, info in self.menu_items.iteritems():
            text_items[name] = {'text': str(self.menu_items[name]['amount']), 'x': self.menu_items[name]['x'] + 40, 'y': self.menu_items[name]['y'] + 10}
        for text_item in text_items.values():
            render = self.menu_font.render(text_item['text'], True, white)
            render_rect = render.get_rect(x=text_item['x'], y=text_item['y'])
            screen.blit(render, render_rect)

    def handle_mouse(self, mouse_x, mouse_y): #Hanterar musklick
        for icon in self.menu_sprites:
            if icon.rect.x <= mouse_x <= icon.rect.x + icon.rect.w and icon.rect.y <= mouse_y <= icon.rect.y + icon.rect.h: #Kollar om användaren klickat på en ikon
                if self.menu_items[icon.name]['amount'] > 0: #Om användaren har det vapnet
                    self.active_weapon = icon.name           #Sätt vapnet som aktivt
                    self.active_rectangle = pygame.Rect(icon.rect.x, icon.rect.y, 32, 32) #Och rita ut en rektangel runt vapnet
        mouse_aligned_x = (mouse_x - mouse_x % tile.tile_size) #Anpassa positionen så den hamnar mitt över en tile
        mouse_aligned_y = (mouse_y - mouse_y % tile.tile_size)
        if mouse_x <= self.board_width and mouse_y <= self.board_height and not self.leveltest.is_wall(mouse_x / tile.tile_size, mouse_y / tile.tile_size) and self.active_weapon: #Om musen är innanför spelplanen, och inte på en vägg, och det finns ett aktivt vapen
            self.place_weapon(mouse_aligned_x, mouse_aligned_y) #Placera vapnet på spelplanen

    def place_weapon(self, mouse_x, mouse_y): #Placera vapnet på spelplanen
        if self.active_weapon == 'Stop sign':
            self.weapon_sprites.add(weapons.StopSign(self, mouse_x, mouse_y)) #Lägg till vapnet i spritegroupen för vapen
        elif self.active_weapon == 'Poison':
            self.weapon_sprites.add(weapons.Poison(self, mouse_x, mouse_y))
        elif self.active_weapon == 'Bomb':
            self.weapon_sprites.add(weapons.Bomb(self, mouse_x, mouse_y))
        elif self.active_weapon == 'Change gender male':
            self.weapon_sprites.add(weapons.ChangeGenderMale(self, mouse_x, mouse_y))
        elif self.active_weapon == 'Change gender female':
            self.weapon_sprites.add(weapons.ChangeGenderFemale(self, mouse_x, mouse_y))
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
        pass
        #self.sounds[sound].play()

    def main_loop(self):
        while not self.done:
            for event in pygame.event.get():
                #print event
                if event.type == pygame.QUIT:
                    self.done = True
 #                   pygame.mixer.music.stop()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse(event.pos[0], event.pos[1])
            screen.fill(black, pygame.Rect(672, 0, 800 - 672, 672))
            clock.tick(60)
            self.generate_weapons()
            self.update_sprites()
            self.collisions()
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
            self.check_game_over()
            if self.win and not self.editor_map:
                self.done = True
                self.level += 1
                if not self.level > self.num_levels:
                    self.reset(self.level)
            elif self.win and self.editor_map:
                self.done = True

    def check_game_over(self): #testmetod
        population = self.population_count['M'] + self.population_count['F']
        if population > 1500:
            self.lost = True
        elif population <= 0:
            self.win = True

    def create_rat(self, x=0, y=0, init=False, set_gender=None, isAdult=False, direction=None, sterile = False): #Metod för att skapa nya råttor (lite rörig just nu)
        if init: #Om det är spelstart
            while self.leveltest.is_wall(x, y): #Så länge som startposition är en vägg
                x, y = random.randrange(21), random.randrange(21) #Slumpa fram nya index
            x *= tile.tile_size #Omvanlda koordinaterna från index i map-arrayen till koordinater
            y *= tile.tile_size
            isAdult = True #Alla startråttor ska vara vuxna
        if not direction: #Om råttan inte har en riktning, måste vi placera den rakt över en tile så att en riktning kan beräknas
            x = x - (x % 32)
            y = y - (y % 32)
        new_rat = rat.EnemyRat(self, self.leveltest, x, y, isAdult, gender=set_gender, direction=direction, sterile = sterile) #Skapa råttan
        if not new_rat.adult: #Om det är ett barn
            self.child_rat_sprites.add(new_rat) #Lägg till i gruppen för barnsprites
            self.play_sound('Birth')
        elif new_rat.gender == 'M':
            self.male_rat_sprites.add(new_rat)
        else:
            self.female_rat_sprites.add(new_rat)
       # print 'number of basic_rat:', len(self.male_rat_sprites) + len(self.female_rat_sprites) + len(self.child_rat_sprites)

    def collisions(self): #kollisionsdetektering
        if pygame.time.get_ticks() - self.collision_time > 50: #Ett test för att minska antal kollisionsdetekteringar. Hälften av spritegroupsen testas var 50 ms, och andra hälften nästa 50 ms
            self.collision_time = pygame.time.get_ticks()
            mate_hit = pygame.sprite.groupcollide(self.female_rat_sprites, self.male_rat_sprites, False, False) #Kolla om några manliga och kvinnliga råttor kolliderar
            for female, males in mate_hit.iteritems():
                for male in males:
                    if female in self.female_rat_sprites and male in self.male_rat_sprites:
                        female.check_mate(male) #Om de gör det, så kör metoden för att kolla om råttan ska bli gravid
            weapon_male_hit = pygame.sprite.groupcollide(self.weapon_sprites, self.male_rat_sprites, False, False)
            for weapon, males in weapon_male_hit.iteritems(): #Kolla om några manliga råttor kolliderar, och hantera kollisionen då
                for male in males:
                    if weapon in self.weapon_sprites and male in self.male_rat_sprites:
                        weapon.handle_collision(male)

        elif pygame.time.get_ticks() - self.collision_time > 25:
            weapon_female_hit = pygame.sprite.groupcollide(self.weapon_sprites, self.female_rat_sprites, False, False) #Kvinnliga -> vapen
            for weapon, females in weapon_female_hit.iteritems():
                for female in females:
                    if weapon in self.weapon_sprites and female in self.female_rat_sprites:
                        weapon.handle_collision(female)
            weapon_child_hit = pygame.sprite.groupcollide(self.weapon_sprites, self.child_rat_sprites, False, False) #Barn ->
            for weapon, children in weapon_child_hit.iteritems():
                for child in children:
                    if weapon in self.weapon_sprites and child in self.child_rat_sprites:
                        weapon.handle_collision(child)
            weapon_weapon_hit = pygame.sprite.groupcollide(self.weapon_sprites, self.weapon_sprites, False, False) #Vapen -> Vapen
            for weapon1, weapons in weapon_weapon_hit.iteritems():
                for weapon2 in weapons:
                    if weapon1 is weapon2 or weapon1 not in self.weapon_sprites or weapon2 not in self.weapon_sprites: #Om det är samma objekt, fortsätt
                        continue
                    if weapon1.name == 'Explosion' and weapon2.name != 'Explosion' and weapon2.name != 'Gas source': #Om första vapnet är en explosion, och andra vapnet inte är det, hantera det (ta bort andra vapnet)
                        weapon1.handle_collision(weapon2)
                    elif weapon1.type == 'Weapon' and weapon2.name == 'Terminator':
                        if weapon1.name == 'Change gender male' or weapon1.name == 'Change gender female': #Om ena vapnet är könsbyte och andra är terminator, gör om terminatorn till vanlig
                            gender = 'M' if weapon1.name == 'Change gender male' else 'F'
                            self.create_rat(weapon2.rect.x, weapon2.rect.y, isAdult=True, direction=weapon2.direction, set_gender=gender)
                            weapon2.delete()
                            weapon1.delete()
                        else:
                            weapon1.handle_collision(weapon2)


#import sys
#if __name__ == "__main__":
#
#    if "profile" in sys.argv:
#        import hotshot
#        import hotshot.stats
#        import tempfile
#        import os
#
#        profile_data_fname = tempfile.mktemp("prf")
#        try:
#            prof = hotshot.Profile(profile_data_fname)
#            prof.run('rats.main_loop()')
#            del prof
#            s = hotshot.stats.load(profile_data_fname)
#            s.strip_dirs()
#            print "cumulative\n\n"
#            s.sort_stats('cumulative').print_stats()
#            print "By time.\n\n"
#            s.sort_stats('time').print_stats()
#            del s
#        finally:
#            # clean up the temporary file name.
#            try:
#                os.remove(profile_data_fname)
#            except:
#                # may have trouble deleting ;)
#                pass
#    else:
#        try:
#
#
#
#        except:
#            traceback.print_exc(sys.stderr)

rats = MainMenu()
rats.main()
pygame.quit()
