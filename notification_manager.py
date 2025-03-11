import pygame
import json

class NotificationManager:
    def __init__(self, sound_file):
        pygame.mixer.init()
        self.notification_sound = pygame.mixer.Sound(sound_file)
        
    def play_notification(self, user_preferences):
        preferences = json.loads(user_preferences)
        if preferences.get('notifications', True):
            self.notification_sound.play()