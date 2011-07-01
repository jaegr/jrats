# -*- coding: utf-8 -*-
import pygame
import pygame.locals
import random
import ConfigParser
import os
from collections import deque
import glob

#TODO       win-conditions
#TODO       egna vapen?
#TODO       balancera svårighetsgrad
#TODO       svårighetsgrader (easy/normal/hard)?
#TODO       Font caching, dictionary?, rendera inte fonten varje tick
#TODO       Game states - main menu, game over screen, win screen. Win screen - try-except vid inladdning av bana, ingen sån bana - win screen?
#TODO       optimera kollisionsdetektering?
#TODO       powerups
#TODO       egen musik? glob.glob(os.path.join('data', 'sounds', 'music', '*')) ?
#TODO       ost?
#TODO       bättre lösning för att spara banor
#BUG        sterila barn är inte sterila när de blir vuxna
#BUG        dubbla stoppskyltar
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
tile_size = 32
screen = pygame.display.set_mode(size)
pygame.display.set_caption("j&R")
clock = pygame.time.Clock()

class Rat(pygame.sprite.DirtySprite): #Huvudklassen för alla råttor. Vanliga råttor och terminator-råttorna ärver den
    def __init__(self, direction=None):
        pygame.sprite.DirtySprite.__init__(self)
        self.directions = {'N': 1, 'S': -1, 'E': 2, 'W': -2} #Vilken riktning som råttorna ska gå. Heltal gör det enkelt att vända om (-self.direction)
        self.rotation = {1: 0, -1: 180, 2: 270, -2: 90}     #Hur många grader bilden på råttan ska roteras. Motsvarar samma heltal som i self.directions
        self.direction_timer = []
        if not direction:    #När barn blir vuxna, eller råttor byter kön så skapas en ny sprite, och den spriten ska ha samma riktning som den "gamla"
            available_directions = self.level_instance.get_directions(self.rect.x, self.rect.y)
            if not len(available_directions):
                self.direction = None
            else:
                self.direction = random.choice(available_directions) #Om de inte har någon gammal riktning (t.ex. råttorna som skapas vid spelstart) tilldelas en riktning
        else:
            self.direction = direction
        self.dirty = 2       #Råttorna ska alltid ritas om. DirtySprite på råttorna ger ingen direkt fördel, utan är mest för att stämma överens med vapen-sprite:arna

    def update(self):
        if not self.direction: #testkod för instängd råtta
            return
        if self.direction == self.directions['N']: #Flytta fram råttorna en pixel i dess riktning
            self.rect.y -= 1
        elif self.direction == self.directions['E']:
            self.rect.x += 1
        elif self.direction == self.directions['S']:
            self.rect.y += 1
        elif self.direction == self.directions['W']:
            self.rect.x -= 1
        if self.rect.x % tile_size == 0 and self.rect.y % tile_size == 0: #Om råttan är mitt på en tile måste vi kolla vilka riktningar som är tillgängliga
            available_paths = self.level_instance.get_directions(self.rect.x, self.rect.y) #Vi lägger in alla tillgängliga riktningar som get_directions() returnerar i en lista
            if -self.direction in available_paths:
                available_paths.remove(-self.direction) #Råttan ka inte gå tillbaka samma väg som den kom ifrån, så ta bort den från möjliga riktningar
            if not len(available_paths): #Men om det är en återvändsgränd (dvs längden på alla möjliga riktningar är 0)
                self.direction = -self.direction  #Gå tillbaka samma väg
            else:
                self.direction = random.choice(available_paths) #Annars välj en slumpvis väg
        self.image = pygame.transform.rotate(self.base_image, self.rotation[self.direction]) #Rotera bilden så den överensstämmer med riktningen
        for index, items in enumerate(self.direction_timer):
                if pygame.time.get_ticks() - items[1] > 500:
                    self.direction_timer.pop(index)

    def change_direction(self, weapon = None): #Sätt riktning till motsatt riktning
        if isinstance(weapon, StopSign) or isinstance(weapon, Bomb) and self.direction:
            for items in self.direction_timer:
                if weapon == items[0]:
                    return 0
            self.direction_timer.append([weapon, pygame.time.get_ticks()])
            self.direction = -self.direction
            return 1

    def delete(self): #Ta bort råttan från spritegroupen (och därmed från spelet)
        self.kill()


