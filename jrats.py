# -*- coding: utf-8 -*-
import pygame
import pygame.locals
import random
import ConfigParser
import os
from collections import deque

#TODO       egna sprites
#TODO       win-conditions
#TODO       egna vapen?
#TODO       balancera svårighetsgrad
#TODO       svårighetsgrader (easy/normal/hard)?
#TODO       större bana (öka tiles)
#TODO       dynamisk fönsterstorlek?
#TODO       Font caching, dictionary?, rendera inte fonten varje tick
#TODO       Fler tiles, slumpmässigt? Variera gräst och path-tiles?
#TODO       Game states - main menu, game over screen, win screen. Win screen - try-except vid inladdning av bana, ingen sån bana - win screen?
#BUG        kollision vid placering ovanpå råttor
black    = (   0,   0,   0)
white    = ( 255, 255, 255)
green    = (   0, 255,   0)
red      = ( 255,   0,   0)
blue     = (   0,   0, 255)
yellow   = ( 255, 255,   0)

pygame.init()
pygame.font.init() #initierar textutskrift
size=[800,672]
tile_size = 32
screen=pygame.display.set_mode(size)
pygame.display.set_caption("j&R")
clock=pygame.time.Clock()

class Rat(pygame.sprite.DirtySprite): #Huvudklassen för alla råttor. Vanliga råttor och terminator-råttorna ärver den
    def __init__(self, direction = None):
        pygame.sprite.DirtySprite.__init__(self)
        self.directions = {'N': 1, 'S' : -1, 'E' : 2, 'W' : -2} #Vilken riktning som råttorna ska gå. Heltal gör det enkelt att vända om (-self.direction)
        self.rotation = {1 : 0, -1 : 180, 2 : 270, -2 : 90}     #Hur många grader bilden på råttan ska roteras. Motsvarar samma heltal som i self.directions
        if not direction:    #När barn blir vuxna, eller råttor byter kön så skapas en ny sprite, och den spriten ska ha samma riktning som den "gamla"
            self.direction = random.choice(self.get_directions()) #Om de inte har någon gammal riktning (t.ex. råttorna som skapas vid spelstart) tilldelas en riktning
        else:
            self.direction = direction
        self.dirty = 2       #Råttorna ska alltid ritas om. DirtySprite på råttorna ger ingen direkt fördel, utan är mest för att stämma överens med vapen-sprite:arna
        
    def update(self):
        if self.direction == self.directions['N']: #Flytta fram råttorna en pixel i dess riktning
            self.rect.y -= 1
        elif self.direction == self.directions['E']:
            self.rect.x += 1
        elif self.direction == self.directions['S']:
            self.rect.y += 1
        elif self.direction == self.directions['W']:
            self.rect.x -= 1
        if self.rect.x % tile_size == 0 and self.rect.y % tile_size == 0: #Om råttan är mitt på en tile måste vi kolla vilka riktningar som är tillgängliga
            available_paths = self.get_directions() #Vi lägger in alla tillgängliga riktningar som get_directions() returnerar i en lista
            if -self.direction in available_paths:  
                available_paths.remove(-self.direction) #Råttan ka inte gå tillbaka samma väg som den kom ifrån, så ta bort den från möjliga riktningar
            if not len(available_paths): #Men om det är en återvändsgränd (dvs längden på alla möjliga riktningar är 0)
                self.direction = -self.direction  #Gå tillbaka samma väg
            else:
                self.direction = random.choice(available_paths) #Annars välj en slumpvis väg
        self.image = pygame.transform.rotate(self.base_image, self.rotation[self.direction]) #Rotera bilden så den överensstämmer med riktningen

    def get_directions(self): #Kollar möjliga riktningar
        available_paths = []
        if not self.level_instance.is_wall(self.rect.x / tile_size, (self.rect.y - tile_size) / tile_size): #Kollar om tilen rakt ovanför, till vänster, höger eller rakt nedan
            available_paths.append(self.directions['N'])                                                    # är en vägg. I sådana fall, lägg inte till den riktningen 
        if not self.level_instance.is_wall(self.rect.x / tile_size, (self.rect.y + tile_size) / tile_size): #i listan
            available_paths.append(self.directions['S'])
        if not self.level_instance.is_wall((self.rect.x + tile_size)/ tile_size, self.rect.y / tile_size):
            available_paths.append(self.directions['E'])
        if not self.level_instance.is_wall((self.rect.x - tile_size)/ tile_size, self.rect.y / tile_size):
            available_paths.append(self.directions['W'])
        return available_paths
        
    def change_direction(self): #Sätt riktning till motsatt riktning
        self.direction = -self.direction

    def delete(self): #Ta bort råttan från spritegroupen (och därmed från spelet)
        self.kill()

