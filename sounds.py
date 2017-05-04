import pygame
import os

class SoundManager(object):

    START = 'start'
    PAR = 'par'
    HIT = 'hit'
    MISS = 'miss'
    
    def __init__(self):
        pygame.mixer.pre_init(44100,-16,1, 64)
        pygame.mixer.init()
        pygame.init()

        self.gunshot1 = pygame.mixer.Sound(os.path.dirname(os.path.realpath(
            __file__)) + "/sounds/gun-gunshot-01.ogg")
        self.beep1 = pygame.mixer.Sound(os.path.dirname(
            os.path.realpath(__file__)) + "/sounds/beep-01.ogg")
        self.beep2 = pygame.mixer.Sound(os.path.dirname(
            os.path.realpath(__file__)) + "/sounds/beep-02.ogg")
        self.beep3 = pygame.mixer.Sound(os.path.dirname(
            os.path.realpath(__file__)) + "/sounds/beep-03.ogg")

    def play_sound(self, sound):
        if sound == self.START:
            self.beep3.play()
        elif sound == self.PAR:
            self.beep1.play()
        elif sound == self.HIT:
            self.gunshot1.play()
        elif sound == self.MISS:
            self.beep2.play()