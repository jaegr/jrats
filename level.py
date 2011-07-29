# -*- coding: utf-8 -*-
import random
import pygame
import os
import ConfigParser
import tile

class Level(object):
    def __init__(self, level, game, editor_map): #level är startnivån (dvs. 1)
        self.map = []
        self.editor_map = editor_map
        self.game = game
        self.level = level
        self.tile_set = ''
        self.directions = {'N': 1, 'S': -1, 'E': 2, 'W': -2}

    def load_map(self):
        if not self.editor_map:
            parser = self.get_parser()
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

    def number_of_levels(self):
        parser = self.get_parser()
        lvl_number = 0
        while True:
            if parser.has_section('level{0}'.format(lvl_number + 1)):
                lvl_number += 1
            else:
                break
        return lvl_number

    def get_parser(self, filename=os.path.join('data', 'map.txt')):
        parser = ConfigParser.ConfigParser()
        parser.read(filename)
        return parser

    def load_tile_map(self):
        self.tile_map = [[tile.Tile(self.game, x, y, col, self.check_neighbors(x, y)) for x, col in enumerate(row)] for y, row in enumerate(self.map)]

    def get_directions(self, x, y):
        available_paths = []
        x = x / tile.tile_size
        y = y / tile.tile_size
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
        tile_x = rect.x / tile.tile_size #Bombens x och y-koordinater divideras med tile_size (32) för få rätt index i self.map
        tile_y = rect.y / tile.tile_size
        available_lanes = [rect] #Den tile som bomben exploderade på läggs först till
        directions = {'Up': (0, 1), 'Right': (1, 0), 'Down': (0, -1), 'Left': (-1, 0)} #directions gör det lätt att öka indexet i self.map för att gå vidare till nästa kolumn eller rad
        for direction in directions.values(): #För varje riktning
            while True:
                tile_y += direction[1] #Gå vidare till nästa tile i den riktningen
                tile_x += direction[0]
                if not self.is_wall(tile_x, tile_y): #Om det inte är en vägg, lägg till tilen
                    available_lanes.append(pygame.Rect(tile_x * tile.tile_size, tile_y * tile.tile_size, rect.h, rect.w))
                else:
                    tile_x = rect.x / tile.tile_size #Annars så kan explosionen inte expandera mer i den riktningen, så återställ index och hoppa ur while-loopen
                    tile_y = rect.y / tile.tile_size
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