class basic_rat(Rat):
    def __init__(self, game, level, x = 32, y = 32, isAdult = True, gender = None, direction = None): #Vanliga råttor
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
        self.game.create_rat(x = self.rect.x, y = self.rect.y, set_gender = new_gender, isAdult = self.adult, direction = self.direction)
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
            print 'pregnant!'
        elif pygame.time.get_ticks() - self.time_since_baby > 4000 and self.pregnant: #Ett barn föds var fjärde sekund
            print 'baby born! babies left:', self.babies_left
            self.time_since_baby = pygame.time.get_ticks() #Återställ timern
            self.game.create_rat(x = self.rect.x, y = self.rect.y) #Skapa barnet på samma position som mamman
            self.babies_left -= 1 #Minska hur många barn som är kvar att föda
            if self.babies_left <= 0: #Om råttan har fött alla barn
                print 'no more babies'
                self.pregnant = False #Så är den inte gravid längre

    def set_sterile(self): #Gör råttan steril
        self.sterile = True

    def update(self):
        Rat.update(self) #Kör huvudklassens update-metod
        if self.gender == 'F' and self.pregnant: #Om råttan är kvinnlig och gravid, kör graviditetsmetoden
            self.handle_pregnant()

        if not self.adult: #Om det är ett barn, och de har gått mer än 10 sekunder sen födseln, skapa en ny, vuxen, råtta med rätt kön
            if pygame.time.get_ticks() - self.birth > 10000:
                self.game.create_rat(x = self.rect.x, y = self.rect.y, set_gender = self.gender, isAdult = True, direction = self.direction)
                self.delete()

class Tile(pygame.sprite.DirtySprite):
    def __init__(self, game, x, y, tile, tile_number):
        pygame.sprite.DirtySprite.__init__(self)
        self.dirty = 2
        self.game = game
        self.tile = tile
        self.tile_number = tile_number
        self.name = self.get_name_from_tile()
        self.x = x
        self.y = y
        if self.name == 'Path':
            self.image = self.game.graphics[self.name][self.tile_number]
        else:
            if random.randint(1,100) < 95:
                self.image = random.choice(self.game.graphics[self.name])
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
    def __init__(self, level, game): #level är startnivån (dvs. 1)
        self.map = []
        self.game = game
        self.level = level

    def load_map(self, filename = os.path.join('data', 'map.txt')):
        parser = ConfigParser.ConfigParser() #ConfigParser gör det smidigt att läsa in banor från textfiler
        parser.read(filename) #Läs in map.txt
        for row in parser.get('level{0}'.format(self.level), 'map').split(): #Och läs in map under rubriken level{nivå}
            self.map.append(list(row)) #Raderna görs om till en lista och läggs till i self.map

    def load_tile_map(self):
        self.tile_map = [[Tile(self.game, x, y, col, self.check_neighbors(x, y)) for x, col in enumerate(row)] for y, row in enumerate(self.map)]
        
    def find_lanes(self, rect): #Kollar vilka rader och kolumner som explosionen kan expandera i.
        tile_x = rect.x / tile_size #Bombens x och y-koordinater divideras med tile_size (32) för få rätt index i self.map
        tile_y = rect.y / tile_size
        available_lanes = [rect] #Den tile som bomben exploderade på läggs först till
        directions = {'Up' : (0, 1), 'Right' : (1, 0), 'Down' : (0, -1), 'Left' : (-1 , 0)} #directions gör det lätt att öka indexet i self.map för att gå vidare till nästa kolumn eller rad
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

    def set_tile(self, x, y, tile):
        if 0 <= x <= 20 and 0 <= y <= 20:
            self.map[y][x] = tile

    def check_neighbors(self, x, y):
        if not self.is_wall(x, y):
            directions = {'N' : (0, -1), 'E' : (1, 0), 'W' : (-1, 0), 'S' : (0, 1)}
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

    def play_sound(self, file = None): #Spela upp rätt vapenljud
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

