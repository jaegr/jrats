# -*- coding: utf-8 -*-
import random
import pygame
import tile
import weapons

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
        if not self.direction: #Om råttan är instängd
            return
        if self.direction == self.directions['N']: #Flytta fram råttorna en pixel i dess riktning
            self.rect.y -= 1
        elif self.direction == self.directions['E']:
            self.rect.x += 1
        elif self.direction == self.directions['S']:
            self.rect.y += 1
        elif self.direction == self.directions['W']:
            self.rect.x -= 1
        if self.rect.x % tile.tile_size == 0 and self.rect.y % tile.tile_size == 0: #Om råttan är mitt på en tile måste vi kolla vilka riktningar som är tillgängliga
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
        if isinstance(weapon, weapons.StopSign) or isinstance(weapon, weapons.Bomb) and self.direction:
            for items in self.direction_timer:
                if weapon == items[0]:
                    return 0
            self.direction_timer.append([weapon, pygame.time.get_ticks()])
            self.direction = -self.direction
            return 1

    def delete(self): #Ta bort råttan från spritegroupen (och därmed från spelet)
        self.kill()


class EnemyRat(Rat):
    def __init__(self, game, level, x=32, y=32, isAdult=True, gender=None, direction=None, sterile = False): #Vanliga råttor
        self.level_instance = level #Ta emot levelinstansen (som krävs för att bestämma riktningar)
        self.game = game            #Gameklassens instans krävs bl.a. för att byta kön eftersom den skapar en ny råtta av motsatt kön
        if not gender:          #Om råttans kön inte redan är bestäms, välj ett slumpvis
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
        self.sterile = sterile      #Råttorna blir sterila om de utsätts för strålning, men de föds aldrig som sterila
        self.birth = pygame.time.get_ticks()  #Hur länge sen de föddes. Barn blir vuxna efter 10 sekunder.
        Rat.__init__(self, direction) #Kör huvudklassens __init__
       # print self.gender, self.adult, self.direction, self.pregnant, self.sterile, self.name, self.type

    def change_gender(self): #Skapar en ny råttsprite vid könbyte.
        new_gender = 'M' if self.gender == 'F' else 'F'
        self.game.create_rat(x=self.rect.x, y=self.rect.y, set_gender=new_gender,
                             isAdult=self.adult, direction=self.direction, sterile = self.sterile)
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
                self.game.create_rat(x=self.rect.x, y=self.rect.y, set_gender=self.gender, isAdult=True, direction=self.direction, sterile = self.sterile)
                self.delete()