class EnemyRat(Rat):
    def __init__(self, game, level, x=32, y=32, isAdult=True, gender=None, direction=None): #Vanliga råttor
        self.level_instance = level #Ta emot levelinstansen (som krävs för att bestämma riktningar)
        self.game = game            #Gameklassens instans krävs bl.a. för att byta kön eftersom den skapar en ny råtta av motsatt kön
        if gender is None:          #Om råttans kön inte redan är bestäms, välj ett slumpvis
            self.gender = random.choice(['M', 'F'])
        else:
            self.gender = gender   #Annars sätt det som vi fick som inparameter
        self.adult = isAdult       #Är råttan vuxen?
        self.type = 'Rat'          #Type används bl.a. vid kollisionsdetekteringen
        if not self.adult:
            self.name = 'Baby rat' #Sätt rätt namn, vilket också används vid kollisionsdetekteringen
        elif self.gender == 'M':
            self.name = 'Male rat'
        else:
            self.name = 'Female rat'
        self.pregnant = False     #En nyskapad råtta är inte gravid
        self.base_image = self.game.graphics[self.name] #base_image är den bild som vi kommer utgå ifrån när bilden på råttan ska roteras. Den behövs eftersom rotationen är destruktiv
        self.image = self.base_image
        self.rect = self.base_image.get_rect() #Läs in bildens rektangel
        self.rect.x = x  #Sätt råttans position
        self.rect.y = y
        self.time_since_baby = 0  #Hur länge sen en gravid råtta födde barn
        self.babies_left = 0      #Hur många barn som ska födas
        self.sterile = False      #Råttorna blir sterila om de utsätts för strålning, men de föds aldrig som sterila
        self.birth = pygame.time.get_ticks()  #Hur länge sen de föddes. Barn blir vuxna efter 10 sekunder.
        Rat.__init__(self, direction) #Kör huvudklassens __init__
        print self.gender, self.adult, self.direction, self.pregnant, self.sterile, self.name, self.type

    def change_gender(self): #Skapar en ny råttsprite vid könbyte. 
        new_gender = 'M' if self.gender == 'F' else 'F'
        self.game.create_rat(x=self.rect.x, y=self.rect.y, set_gender=new_gender,
                             isAdult=self.adult, direction=self.direction)
        self.delete()


    def check_mate(self, other_rat): #Kollar om det är okej att para sig. Kollisionsdetekteringen ser till så att self är kvinnlig och other_rat är manlig
        if not self.pregnant and self.adult and other_rat.adult and not self.sterile and not other_rat.sterile: #Råttan får inte redan vara gravid, båda måste vara vuxna, och ingen får vara steril
            self.game.play_sound('Mate') #Spela parningsljudet
            self.handle_pregnant() #Kör funktionen för att hantera en gravid råtta

    def handle_pregnant(self):
        if not self.pregnant: #Första gången funktionen så sätts råttan som gravid
            self.pregnant = True
            self.time_since_baby = pygame.time.get_ticks() #En timer bestämmer när råttorna ska börja födas
            self.babies_left = 5 #Råttorna föder fem barn
        elif pygame.time.get_ticks() - self.time_since_baby > 4000 and self.pregnant: #Ett barn föds var fjärde sekund
            self.time_since_baby = pygame.time.get_ticks() #Återställ timern
            self.game.create_rat(x=self.rect.x, y=self.rect.y) #Skapa barnet på samma position som mamman
            self.babies_left -= 1 #Minska hur många barn som är kvar att föda
            if self.babies_left <= 0: #Om råttan har fött alla barn
                self.pregnant = False #Så är den inte gravid längre

    def set_sterile(self): #Gör råttan steril
        self.sterile = True

    def update(self):
        Rat.update(self) #Kör huvudklassens update-metod
        if self.gender == 'F' and self.pregnant: #Om råttan är kvinnlig och gravid, kör graviditetsmetoden
            self.handle_pregnant()

        if not self.adult: #Om det är ett barn, och de har gått mer än 10 sekunder sen födseln, skapa en ny, vuxen, råtta med rätt kön
            if pygame.time.get_ticks() - self.birth > 10000:
                self.game.create_rat(x=self.rect.x, y=self.rect.y, set_gender=self.gender, isAdult=True, direction=self.direction)
                self.delete()


class Tile(pygame.sprite.DirtySprite):
    def __init__(self, game, x, y, tile, tile_number):
        pygame.sprite.DirtySprite.__init__(self)
        self.dirty = 1
        self.game = game
        self.tile = tile
        self.tile_number = tile_number
        self.name = self.get_name_from_tile()
        self.x = x
        self.y = y
        if self.name == 'Path':
            self.image = self.game.graphics['Path'][self.tile_number]
        else:
            if random.randint(1, 100) < 95:
                self.image = random.choice(self.game.graphics['Wall'])
            else:
                self.image = random.choice(self.game.graphics['Decorations'])
        self.rect = self.image.get_rect()
        self.rect.x = self.x * tile_size
        self.rect.y = self.y * tile_size

    def get_name_from_tile(self):
        if self.tile == '#':
            return 'Wall'
        elif self.tile == '.':
            return 'Path'