class Gas_source(Weapons):
    def __init__(self, game, level, x, y):
        Weapons.__init__(self, game, x, y, 'Gas source')
        self.level = level
        self.gas_timer = pygame.time.get_ticks() #Kollar när ett nytt gasmoln ska skapas
        self.depth = 1 #Hur långt ifrån gaskällan vi är (t.ex. 2 * 32 pixlar)
        #self.expand_directions = deque(['Up', 'Right', 'Down', 'Left', 'Up Left', 'Up Right', 'Down Right', 'Down Left'])
        self.expand_directions = deque(['Up', 'Right', 'Down', 'Left'])
        print self.expand_directions
        self.start_x = x
        self.start_y = y
        self.index = 1
        self.initial_gas = True
        self.start_removing = False
        self.basic_directions = {'Up' : (0, 32), 'Right' : (32, 0), 'Down' : (0, -32), 'Left' : (-32 , 0)}
        self.directions = {'Up' : (0, 32), 'Right' : (32, 0), 'Down' : (0, -32), 'Left' : (-32 , 0), 'Up Right' : (32, 32), 'Up Left' : (-32, 32), 'Down Right' : (32, -32), 'Down Left' : (-32, -32)}
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

    def update(self):
        if len(self.gas_clouds) > 10:
            self.start_removing = True
        elif len(self.gas_clouds) == 0 and self.start_removing:
            self.delete()
        if pygame.time.get_ticks() - self.gas_timer > 100 and not self.start_removing:
            self.add_gas()
            self.gas_timer = pygame.time.get_ticks()
        elif self.start_removing and pygame.time.get_ticks() - self.gas_timer > 100:
            gas_cloud = random.choice(self.gas_clouds)
            gas_cloud.delete()
            self.gas_clouds.remove(gas_cloud)
            self.gas_timer = pygame.time.get_ticks()

class Gas(Weapons): #Ej implementerat än
    def __init__(self, game, x, y, gas_source, level):
        Weapons.__init__(self, game, x, y, 'Gas')
        self.gas_source = gas_source
        self.level = level
        self.directions = {'Up' : (0, 32), 'Right' : (32, 0), 'Down' : (0, -32), 'Left' : (-32 , 0)}

    def check_neighbors(self):
        available_neighbor_tiles = []
        for direction in self.directions.keys():
            x = self.rect.x + self.directions[direction][0]
            y = self.rect.y + self.directions[direction][1]
            if not self.level.is_wall(x / 32, y / 32):
                available_neighbor_tiles.append((x, y))
        return available_neighbor_tiles


    def handle_collision(self, rat):
        rat.delete()
        
class Terminator(Weapons, Rat): #Terminator-råttor ärver från både Weapons och Rat, för vi vill att de ska röra sig som råttor
    def __init__(self, game, level, x, y):
        Weapons.__init__(self, game, x, y, 'Terminator')
        self.level_instance = level #Råttklassen kräver en levelinstans
        self.base_image = self.image #Basbilden, som kommer att roteras
        Rat.__init__(self)   #Kör Ratklassens __init__
        self.kills_left = 5 #Hur många råttor den kan döda innan den dör själv
        self.dirty = 2
        
    def handle_collision(self, rat):
        if rat.type == 'Rat': #Om terminatorn kolliderar med en råtta, döda råttan
            self.kills_left -= 1
            rat.delete()
            self.play_sound()
            if self.kills_left <= 0: #
                self.delete()
            
    def update(self): #Kör Ratklassens update
        Rat.update(self)

