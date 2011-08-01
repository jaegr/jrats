# -*- coding: utf-8 -*-
import random
import pygame
import rat
from collections import deque
import tile

class Weapons(pygame.sprite.DirtySprite): #Huvudklassen för vapen
    def __init__(self, game, x, y, name): #Tar en game-instans, musens x och y-värden, samt namnet på vapnet
        pygame.sprite.DirtySprite.__init__(self)
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

    def handle_collision(self, colliding_rat): #Om råttan inte är en terminator-råtta, sätt den som steril
        if isinstance(colliding_rat, rat.EnemyRat):
            colliding_rat.set_sterile()

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
                if not self.level.is_wall(x / tile.tile_size, y / tile.tile_size):
                    self.gas_clouds.append(Gas(self.game, x, y, self, self.level))
                    self.game.weapon_sprites.add(self.gas_clouds[-1])
                    done = True
                self.expand_directions.rotate(-1)
                if self.expand_directions[0] == 'Up':
                    self.initial_gas = False
                    done = True
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

class Gas(Weapons):
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


class Terminator(Weapons, rat.Rat): #Terminator-råttor ärver från både Weapons och Rat, för vi vill att de ska röra sig som råttor
    def __init__(self, game, level, x, y):
        Weapons.__init__(self, game, x, y, 'Terminator')
        self.level_instance = level #Råttklassen kräver en levelinstans
        self.base_image = self.image #Basbilden, som kommer att roteras
        rat.Rat.__init__(self)  #Kör Ratklassens __init__
        self.kills_left = 5 #Hur många råttor den kan döda innan den dör själv
        self.dirty = 2

    def handle_collision(self, colliding_rat):
        if isinstance(colliding_rat, rat.EnemyRat): #Om terminatorn kolliderar med en råtta, döda råttan
            self.kills_left -= 1
            self.game.score += 1
            colliding_rat.delete()
            self.play_sound()
            if self.kills_left <= 0: #
                self.delete()

    def update(self): #Kör Ratklassens update
        rat.Rat.update(self)


class ChangeGender(Weapons): #Byter kön på en råtta, och gör en terminator-råtta till en vanlig råtta
    def __init__(self, game, x, y, name):
        Weapons.__init__(self, game, x, y, name)

    def handle_collision(self, colliding_rat):
        if isinstance(colliding_rat, rat.Rat): #Om den kolliderar med en rått-typ, kör råttans change gender-metod, och ta bort sig själv
            if self.name == 'Change gender male' and colliding_rat.gender == 'M' or self.name == 'Change gender female' and colliding_rat.gender == 'F':
                return
            self.play_sound('Change gender')
            colliding_rat.change_gender()
            self.delete()

class Poison(Weapons): #Placeras ut på banan och vid kollision med en råtta så försvinner både råttan och giftet
    def __init__(self, game, x, y):
        Weapons.__init__(self, game, x, y, 'Poison')

    def handle_collision(self, colliding_rat):
        self.play_sound()
        if isinstance(colliding_rat, rat.EnemyRat):
            self.game.score += 1
        colliding_rat.delete()
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
        if isinstance(obj, rat.EnemyRat):
            self.game.score += 1
        obj.delete() #Allt som kolliderar med explosionen ska tas bort (både råttor och vapen)