class Level(object):
    def __init__(self, level, game, editor_map): #level är startnivån (dvs. 1)
        self.map = []
        self.editor_map = editor_map
        self.game = game
        self.level = level
        self.tile_set = ''
        self.directions = {'N': 1, 'S': -1, 'E': 2, 'W': -2}

    def load_map(self, filename=os.path.join('data', 'map.txt')):
        if not self.editor_map:
            parser = ConfigParser.ConfigParser() #ConfigParser gör det smidigt att läsa in banor från textfiler
            parser.read(filename) #Läs in map.txt
            self.tile_set = parser.get('level{0}'.format(self.level), 'tileset')
            for row in parser.get('level{0}'.format(self.level), 'map').split(): #Och läs in map under rubriken level{nivå}
                self.map.append(list(row)) #Raderna görs om till en lista och läggs till i self.map
        else:
            self.map = self.editor_map
            dir = os.path.join('data', 'images')
            print dir
            available_tilesets = []
            for name in os.listdir(dir):
                print os.path.isdir(name)
                if os.path.isdir(os.path.join(dir, name)):
                    available_tilesets.append(name)
            self.tile_set = random.choice(available_tilesets)


    def load_tile_map(self):
        self.tile_map = [[Tile(self.game, x, y, col, self.check_neighbors(x, y)) for x, col in enumerate(row)] for y, row in enumerate(self.map)]

    def get_directions(self, x, y):
        available_paths = []
        x = x / tile_size
        y = y / tile_size
        if not self.is_wall(x, y - 1) and y - 1 > 0: #Kollar om tilen rakt ovanför, till vänster, höger eller rakt nedan
            available_paths.append(self.directions['N'])                                                    # är en vägg. I sådana fall, lägg inte till den riktningen
        if not self.is_wall(x, y + 1) and y + 1 < 20: #i listan
            available_paths.append(self.directions['S'])
        if not self.is_wall(x + 1, y) and x + 1 < 20:
            available_paths.append(self.directions['E'])
        if not self.is_wall(x - 1, y) and x - 1 > 0:
            available_paths.append(self.directions['W'])
        return available_paths

    def find_lanes(self, rect): #Kollar vilka rader och kolumner som explosionen kan expandera i.
        tile_x = rect.x / tile_size #Bombens x och y-koordinater divideras med tile_size (32) för få rätt index i self.map
        tile_y = rect.y / tile_size
        available_lanes = [rect] #Den tile som bomben exploderade på läggs först till
        directions = {'Up': (0, 1), 'Right': (1, 0), 'Down': (0, -1), 'Left': (-1, 0)} #directions gör det lätt att öka indexet i self.map för att gå vidare till nästa kolumn eller rad
        for direction in directions.values(): #För varje riktning
            while True:
                tile_y += direction[1] #Gå vidare till nästa tile i den riktningen
                tile_x += direction[0]
                if not self.is_wall(tile_x, tile_y): #Om det inte är en vägg, lägg till tilen
                    available_lanes.append(pygame.Rect(tile_x * tile_size, tile_y * tile_size, rect.h, rect.w))
                else:
                    tile_x = rect.x / tile_size #Annars så kan explosionen inte expandera mer i den riktningen, så återställ index och hoppa ur while-loopen
                    tile_y = rect.y / tile_size
                    break
        return available_lanes

    def get_tile(self, x, y): #Returnerar typen av tile på positionen
        if 0 <= x <= 20 and 0 <= y <= 20:
            return self.map[y][x]

    def check_neighbors(self, x, y):
        if not self.is_wall(x, y):
            directions = {'N': (0, -1), 'E': (1, 0), 'W': (-1, 0), 'S': (0, 1)}
            available_dirs = []
            for dir in directions.keys():
                neigh_x = x + directions[dir][0]
                neigh_y = y + directions[dir][1]
                if not self.is_wall(neigh_x, neigh_y):
                    available_dirs.append(dir)
            if len(available_dirs) == 1:
                if 'S' in available_dirs:
                    return 0
                elif 'W' in available_dirs:
                    return 1
                elif 'N' in available_dirs:
                    return 2
                elif 'E' in available_dirs:
                    return 3
            elif len(available_dirs) == 2:
                if 'N' in available_dirs and 'S' in available_dirs:
                    return 4
                elif 'E' in available_dirs and 'W' in available_dirs:
                    return 5
                elif 'E' in available_dirs and 'S' in available_dirs:
                    return 6
                elif 'W' in available_dirs and 'S' in available_dirs:
                    return 7
                elif 'W' in available_dirs and 'N' in available_dirs:
                    return 8
                elif 'N' in available_dirs and 'E' in available_dirs:
                    return 9
            elif len(available_dirs) == 3:
                if 'E' in available_dirs and 'W' in available_dirs and 'S' in available_dirs:
                    return 10
                elif 'N' in available_dirs and 'W' in available_dirs and 'S' in available_dirs:
                    return 11
                elif 'E' in available_dirs and 'W' in available_dirs and 'N' in available_dirs:
                    return 12
                elif 'E' in available_dirs and 'S' in available_dirs and 'N' in available_dirs:
                    return 13
            else:
                return 14
        else:
            return None

    def is_wall(self, x, y): #Kollar om tilen är antingen är gräs eller blomma, dvs. en vägg
        if 0 <= x <= 20 and 0 <= y <= 20:
            if self.get_tile(x, y) == '#' or self.get_tile(x, y) == '*': return True
            else: return False