class Change_gender_male(Weapons): #Byter kön på en råtta, och gör en terminator-råtta till en vanlig råtta
    def __init__(self, game, x, y):
        Weapons.__init__(self, game, x, y, 'Change gender male')
        
    def handle_collision(self, rat):
        if rat.type == 'Rat' and rat.gender == 'F': #Om den kolliderar med en rått-typ, kör råttans change gender-metod, och ta bort sig själv
            self.play_sound('Change gender')
            rat.change_gender()
            self.delete()

class Change_gender_female(Weapons): #Byter kön på en råtta, och gör en terminator-råtta till en vanlig råtta
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
        rat.delete()
        self.play_sound()
        self.delete()

class Stop_sign(Weapons): #Får en råtta att byta riktning
    def __init__(self, game, x, y):
        Weapons.__init__(self, game, x, y, 'Stop sign')
        self.hits_left = 5 #Efter 5 kollisioner tas stoppblocket bort

    def handle_collision(self, rat):
        self.hits_left -= 1 
        if self.hits_left <= 0:
            self.delete()
        rat.change_direction() #Kör råttans change direction-metod

class Bomb(Weapons): #En bomb exploderar efter 3 sekunder och skapar en explosion
    def __init__(self, game, x, y):
        Weapons.__init__(self, game, x, y, 'Bomb')
        self.start_countdown = pygame.time.get_ticks()
        self.countdown = 2
        self.exploded = False #Används i gameklassen för att kolla om bomben har exploderat. I så fall skapas explosionssprites

    def handle_collision(self, rat):
        rat.change_direction() #Råttan byter riktning vid kollision med bomben

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
        obj.delete() #Allt som kolliderar med explosionen ska tas bort (både råttor och vapen)

class main_menu(object):
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
        self.menu_text = {'Play' : {'text' : 'Play game', 'x' : 600, 'y' : 300},
                          'Highscore' : {'text' : 'Highscore', 'x' : 600, 'y' : 350},
                          'Exit' : {'text' : 'Exit', 'x' : 600, 'y' : 400}}

        self.done = False
        self.image = pygame.image.load(os.path.join('data','main.png')).convert_alpha()
        self.rect = self.image.get_rect()
        self.initialize_text()

    def initialize_text(self):
#        render = self.help_font.render(self.help_text, True, black)
#        render_rect = render.get_rect(x = self.help_item['x'], y = self.help_item['y'])
#        self.help_item['render'] = render
#        self.help_item['rect'] = render_rect
        for menu_item in self.menu_text.values():
            render = self.menu_font.render(menu_item['text'], True, black)
            render_rect = render.get_rect(x = menu_item['x'], y = menu_item['y'])
            menu_item['render'] = render
            menu_item['rect'] = render_rect

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
            if menu_item['rect'].x <= mouse_x <= menu_item['rect'].x + menu_item['rect'].x and menu_item['rect'].y <= mouse_y <= menu_item['rect'].y + menu_item['rect'].h:
                print menu_item['text']
                if menu_item['text'] == 'Play game':
                    rats = Game()
                    rats.main_loop()
                elif menu_item['text'] == 'Exit':
                    self.done = True

