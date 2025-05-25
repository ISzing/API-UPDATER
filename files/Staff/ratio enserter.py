import cv2
import pyautogui
import numpy as np

def get_cropped_frame(proportions, screen_width, screen_height):
    """Zwraca wycięty fragment ekranu na podstawie proporcji."""
    x, y, w, h = proportions
    x1, y1 = int(x * screen_width), int(y * screen_height)
    x2, y2 = int((x + w) * screen_width), int((y + h) * screen_height)
    
    # Pobierz zrzut ekranu i wytnij zaznaczony obszar
    screenshot = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    cropped = frame[y1:y2, x1:x2]
    return cropped

def main():
    # Pobranie rozdzielczości ekranu
    screen_width, screen_height = pyautogui.size()

    # Poproś użytkownika o proporcje (x, y, szerokość, wysokość)
    try:
        x = float(input("Podaj proporcję X (od 0 do 1): "))
        y = float(input("Podaj proporcję Y (od 0 do 1): "))
        w = float(input("Podaj proporcję szerokości (od 0 do 1): "))
        h = float(input("Podaj proporcję wysokości (od 0 do 1): "))
        proportions = (x, y, w, h)
    except ValueError:
        print("Błędne wartości. Spróbuj ponownie.")
        return

    # Sprawdź, czy proporcje są poprawne
    if not (0 <= x <= 1 and 0 <= y <= 1 and 0 <= w <= 1 and 0 <= h <= 1):
        print("Proporcje muszą być w zakresie od 0 do 1.")
        return

    live_preview_window = "Podgląd wycinka"

    while True:
        # Wycięcie fragmentu ekranu na podstawie proporcji
        cropped_frame = get_cropped_frame(proportions, screen_width, screen_height)

        # Wyświetlanie wyciętego fragmentu
        if cropped_frame.size > 0:
            cv2.imshow(live_preview_window, cropped_frame)

        # Zakończenie programu przy naciśnięciu klawisza 'q'
        if cv2.waitKey(1) == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