class Weapons(pygame.sprite.DirtySprite): #Huvudklassen för vapen
    def __init__(self, game, x, y, name): #Tar en game-instans, musens x och y-värden, samt namnet på vapnet
        pygame.sprite.DirtySprite.__init__(self)
        self.type = 'Weapon' #Typen sätts som vapen
        self.name = name     #Namnet sätts som vapennamnet
        self.game = game
        self.image = self.game.graphics[self.name] #Bilden på vapnet tas från gameinstansens graphics-dictionary
        self.rect = self.image.get_rect() #Läs av bildens rektangel
        self.rect.x = x #Och sätt x och y-värde
        self.rect.y = y
        self.dirty = 2  #Vapnena ska ritas om i varje frame (kan optimeras i framtiden)

    def handle_collision(self, obj): #Vissa vapen hanterar inte kollision med råttor, så de får en tom metod
        pass

    def delete(self): #Ta bort vapenet från spritegroupen
        self.kill()

    def update(self): #För de vapen som inte uppdateras i varje frame
        pass

    def play_sound(self, file=None): #Spela upp rätt vapenljud
        if not file:
            file = self.name
        self.game.play_sound(file)


class Nuke(Weapons): #Nuke avger strålning som gör råttor sterila
    def __init__(self, game, x, y):
        Weapons.__init__(self, game, x, y, 'Nuke') #Kör huvudklassens __init__
        self.activation_time = pygame.time.get_ticks()  #Vapnet ska försvinna efter 5 sekunder, så sätt starttiden
        self.play_sound() #Spela upp ljudet vid placering av vapnet

    def update(self):
        if pygame.time.get_ticks() - self.activation_time > 5000: #Efter 5 sekunder, ta bort vapnet
            self.delete()


class Radiation(Weapons): #Radiation är den strålning som Nuke avger
    def __init__(self, game, x, y):
        Weapons.__init__(self, game, x, y, 'Radiation')
        self.activation_time = pygame.time.get_ticks()
        self.blink_time = pygame.time.get_ticks() #Strålningen ska blinka, och blink_time hålla reda på om bilden ska visas eller är osynlig

    def handle_collision(self, rat): #Om råttan inte är en terminator-råtta, sätt den som steril
        if rat.name != 'Terminator':
            rat.set_sterile()

    def update(self):
        if pygame.time.get_ticks() - self.activation_time > 5000: #Tar bort efter 5 sekunder
            self.delete()
        else:
            if pygame.time.get_ticks() - self.blink_time > 50: #Bilden ska visas eller gömmas var 50 ms
                self.visible = 1 if self.visible == 0 else 0 #Visible är en funktion i DirtySprite som bestämmer om bilden ska vara synlig eller inte
                self.blink_time = pygame.time.get_ticks() #Återställ blinktiden


