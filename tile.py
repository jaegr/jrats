# -*- coding: utf-8 -*-
import random
import pygame

tile_size = 32

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
        self.image = self.get_image()
        self.rect = self.image.get_rect()
        self.rect.x = self.x * tile_size
        self.rect.y = self.y * tile_size

    def get_image(self):
        if self.name == 'Path':
            return self.game.graphics['Path'][self.tile_number]
        else:
            if random.randint(1, 100) < 95:
                return random.choice(self.game.graphics['Wall'])
            else:
                return random.choice(self.game.graphics['Decorations'])


    def get_name_from_tile(self):
        if self.tile == '#':
            return 'Wall'
        elif self.tile == '.':
            return 'Path'