class highscore_screen(object):
    pass

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
    def __init__(self):
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=4096) #Initierar ljuder
        self.graphics = {} #Kommer innehålla all grafik
        self.sounds = {}   #Och allt ljud
        self.initialize_graphics() #Metod för att ladda in all grafik
        self.initialize_sounds()   #Metod för att ladda in allt ljud
        self.reset()               #reset innehåller alla som ska återställas vid omstart eller ny bana
       # pygame.mixer.music.load('Beetlejuice.mid')
       # pygame.mixer.music.set_volume(0.2)
       # pygame.mixer.music.play(-1)
        self.board_width = self.board_height = 20 * tile_size #Brädet är 21 tiles högt och brett, och varje tile är 32 x 32 pixlar
        
    def reset(self, level = 1):
        self.menu_items = {} #Ett dictionary som kommer innehålla information om vapenikonerna i menyn
        self.level = level   #Vilken nivå 
        self.initialize_menu() #Initiera menyn genom att tilldela menu_items värden
        self.male_rat_sprites = pygame.sprite.LayeredDirty() #Skapa spritegroups (för dirtysprites) för de olika sprite:arna
        self.female_rat_sprites = pygame.sprite.LayeredDirty()
        self.child_rat_sprites = pygame.sprite.LayeredDirty()
        self.weapon_sprites = pygame.sprite.LayeredDirty()
        self.tile_sprites = pygame.sprite.LayeredDirty()
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
#        self.gameover_font = pygame.font.Font(None, 200)
        self.win = False 
        self.active_rectangle = pygame.Rect(0, 0, 0 ,0) #Rektangeln som ritas ut runt det aktiva vapnet
        self.lost = False
        self.active_weapon = None #Inget vapen är aktivt i början
        self.last_generated_weapon = pygame.time.get_ticks() #När ett vapen senast skapades
        self.generate_weapons() #Kör metoden för att generera vapen
        self.collision_time = pygame.time.get_ticks() 

    def initial_population(self):
        for i in range(7):
            self.create_rat(init = True)

    def create_level(self): #Skapa en instans av Level, ladda kartan, rita ut blommor
        self.leveltest = Level(self.level, self)
        self.leveltest.load_map()
        self.leveltest.load_tile_map()
        for row in self.leveltest.tile_map:
            for col in row:
                self.tile_sprites.add(col)
        print self.tile_sprites
        for row in self.leveltest.map:
            print ''.join(row)

    def initialize_graphics(self): #Ladda in all grafik
        self.graphics['Stop sign'] = pygame.image.load(os.path.join('data','stop.png')).convert_alpha()
        self.graphics['Poison'] = pygame.image.load(os.path.join('data', 'poison.png')).convert_alpha()
        self.graphics['Male rat'] = pygame.image.load(os.path.join('data', 'male.png')).convert_alpha()
        self.graphics['Female rat'] = pygame.image.load(os.path.join('data', 'female.png')).convert_alpha()
        self.graphics['Baby rat'] = pygame.image.load(os.path.join('data', 'baby_rat.png')).convert_alpha()
        self.graphics['Terminator'] = pygame.image.load(os.path.join('data', 'terminator.png')).convert_alpha()
        self.graphics['Bomb'] = pygame.image.load(os.path.join('data', 'bomb.png')).convert_alpha()
        self.graphics['Explosion'] = pygame.image.load(os.path.join('data', 'explosion.png')).convert_alpha()
        self.graphics['Change gender male'] = pygame.image.load(os.path.join('data', 'gender_male.png')).convert_alpha()
        self.graphics['Change gender female'] = pygame.image.load(os.path.join('data', 'gender_female.png')).convert_alpha()
        self.graphics['Nuke'] = pygame.image.load(os.path.join('data', 'nuke.png')).convert_alpha()
        self.graphics['Radiation'] = pygame.image.load(os.path.join('data', 'radiation.png')).convert_alpha()
        self.graphics['Gas'] = pygame.image.load(os.path.join('data', 'gas.png')).convert_alpha()
        self.graphics['Gas source'] = pygame.image.load(os.path.join('data', 'gas_source.png')).convert_alpha()
        self.graphics['Wall'] = [ pygame.image.load(os.path.join('data', 'desert', 'wall1.png')).convert_alpha(),
                                  pygame.image.load(os.path.join('data', 'desert', 'wall2.png')).convert_alpha(),
                                  pygame.image.load(os.path.join('data', 'desert', 'wall3.png')).convert_alpha(),
                                  pygame.image.load(os.path.join('data', 'desert', 'wall4.png')).convert_alpha()]
        self.graphics['Decorations'] = [ pygame.image.load(os.path.join('data', 'desert', 'wall5.png')).convert_alpha(),
                                  pygame.image.load(os.path.join('data', 'desert', 'wall6.png')).convert_alpha(),
                                  pygame.image.load(os.path.join('data', 'desert', 'wall7.png')).convert_alpha()]
        self.graphics['Path'] = [pygame.image.load(os.path.join('data', 'desert', '{0}.png'.format(i))).convert_alpha() for i in range(15)]
        print type(self.graphics['Path'][0])
    #    for i in range(0, 15):
    #        self.graphics[str(i)] = pygame.image.load(os.path.join('data', 'desert', '{0}.png'.format(i))).convert_alpha()
         #   self.graphics['Restart'] = pygame.image.load(os.path.join('data', 'restart.png')).convert_alpha()
           # quit()

    def initialize_sounds(self): #ladda in allt ljud
        try:
            self.sounds['Nuke'] = pygame.mixer.Sound(os.path.join('data', 'nuke.wav'))
            self.sounds['Mate'] = pygame.mixer.Sound(os.path.join('data', 'mate.wav'))
            self.sounds['Explosion'] = pygame.mixer.Sound(os.path.join('data', 'explosion.wav'))
            self.sounds['Birth'] = pygame.mixer.Sound(os.path.join('data', 'birth.wav'))
            self.sounds['Change gender'] = pygame.mixer.Sound(os.path.join('data', 'gender.wav'))
            self.sounds['Poison'] = pygame.mixer.Sound(os.path.join('data', 'poison.wav'))
            self.sounds['Terminator'] = pygame.mixer.Sound(os.path.join('data', 'terminator.wav'))
            self.sounds['Gas source'] = pygame.mixer.Sound(os.path.join('data', 'gas.wav'))
        except pygame.error as e:
            print e
         #   quit()

    def initialize_menu(self): 
        self.menu_sprites = pygame.sprite.LayeredDirty() #Alla menysprites läggs in i en spritegroup
        self.menu_items['Stop sign'] = { 'x' : 700, 'y' : 120, 'amount' : 10} #Alla vapen i menyn får ett x och y-värde, och hur stort antal av det vapnet som användaren har
        self.menu_items['Poison'] = { 'x' : 700, 'y' : 160, 'amount' : 10 }
        self.menu_items['Terminator'] = { 'x' : 700, 'y' : 200, 'amount' : 10 }
        self.menu_items['Bomb'] = { 'x' : 700, 'y' : 240, 'amount' : 10 }
        self.menu_items['Change gender male'] = { 'x' : 700, 'y' : 280, 'amount' : 100 }
        self.menu_items['Change gender female'] = { 'x' : 700, 'y' : 320, 'amount' : 100 }
        self.menu_items['Nuke'] = { 'x' : 700, 'y': 360, 'amount' : 10}
        self.menu_items['Gas source'] = { 'x' : 700, 'y' : 400, 'amount' : 10}
   #     self.menu_items['Restart'] = { 'x' : 700, 'y' : 500, 'amount': 'Restart'}
        for name, coords in self.menu_items.iteritems():
            self.menu_sprites.add(Menu_items(self, name, coords['x'], coords['y'])) #Skapa sprites av alla vapen och lägg till i spritegroupen

    def generate_weapons(self):
        if pygame.time.get_ticks() - self.last_generated_weapon > random.randint(3000, 7000): #Mellan var 3:e och var 7:e sekunder, skapa ett slumpat vapen
            self.menu_items[random.choice(self.menu_items.keys())]['amount'] += 1
            self.last_generated_weapon = pygame.time.get_ticks()    

    def draw_level(self): #Rita ut kartan genom att läsa av ersätta tecknet i leveltest.map med en bild och blitta den
        for row in range(len(self.leveltest.map)):
            for col in range(len(self.leveltest.map[row])):
                tile = self.leveltest.map[row][col]
                if tile == '#' or tile == '*':
                    screen.blit(self.graphics['Grass'], pygame.Rect(col * tile_size, row * tile_size, 32, 32))
                if tile == '*':
                    screen.blit(self.graphics['Flower'], pygame.Rect(col * tile_size, row * tile_size, 32, 32))
               # elif tile == '.':
               #     screen.blit(random.choice(self.graphics['Dirt']), pygame.Rect(col * tile_size, row * tile_size, 32, 32))
                elif tile != '#':
                    screen.blit(self.graphics[tile], pygame.Rect(col * tile_size, row * tile_size, 32, 32))

    def update_sprites(self):
        self.male_count = 0 #Återställ räkningen av råttor
        self.female_count = 0
        for sprite in self.male_rat_sprites: #För alla råttor, kör deras update-metod och öka på räkningen
            sprite.update()
            self.male_count += 1
        for sprite in self.female_rat_sprites:
            sprite.update()
            self.female_count += 1
        for sprite in self.child_rat_sprites:
            sprite.update()
            if sprite.gender == 'M':
                self.male_count +=1
            else:
                self.female_count +=1
        for sprite in self.weapon_sprites: #För varje vapen
            sprite.update() #Kör deras update-metod
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
#        if self.win:
#            win_text = self.gameover_font.render('You won!', True, white)
#            win_textRect = win_text.get_rect(x = 50, y = 250)
#            screen.blit(win_text, win_textRect)
#        elif self.lost:
#            lost_text = self.gameover_font.render('Game over!', True, white)
#            lost_textRect = lost_text.get_rect(x = 20, y = 250)
#            screen.blit(lost_text, lost_textRect)
        text_items = {
                'Population':           {'text': 'Number of rats: {0}'.format(self.male_count + self.female_count), 'x': 680, 'y': 20},
                'Male population':      {'text': 'Male: {0}'.format(self.male_count), 'x': 680, 'y': 40},
                'Female population':    {'text': 'Female: {0}'.format(self.female_count), 'x': 680, 'y': 60}}
        for name, info in self.menu_items.iteritems():
            text_items[name] = {'text' : str(self.menu_items[name]['amount']), 'x' : self.menu_items[name]['x'] + 40, 'y' : self.menu_items[name]['y'] + 10}
        for text_item in text_items.values():
            render = self.menu_font.render(text_item['text'], True, white)
            render_rect = render.get_rect(x = text_item['x'], y = text_item['y'])
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
            self.weapon_sprites.add(Stop_sign(self, mouse_x, mouse_y)) #Lägg till vapnet i spritegroupen för vapen