class GasSource(Weapons):
    def __init__(self, game, level, x, y):
        Weapons.__init__(self, game, x, y, 'Gas source')
        self.level = level
        self.gas_timer = pygame.time.get_ticks() #Kollar när ett nytt gasmoln ska skapas
        self.depth = 1 #Hur långt ifrån gaskällan vi är (t.ex. 2 * 32 pixlar)
        self.expand_directions = deque(['Up', 'Right', 'Down', 'Left'])
        self.start_x = x
        self.start_y = y
        self.index = 1
        self.initial_gas = True
        self.start_removing = False
        self.directions = {'Up': (0, 32), 'Right': (32, 0), 'Down': (0, -32), 'Left': (-32, 0)}
        self.gas_clouds = []
        self.play_sound()

    def add_gas(self):
        done = False
        if self.initial_gas:
            while not done:
                x = self.start_x + self.directions[self.expand_directions[0]][0]
                y = self.start_y + self.directions[self.expand_directions[0]][1]
                if not self.level.is_wall(x / tile_size, y / tile_size):
                    self.gas_clouds.append(Gas(self.game, x, y, self, self.level))
                    self.game.weapon_sprites.add(self.gas_clouds[-1])
                    done = True
                self.expand_directions.rotate(-1)
                if self.expand_directions[0] == 'Up':
                    self.initial_gas = False
                    if len(self.gas_clouds) == 0: #Om det inte finns utrymme att släppa ut gasen
                        self.delete()
                        return
        else:
            for cloud in self.gas_clouds:
                available_neighbor_tiles = cloud.check_neighbors()
                for cloud in self.gas_clouds:
                    if (cloud.rect.x, cloud.rect.y) in available_neighbor_tiles:
                        available_neighbor_tiles.remove((cloud.rect.x, cloud.rect.y))
                if (self.rect.x, self.rect.y) in available_neighbor_tiles:
                    available_neighbor_tiles.remove((self.rect.x, self.rect.y))
                if available_neighbor_tiles:
                    x, y = random.choice(available_neighbor_tiles)
                    self.gas_clouds.append(Gas(self.game, x, y, self, self.level))
                    self.game.weapon_sprites.add(self.gas_clouds[-1])
                    done = True
                    break
            else:
                self.start_removing = True

    def update(self):
        if len(self.gas_clouds) > 10:
            self.start_removing = True
        if pygame.time.get_ticks() - self.gas_timer > 100 and not self.start_removing:
            self.add_gas()
            self.gas_timer = pygame.time.get_ticks()
        elif self.start_removing:
            self.remove_gas()

    def remove_gas(self):
        if pygame.time.get_ticks() - self.gas_timer > 100:
            gas_cloud = random.choice(self.gas_clouds)
            gas_cloud.delete()
            self.gas_clouds.remove(gas_cloud)
            self.gas_timer = pygame.time.get_ticks()
        elif not len(self.gas_clouds):
            self.delete()

class Gas(Weapons): #Ej implementerat än
    def __init__(self, game, x, y, gas_source, level):
        Weapons.__init__(self, game, x, y, 'Gas')
        self.gas_source = gas_source
        self.level = level
        self.directions = {'Up': (0, 32), 'Right': (32, 0), 'Down': (0, -32), 'Left': (-32, 0)}

    def check_neighbors(self):
        available_neighbor_tiles = []
        for direction in self.directions.keys():
            x = self.rect.x + self.directions[direction][0]
            y = self.rect.y + self.directions[direction][1]
            if not self.level.is_wall(x / 32, y / 32):
                available_neighbor_tiles.append((x, y))
        return available_neighbor_tiles


    def handle_collision(self, rat):
        self.game.score += 1
        rat.delete()


class Terminator(Weapons, Rat): #Terminator-råttor ärver från både Weapons och Rat, för vi vill att de ska röra sig som råttor
    def __init__(self, game, level, x, y):
        Weapons.__init__(self, game, x, y, 'Terminator')
        self.level_instance = level #Råttklassen kräver en levelinstans
        self.base_image = self.image #Basbilden, som kommer att roteras
        Rat.__init__(self)  #Kör Ratklassens __init__
        self.kills_left = 5 #Hur många råttor den kan döda innan den dör själv
        self.dirty = 2

    def handle_collision(self, rat):
        if isinstance(rat, EnemyRat): #Om terminatorn kolliderar med en råtta, döda råttan
            self.kills_left -= 1
            self.game.score += 1
            rat.delete()
            self.play_sound()
            if self.kills_left <= 0: #
                self.delete()

    def update(self): #Kör Ratklassens update
        Rat.update(self)


class ChangeGenderMale(Weapons): #Byter kön på en råtta, och gör en terminator-råtta till en vanlig råtta
    def __init__(self, game, x, y):
        Weapons.__init__(self, game, x, y, 'Change gender male')

    def handle_collision(self, rat):
        if rat.type == 'Rat' and rat.gender == 'F': #Om den kolliderar med en rått-typ, kör råttans change gender-metod, och ta bort sig själv
            self.play_sound('Change gender')
            rat.change_gender()
            self.delete()


class ChangeGenderFemale(Weapons): #Byter kön på en råtta, och gör en terminator-råtta till en vanlig råtta
    def __init__(self, game, x, y):
        Weapons.__init__(self, game, x, y, 'Change gender female')

    def handle_collision(self, rat):
        if rat.type == 'Rat' and rat.gender == 'M': #Om den kolliderar med en rått-typ, kör råttans change gender-metod, och ta bort sig själv
            self.play_sound('Change gender')
            rat.change_gender()
            self.delete()


