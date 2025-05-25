import cv2
import pyautogui
import time
import numpy as np

# Zmienna globalna do przechowywania współrzędnych zaznaczenia
rect_start = None
rect_end = None
drawing = False
proportions = None

def mouse_callback(event, x, y, flags, param):
    global rect_start, rect_end, drawing

    # Rozpoczęcie zaznaczania przy naciśnięciu lewego przycisku myszy
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        rect_start = (x, y)
        rect_end = (x, y)

    # Aktualizacja pozycji końca prostokąta
    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        rect_end = (x, y)

    # Zakończenie zaznaczania przy puszczeniu lewego przycisku myszy
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        rect_end = (x, y)

def calculate_proportions(start, end, screen_width, screen_height):
    """Przelicza współrzędne na proporcje w stosunku do rozdzielczości ekranu."""
    x1, y1 = start
    x2, y2 = end
    x1, x2 = sorted([x1, x2])
    y1, y2 = sorted([y1, y2])

    return (x1 / screen_width, y1 / screen_height, 
            (x2 - x1) / screen_width, (y2 - y1) / screen_height)

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
    global rect_start, rect_end, proportions

    # Pobranie rozdzielczości ekranu
    screen_width, screen_height = pyautogui.size()

    # Zrobienie zrzutu ekranu
    screenshot = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # Ustawienie okna z możliwością zaznaczania myszką
    cv2.namedWindow("Zaznacz obszar")
    cv2.setMouseCallback("Zaznacz obszar", mouse_callback)

    last_update_time = time.time()
    live_preview_window = "Podgląd na żywo"

    while True:
        img_copy = frame.copy()

        # Rysowanie prostokąta w trakcie zaznaczania
        if rect_start and rect_end:
            cv2.rectangle(img_copy, rect_start, rect_end, (0, 255, 0), 2)

        # Wyświetlanie podglądu zaznaczania
        cv2.imshow("Zaznacz obszar", img_copy)
        key = cv2.waitKey(1)

        # Zakończenie programu przy naciśnięciu klawisza 'q'
        if key == ord('q'):
            break

        # Po naciśnięciu 's' zapisujemy zaznaczenie jako proporcje
        elif key == ord('s') and rect_start and rect_end:
            proportions = calculate_proportions(rect_start, rect_end, screen_width, screen_height)
            print(f"Proporcje zaznaczonego obszaru: {proportions}")

        # Aktualizacja podglądu na żywo co 2 sekundy
        if proportions and (time.time() - last_update_time) > 2:
            cropped_frame = get_cropped_frame(proportions, screen_width, screen_height)
            cv2.imshow(live_preview_window, cropped_frame)
            last_update_time = time.time()

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
