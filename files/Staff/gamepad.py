import pygame
from pygame.locals import *

# Inicjalizacja pygame i joysticka
pygame.init()
pygame.joystick.init()

# Sprawdzenie, czy joystick został wykryty
if pygame.joystick.get_count() == 0:
    print("Brak podłączonego pada!")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Znaleziono pad: {joystick.get_name()}")

try:
    while True:
        for event in pygame.event.get():
            if event.type == JOYBUTTONDOWN:
                print(f"Przycisk wciśnięty: {event.button}")
            elif event.type == JOYBUTTONUP:
                print(f"Przycisk zwolniony: {event.button}")
            elif event.type == JOYAXISMOTION:
                print(f"Oś {event.axis} poruszona: {event.value}")
except KeyboardInterrupt:
    print("Zakończono")
    pygame.quit()