class Poison(Weapons): #Placeras ut på banan och vid kollision med en råtta så försvinner både råttan och giftet
    def __init__(self, game, x, y):
        Weapons.__init__(self, game, x, y, 'Poison')

    def handle_collision(self, rat):
        self.play_sound()
        if isinstance(rat, EnemyRat):
            self.game.score += 1
        rat.delete()
        self.delete()


class StopSign(Weapons): #Får en råtta att byta riktning
    def __init__(self, game, x, y):
        Weapons.__init__(self, game, x, y, 'Stop sign')
        self.hits_left = 5 #Efter 5 kollisioner tas stoppblocket bort

    def handle_collision(self, rat):
        if rat.change_direction(self): #Kör råttans change direction-metod
            self.hits_left -= 1
            if self.hits_left <= 0:
                self.delete()



class Bomb(Weapons): #En bomb exploderar efter 3 sekunder och skapar en explosion
    def __init__(self, game, x, y):
        Weapons.__init__(self, game, x, y, 'Bomb')
        self.start_countdown = pygame.time.get_ticks()
        self.countdown = 2
        self.exploded = False #Används i gameklassen för att kolla om bomben har exploderat. I så fall skapas explosionssprites

    def handle_collision(self, rat):
        rat.change_direction(self) #Råttan byter riktning vid kollision med bomben

    def update(self):
        if pygame.time.get_ticks() - self.start_countdown > 1000: #Varje sekunder räknas timern ner
            self.countdown -= 1
            self.start_countdown = pygame.time.get_ticks()
        if self.countdown <= 0:
            self.delete()
            self.exploded = True


class Explosion(Weapons):
    def __init__(self, game, x, y):
        Weapons.__init__(self, game, x, y, 'Explosion')
        self.explosion_time = pygame.time.get_ticks() #Hur länge explosionen ska ritas ut

    def update(self):
        if pygame.time.get_ticks() - self.explosion_time > 200: #Ta bort explosionen efter 200 ms
            self.delete()

    def handle_collision(self, obj):
        if isinstance(obj, EnemyRat):
            self.game.score += 1
        obj.delete() #Allt som kolliderar med explosionen ska tas bort (både råttor och vapen)


