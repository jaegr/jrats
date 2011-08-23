# -*- coding: utf-8 -*-
import random
import pygame
import tile
import weapons

class Rat(pygame.sprite.DirtySprite):
    """Base class for all rats, which both regular rats and terminator rats inherit from"""
    def __init__(self, direction=None):
        """Optional input argument direction for when a new rat previously had a direction (male/female to female/male or child to adult or terminator to regular rat)"""
        pygame.sprite.DirtySprite.__init__(self)
        #Directions as integers simplifies the code for reversing direction (self.direction = -self.direction)
        self.directions = {'N': 1, 'S': -1, 'E': 2, 'W': -2} 
        #For rotating the rat sprite. The keys correspond to the values in self.directions
        self.rotation = {1: 0, -1: 180, 2: 270, -2: 90}
        #Keeps track of when a rat collided with an object
        self.direction_timer = []
        self.direction = self.get_direction(direction)
        self.dirty = 2
        self.last_check = 0

    def get_direction(self, direction):
        #Newly born rats don't have a direction
        if not direction:
            available_directions = self.level_instance.get_directions(self.rect.x, self.rect.y)
            #If the user creates a map in the level editor with a path tile surrounded by walls, the rat is stuck and don't get a direction
            if not len(available_directions):
                return None
            else:
                return random.choice(available_directions)
        else:
            return direction

    def update(self):
        #If the rat is stuck (surrounded by walls) there is nothing to update
        if not self.direction: 
            return
        if self.direction == self.directions['N']:
            self.rect.y -= 1
        elif self.direction == self.directions['E']:
            self.rect.x += 1
        elif self.direction == self.directions['S']:
            self.rect.y += 1
        elif self.direction == self.directions['W']:
            self.rect.x -= 1
        #If the rat is in the middle of a tile, check which directions are available
        if self.rect.x % tile.tile_size == 0 and self.rect.y % tile.tile_size == 0:
            available_paths = self.level_instance.get_directions(self.rect.x, self.rect.y)
            #If there is only one available direction to go, it must be the opposite direction from which the rat came, so change direction
            if len(available_paths) == 1: 
                self.direction = -self.direction
            else:
                #Else, remove the opposite direction (the rat only turns around if there are no other directions) and choose a random direction
                if -self.direction in available_paths:
                    available_paths.remove(-self.direction)
                self.direction = random.choice(available_paths) #Annars välj en slumpvis väg
        #Rotate the image
        self.image = pygame.transform.rotate(self.base_image, self.rotation[self.direction]) 
        for index, items in enumerate(self.direction_timer):
                if pygame.time.get_ticks() - items[1] > 500:
                    self.direction_timer.pop(index)

    def change_direction(self, weapon = None): 
        """Makes the rat turn around if all checks are passed"""
        #Only change direction once every frame at the most
        if self.last_check == pygame.time.get_ticks(): 
            return 0
        else:
            self.last_check = pygame.time.get_ticks()
        if isinstance(weapon, weapons.StopSign) or isinstance(weapon, weapons.Bomb) and self.direction:
            #If the object is already being tracked in direction_timer, ignore the collision
            for items in self.direction_timer:
                if weapon == items[0]:
                    return 0
            self.direction_timer.append([weapon, pygame.time.get_ticks()])
            self.direction = -self.direction
            return 1

    def delete(self):
        self.kill()


class EnemyRat(Rat):
    """Class for the enemy rats"""
    def __init__(self, game, level, x=32, y=32, isAdult=True, gender=None, direction=None, sterile = False):
        self.level_instance = level
        self.game = game 
        self.gender = self.get_gender(gender)
        self.adult = isAdult
        self.name = self.get_name()
        self.pregnant = False
        #Rotating an image is destructive, so we need to have a image which we can use as a template
        self.base_image = self.game.graphics[self.name]
        self.image = self.base_image
        self.rect = self.base_image.get_rect()
        self.rect.x = x  
        self.rect.y = y
        #Time since a pregnant rat had a baby
        self.time_since_baby = 0
        self.babies_left = 0 
        self.sterile = sterile
        #How long ago the rat was born. The rat turns into an adult after 10 seconds
        self.birth = pygame.time.get_ticks()
        Rat.__init__(self, direction)

    def get_name(self):
        """Returns the name of the rat"""
        if not self.adult:
            return 'Baby rat'
        elif self.gender == 'M':
            return 'Male rat'
        else:
            return 'Female rat'

    def get_gender(self, gender):
        """Returns the gender of the rat, or randomly chooses one if the rat doesn't have one yet"""
        if not gender:
            return random.choice(['M', 'F'])
        else:
            return gender


    def change_gender(self):
        """Creates a new rat with the new gender and kills the old rat"""
        new_gender = 'M' if self.gender == 'F' else 'F'
        self.game.create_rat(x=self.rect.x, y=self.rect.y, set_gender=new_gender,
                             isAdult=self.adult, direction=self.direction, sterile = self.sterile)
        self.delete()

    def check_mate(self, other_rat):
        """Checks if the rats can mate"""
        if not self.pregnant and self.adult and other_rat.adult and not self.sterile and not other_rat.sterile: 
            self.handle_pregnant()
            return True

    def handle_pregnant(self):
        """Handles pregnant rats"""
        if not self.pregnant:
            self.pregnant = True
            self.time_since_baby = pygame.time.get_ticks() 
            self.babies_left = 5
        elif pygame.time.get_ticks() - self.time_since_baby > 4000 and self.pregnant:
            self.time_since_baby = pygame.time.get_ticks() 
            self.game.create_rat(x=self.rect.x, y=self.rect.y)
            self.babies_left -= 1 
            if self.babies_left <= 0: 
                self.pregnant = False 

    def set_sterile(self):
        """Set rat as sterile"""
        self.sterile = True

    def update(self):
        Rat.update(self)
        if self.gender == 'F' and self.pregnant:
            self.handle_pregnant()

        if not self.adult: 
            if pygame.time.get_ticks() - self.birth > 10000:
                self.game.create_rat(x=self.rect.x, y=self.rect.y, set_gender=self.gender, isAdult=True, direction=self.direction, sterile = self.sterile)
                self.delete()
