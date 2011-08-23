# -*- coding: utf-8 -*-
import random
import pygame
import rat
from collections import deque
import tile

class Weapons(pygame.sprite.DirtySprite): #Huvudklassen för vapen
    """Base class for all weapons"""
    def __init__(self, game, x, y, name):
        pygame.sprite.DirtySprite.__init__(self)
        self.name = name
        self.game = game
        self.image = self.game.graphics[self.name]
        self.rect = self.image.get_rect() 
        self.rect.x = x 
        self.rect.y = y
        self.dirty = 2 

    def handle_collision(self, obj): 
        """Empty method for objects that don't collide with rats"""
        pass

    def delete(self):
        """Method for removing the sprite"""
        self.kill()

    def update(self): 
        """Empty method for objects whose logic doesn't update each frame"""
        pass

    def play_sound(self, file=None): 
        "Plays the weapon sound"
        if not file:
            file = self.name
        self.game.play_sound(file)


class Nuke(Weapons): 
    def __init__(self, game, x, y):
        Weapons.__init__(self, game, x, y, 'Nuke') 
        self.activation_time = pygame.time.get_ticks() 
        self.play_sound() 

    def update(self):
        #Remove weapon after five seconds
        if pygame.time.get_ticks() - self.activation_time > 5000: 
            self.delete()


class Radiation(Weapons): 
    def __init__(self, game, x, y):
        Weapons.__init__(self, game, x, y, 'Radiation')
        self.activation_time = pygame.time.get_ticks()
        self.blink_time = pygame.time.get_ticks() 

    def handle_collision(self, colliding_rat): 
        #Only make actual rats (and not terminator rats) sterile
        if isinstance(colliding_rat, rat.EnemyRat):
            colliding_rat.set_sterile()

    def update(self):
        if pygame.time.get_ticks() - self.activation_time > 5000: #Remove weapon after five seconds
            self.delete()
        else:
            #Every 50 ms, either show or hide the sprite
            if pygame.time.get_ticks() - self.blink_time > 50: 
                self.visible = 1 if self.visible == 0 else 0 
                self.blink_time = pygame.time.get_ticks() 


class GasSource(Weapons):
    def __init__(self, game, level, x, y):
        Weapons.__init__(self, game, x, y, 'Gas source')
        self.level = level
        self.gas_timer = pygame.time.get_ticks() 
        self.start_x = x
        self.start_y = y
        self.dir = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        self.gas_clouds = []
        self.coords = []
        self.checked_coords = [(x,y)]
        self.initialize_gas(self.start_x / 32, self.start_y / 32)
        self.play_sound()

    def initialize_gas(self, x, y):
        """Checks recursively which tiles the gas can spread to and adds the coordinates to a list"""
        for x_offset, y_offset in self.dir:
             #At most 10 clouds
            if len(self.coords) <= 10:
                new_x = x + x_offset
                new_y = y + y_offset
                #Checks if position is a wall, or has already been added or is the start position
                if not self.level.is_wall(new_x, new_y) and (new_x, new_y) not in self.coords and (new_x * 32, new_y * 32) != (self.start_x, self.start_y):
                    self.coords.append((new_x, new_y))
        #If self.coords is empty, there's no room for the gas to expand
        #len(set(self.coords) - set(self.checked_coords)) > 0 checks if there are any available tiles left to check
        if len(self.coords) <= 10 and self.coords and len(set(self.coords) - set(self.checked_coords)) > 0:
            x, y = random.choice(list(set(self.coords) - set(self.checked_coords))) #Get random unchecked coordinates
            self.checked_coords.append((x,y))
            self.initialize_gas(x, y)

    def update(self):
        if pygame.time.get_ticks() - self.gas_timer > 100:
            if self.coords:
                #Pop the first pair of coordinates and add a gas cloud on that position
                x, y = self.coords.pop(0)
                self.gas_clouds.append(Gas(self.game, x * 32, y * 32, self.level))
                self.game.weapon_sprites.add(self.gas_clouds[-1])
            else:
                #When all coordinates have been popped, start removing a random cloud every update
                if len(self.gas_clouds) > 0:
                    gas_cloud = random.choice(self.gas_clouds)
                    gas_cloud.delete()
                    self.gas_clouds.remove(gas_cloud)
                else:
                    self.delete()
            self.gas_timer = pygame.time.get_ticks()


class Gas(Weapons):
    """Class for the gas clouds that GasSource creates"""
    def __init__(self, game, x, y, level):
        Weapons.__init__(self, game, x, y, 'Gas')
        self.level = level

    def handle_collision(self, rat):
        self.game.score += 1
        rat.delete()


class Terminator(Weapons, rat.Rat): 
    """Class for Terminator rats. Inherits from Weapons and Rat"""
    def __init__(self, game, level, x, y):
        Weapons.__init__(self, game, x, y, 'Terminator')
        self.level_instance = level 
        self.base_image = self.image 
        rat.Rat.__init__(self) 
        self.kills_left = 5 
        self.dirty = 2

    def handle_collision(self, colliding_rat):
        if isinstance(colliding_rat, rat.EnemyRat): 
            self.kills_left -= 1
            self.game.score += 1
            colliding_rat.delete()
            self.play_sound()
            if self.kills_left <= 0: #
                self.delete()

    def update(self):
        rat.Rat.update(self)


class ChangeGender(Weapons): 
    """Class for gender change weapon"""
    def __init__(self, game, x, y, name):
        Weapons.__init__(self, game, x, y, name)

    def handle_collision(self, colliding_rat):
        #If either regular rat or terminator rat
        if isinstance(colliding_rat, rat.Rat): 
            if self.name == 'Change gender male' and colliding_rat.gender == 'M' or self.name == 'Change gender female' and colliding_rat.gender == 'F':
                return
            self.play_sound('Change gender')
            colliding_rat.change_gender()
            self.delete()

class Poison(Weapons): 
    """Class for poison weapon"""
    def __init__(self, game, x, y):
        Weapons.__init__(self, game, x, y, 'Poison')

    def handle_collision(self, colliding_rat):
        self.play_sound()
        if isinstance(colliding_rat, rat.EnemyRat):
            self.game.score += 1
        colliding_rat.delete()
        self.delete()


class StopSign(Weapons): 
    """Class for stop sign weapon"""
    def __init__(self, game, x, y):
        Weapons.__init__(self, game, x, y, 'Stop sign')
        self.hits_left = 5 

    def handle_collision(self, rat):
        #change_direction() returns either True or False depending on if the rat changed direction. Only decrease hits_left if rat changed direction
        if rat.change_direction(self): 
            self.hits_left -= 1
            if self.hits_left <= 0:
                self.delete()



class Bomb(Weapons): 
    """Class for bomb weapon"""
    def __init__(self, game, x, y):
        Weapons.__init__(self, game, x, y, 'Bomb')
        self.start_countdown = pygame.time.get_ticks()
        self.countdown = 2
        self.exploded = False #Used in Game class. If true, create explosion sprites 

    def handle_collision(self, rat):
        rat.change_direction(self) 

    def update(self):
        if pygame.time.get_ticks() - self.start_countdown > 1000: 
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
        if pygame.time.get_ticks() - self.explosion_time > 200: 
            self.delete()

    def handle_collision(self, obj):
        #Remove every object that collides with the explosion
        if isinstance(obj, rat.EnemyRat):
            self.game.score += 1
        obj.delete() 