#            self.play_sound()
        elif self.active_weapon == 'Poison':
            self.weapon_sprites.add(Poison(self, mouse_x, mouse_y))
        elif self.active_weapon == 'Bomb':
            self.weapon_sprites.add(Bomb(self, mouse_x, mouse_y))
        elif self.active_weapon == 'Change gender male':
            self.weapon_sprites.add(Change_gender_male(self, mouse_x, mouse_y))
        elif self.active_weapon == 'Change gender female':
            self.weapon_sprites.add(Change_gender_female(self, mouse_x, mouse_y))
        elif self.active_weapon == 'Terminator':
            self.weapon_sprites.add(Terminator(self, self.leveltest, mouse_x, mouse_y))
        elif self.active_weapon == 'Nuke':
            self.weapon_sprites.add(Nuke(self, mouse_x, mouse_y))
            self.weapon_sprites.add(Radiation(self, mouse_x -32, mouse_y - 32))
        elif self.active_weapon == 'Gas source':
            self.weapon_sprites.add(Gas_source(self, self.leveltest, mouse_x, mouse_y))
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
            screen.fill(black)
            clock.tick(100)
        #    self.draw_level() #Varje frame så ska banan ritas ut, vapen eventuellt genereras, alla sprites uppdateras, alla kollisioner räknas ut och användarinterfacet ritas ut
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
            pygame.display.flip()
            self.check_game_over()
            if self.win:
                self.done = True
                self.level += 1
                self.reset(self.level)

    def check_game_over(self): #testmetod
        population = self.male_count + self.female_count
        if population > 1500:
            self.lost = True
        elif population <= 0:
            self.win = True

    def create_rat(self, x = 0, y = 0, init = False, set_gender = None, isAdult = False, direction = None): #Metod för att skapa nya råttor (lite rörig just nu)
        if init: #Om det är spelstart
            while self.leveltest.is_wall(x, y): #Så länge som startposition är en vägg
                x, y = random.randrange(21), random.randrange(21) #Slumpa fram nya index
            x *= tile_size #Omvanlda koordinaterna från index i map-arrayen till koordinater
            y *= tile_size
            isAdult = True #Alla startråttor ska vara vuxna
        if not direction: #Om råttan inte har en riktning, måste vi placera den rakt över en tile så att en riktning kan beräknas
            x = x - (x % 32)
            y = y - (y % 32)
        rat = basic_rat(self, self.leveltest, x, y, isAdult, gender = set_gender, direction = direction) #Skapa råttan
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
                    female.check_mate(male) #Om de gör det, så kör metoden för att kolla om råttan ska bli gravid
            weapon_male_hit = pygame.sprite.groupcollide(self.weapon_sprites, self.male_rat_sprites, False, False)
            for weapon, males in weapon_male_hit.iteritems(): #Kolla om några manliga råttor kolliderar, och hantera kollisionen då
                for male in males:
                    if weapon in self.weapon_sprites:
                        weapon.handle_collision(male)

        elif pygame.time.get_ticks() - self.collision_time > 25:
            weapon_female_hit = pygame.sprite.groupcollide(self.weapon_sprites, self.female_rat_sprites, False, False) #Kvinnliga -> vapen
            for weapon, females in weapon_female_hit.iteritems():
                for female in females:
                    if weapon in self.weapon_sprites:
                        weapon.handle_collision(female)
            weapon_child_hit = pygame.sprite.groupcollide(self.weapon_sprites, self.child_rat_sprites, False, False) #Barn ->
            for weapon, children in weapon_child_hit.iteritems():
                for child in children:
                    if weapon in self.weapon_sprites:
                        weapon.handle_collision(child)
            weapon_weapon_hit = pygame.sprite.groupcollide(self.weapon_sprites, self.weapon_sprites, False, False) #Vapen -> Vapen
            for weapon1, weapons in weapon_weapon_hit.iteritems():
                for weapon2 in weapons:
                    if weapon1 is weapon2 or weapon1 not in self.weapon_sprites or weapon2 not in self.weapon_sprites: #Om det är samma objekt, fortsätt
                        continue
                    if weapon1.name == 'Explosion' and weapon2.name != 'Explosion' and weapon2.name != 'Gas source': #Om första vapnet är en explosion, och andra vapnet inte är det, hantera det (ta bort andra vapnet)
                        weapon1.handle_collision(weapon2)
                    elif weapon1.type == 'Weapon' and weapon2.name =='Terminator':
                        if weapon1.name == 'Change gender male' or weapon1.name == 'Change gender female': #Om ena vapnet är könsbyte och andra är terminator, gör om terminatorn till vanlig
                            gender = 'M' if weapon1.name == 'Change gender male' else 'F'
                            self.create_rat(weapon2.rect.x, weapon2.rect.y, isAdult = True, direction = weapon2.direction, set_gender = gender)
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
#rats = Game()
#rats.main_loop()
#pygame.quit()
test = main_menu()
test.main()
pygame.quit()