class MainMenu(object):
    def __init__(self):
        self.menu_font = pygame.font.Font(None, 40)
        #    self.help_font = pygame.font.Font(None, 15)
        #        self.help_text = '''Råttorna invaderar! Döda dem innan de tar över världen!\n\r
        #                            Stoppskylt - blockerar gångar. Försvinner efter fem träffar.\n\r
        #                            Råttgift - tillräckligt för att döda en råtta.\n\r
        #                            Robotråtta - dödar fem råttor innan den dör själv. Påverkas av vapen precis som vanliga råttor.\n\r
        #                            Bomb - sprängs efter fem sekunder i en stor explosion. Förstör allt i sin väg, inklusive vapen.\n\r
        #                            Könsbyte - byter kön på råttor, och förvandlar robotråttor till vanliga råttor.\n\r
        #                            Strålning - gör råttor inom dess radie sterila, så att de inte kan para sig.\n\r
        #                            Giftavfall - släpper ut giftig gas som dödar alla som inandas den.
        #                            '''
        #        self.help_item = {'text' : self.help_text, 'x' : 100, 'y': 100}
        self.menu_text = {'Play': {'text': 'Play game', 'x': 630, 'y': 300},
                          'Highscore': {'text': 'Highscore', 'x': 630, 'y': 350},
                          'Editor' : {'text': 'Level editor', 'x': 630, 'y': 400},
                          'Exit': {'text': 'Exit', 'x': 630, 'y': 450}}

        self.done = False
        self.image = pygame.image.load(os.path.join('data', 'images', 'main.png')).convert_alpha()
        self.rect = self.image.get_rect()
        self.initialize_text()

    def initialize_text(self):
    #        render = self.help_font.render(self.help_text, True, black)
    #        render_rect = render.get_rect(x = self.help_item['x'], y = self.help_item['y'])
    #        self.help_item['render'] = render
    #        self.help_item['rect'] = render_rect
        for menu_item in self.menu_text.values():
            render = self.menu_font.render(menu_item['text'], True, black)
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
                    rats = Game()
                    rats.main_loop()
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
        for key in self.editor_text:
            render = self.editor_font.render(self.editor_text[key]['text'], True, white)
            rect = render.get_rect(x = self.editor_text[key]['x'], y = self.editor_text[key]['y'])
            self.editor_text[key]['render'] = render
            self.editor_text[key]['rect'] = rect

    def initialize_map(self):
        self.map = [['.' if x != 0 and y != 0 and x != 20 and y != 20 else '#' for x in range(21)] for y in range(21)]

    def save(self):
        print 'abplb'
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
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse(event.pos[0], event.pos[1])
                if event.type == pygame.MOUSEMOTION and event.buttons[0]:
                    self.motion = True
                    self.handle_mouse(event.pos[0], event.pos[1])
                elif self.motion:
                    self.active_tile = None
                    self.motion = False
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
#        pygame.mixer.music.load(os.path.join('data', 'sounds', 'havanagila.mid'))
#        pygame.mixer.music.set_volume(0.2)
#        pygame.mixer.music.play(-1)
        self.board_width = self.board_height = 20 * tile_size #Brädet är 21 tiles högt och brett, och varje tile är 32 x 32 pixlar

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
        self.create_level() #Skapar banan
        self.initial_population()
        self.male_count = 0 #Antal manliga råttor
        self.female_count = 0 #Antal kvinnliga råttor
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

    def create_level(self): #Skapa en instans av Level, ladda kartan, rita ut blommor
        self.leveltest = Level(self.level, self, self.editor_map)
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
        try:
            self.sounds['Nuke'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'nuke.wav'))
            self.sounds['Mate'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'mate.wav'))
            self.sounds['Explosion'] = pygame.mixer.Sound(os.path.join('data','sounds', 'explosion.wav'))
            self.sounds['Birth'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'birth.wav'))
            self.sounds['Change gender'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'gender.wav'))
            self.sounds['Poison'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'poison.wav'))
            self.sounds['Terminator'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'terminator.wav'))
            self.sounds['Gas source'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'gas.wav'))
            self.sounds['Ding'] = pygame.mixer.Sound(os.path.join('data', 'sounds', 'ding.wav'))
        except pygame.error as e:
            print e
            #   quit()

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
        if isinstance(obj, Rat) and obj.direction: #kolla direction utifall råttan skulle vara fast i en enskild tile
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
        else:
            x = x - (x % 32)
            y = y - (x % 32)
            tile = self.leveltest.tile_map[y / 32][x / 32]
            if not self.dirty_tiles.has(tile):
                self.dirty_tiles.add(tile)
        

    def update_sprites(self):
        self.dirty_tiles.empty()
        self.male_count = 0 #Återställ räkningen av råttor
        self.female_count = 0
        for sprite in self.male_rat_sprites: #För alla råttor, kör deras update-metod och öka på räkningen
            sprite.update()
            self.male_count += 1
            self.get_dirty_tiles(sprite, sprite.rect.x, sprite.rect.y)
        for sprite in self.female_rat_sprites:
            sprite.update()
            self.female_count += 1
            self.get_dirty_tiles(sprite, sprite.rect.x, sprite.rect.y)
        for sprite in self.child_rat_sprites:
            sprite.update()
            if sprite.gender == 'M':
                self.male_count += 1
            else:
                self.female_count += 1
            self.get_dirty_tiles(sprite, sprite.rect.x, sprite.rect.y)
        for sprite in self.weapon_sprites: #För varje vapen
            sprite.update() #Kör deras update-metod
            self.get_dirty_tiles(sprite, sprite.rect.x, sprite.rect.y)
            if sprite.name == 'Bomb' and sprite.exploded: #Om vapnet är en bomb, och det har exploderat
                self.play_sound('Explosion')
                explosion_rects = self.leveltest.find_lanes(sprite.rect) #Hitta alla rutor som explosionen kan expandera till
                for explosion_rect in explosion_rects:
                    self.weapon_sprites.add(Explosion(self, explosion_rect.x, explosion_rect.y)) #Skapa explosionssprites på dessa rutor


    def draw_ui(self): #Ritar ut användarinterfacet
        self.male_ui_rect.h = -self.male_count * 5 #Höjden på mätaren som visar antal manliga råttor får höjden: antal manliga råttor * 5
        pygame.draw.rect(screen, blue, self.male_ui_rect) #Rita ut mätaren
        self.female_ui_rect.h = -self.female_count * 5
        self.female_ui_rect.top = self.male_ui_rect.top + self.male_ui_rect.h #Mätaren för kvinnliga råttor ritas ut ovanför den manliga
        pygame.draw.rect(screen, red, self.female_ui_rect)
        pygame.draw.rect(screen, green, self.population_frame, 2) #Rita ut ramen runt mätarna
        for icon in self.menu_sprites: #Rita ut alla ikoner i menyn
            screen.blit(icon.image, icon.rect)
        if self.active_weapon: #Rita ut en rektangel runt det aktiva vapnet i menyn
            pygame.draw.rect(screen, red, self.active_rectangle, 2)


    def process_text(self): #Hanterar all text
        text_items = {
            'Population': {'text': 'Number of rats: {0}'.format(self.male_count + self.female_count), 'x': 680, 'y': 20},
            'Male population': {'text': 'Male: {0}'.format(self.male_count), 'x': 680, 'y': 40},
            'Female population': {'text': 'Female: {0}'.format(self.female_count), 'x': 680, 'y': 60},
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
        mouse_aligned_x = (mouse_x - mouse_x % tile_size) #Anpassa positionen så den hamnar mitt över en tile
        mouse_aligned_y = (mouse_y - mouse_y % tile_size)
        if mouse_x <= self.board_width and mouse_y <= self.board_height and not self.leveltest.is_wall(mouse_x / tile_size, mouse_y / tile_size) and self.active_weapon: #Om musen är innanför spelplanen, och inte på en vägg, och det finns ett aktivt vapen
            self.place_weapon(mouse_aligned_x, mouse_aligned_y) #Placera vapnet på spelplanen

    def place_weapon(self, mouse_x, mouse_y): #Placera vapnet på spelplanen
        if self.active_weapon == 'Stop sign':
            self.weapon_sprites.add(StopSign(self, mouse_x, mouse_y)) #Lägg till vapnet i spritegroupen för vapen
        elif self.active_weapon == 'Poison':
            self.weapon_sprites.add(Poison(self, mouse_x, mouse_y))
        elif self.active_weapon == 'Bomb':
            self.weapon_sprites.add(Bomb(self, mouse_x, mouse_y))
        elif self.active_weapon == 'Change gender male':
            self.weapon_sprites.add(ChangeGenderMale(self, mouse_x, mouse_y))
        elif self.active_weapon == 'Change gender female':
            self.weapon_sprites.add(ChangeGenderFemale(self, mouse_x, mouse_y))
        elif self.active_weapon == 'Terminator':
            self.weapon_sprites.add(Terminator(self, self.leveltest, mouse_x, mouse_y))
        elif self.active_weapon == 'Nuke':
            self.weapon_sprites.add(Nuke(self, mouse_x, mouse_y))
            self.weapon_sprites.add(Radiation(self, mouse_x - 32, mouse_y - 32))
        elif self.active_weapon == 'Gas source':
            self.weapon_sprites.add(GasSource(self, self.leveltest, mouse_x, mouse_y))
        self.menu_items[self.active_weapon]['amount'] -= 1 #Minska hur många vapen av den sorten som finns vkar
        if self.menu_items[self.active_weapon]['amount'] == 0: #Om det var det sista vapnet, så finns inte längre något aktivt vapen
            self.active_weapon = None

    def play_sound(self, sound):
        self.sounds[sound].play()

    def main_loop(self):
        while not self.done:
            for event in pygame.event.get():
                #print event
                if event.type == pygame.QUIT:
                    self.done = True
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
         #   dirty_rects = self.dirty_tiles.draw(screen)
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
                self.reset(self.level)
            elif self.win and self.editor_map:
                self.done = True

    def check_game_over(self): #testmetod
        population = self.male_count + self.female_count
        if population > 1500:
            self.lost = True
        elif population <= 0:
            self.win = True

    def create_rat(self, x=0, y=0, init=False, set_gender=None, isAdult=False, direction=None): #Metod för att skapa nya råttor (lite rörig just nu)
        if init: #Om det är spelstart
            while self.leveltest.is_wall(x, y): #Så länge som startposition är en vägg
                x, y = random.randrange(21), random.randrange(21) #Slumpa fram nya index
            x *= tile_size #Omvanlda koordinaterna från index i map-arrayen till koordinater
            y *= tile_size
            isAdult = True #Alla startråttor ska vara vuxna
        if not direction: #Om råttan inte har en riktning, måste vi placera den rakt över en tile så att en riktning kan beräknas
            x = x - (x % 32)
            y = y - (y % 32)
        rat = EnemyRat(self, self.leveltest, x, y, isAdult, gender=set_gender, direction=direction) #Skapa råttan
        if not rat.adult: #Om det är ett barn
            self.child_rat_sprites.add(rat) #Lägg till i gruppen för barnsprites
            self.play_sound('Birth')
        elif rat.gender == 'M':
            self.male_rat_sprites.add(rat)
        else:
            self.female_rat_sprites.add(rat)
        print 'number of basic_rat:', len(self.male_rat_sprites) + len(self.female_rat_sprites) + len(self.child_rat_sprites)

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
