import pyautogui
import time

try:
    while True:
        x, y = pyautogui.position()  # Pobierz pozycję myszy
        print(f'Pozycja myszy: x={x}, y={y}')
        time.sleep(0.5)  # Odśwież co 0.5 sekundy
except KeyboardInterrupt:
    print("Zatrzymano śledzenie pozycji.")
