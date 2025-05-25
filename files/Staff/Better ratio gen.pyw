import cv2
import pyautogui
import time
import numpy as np
import tkinter as tk
from tkinter import messagebox
import threading

# Zmienna globalna do przechowywania współrzędnych zaznaczenia
rect_start = None
rect_end = None
drawing = False
proportions = None

def mouse_callback(event, x, y, flags, param):
    global rect_start, rect_end, drawing

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        rect_start = (x, y)
        rect_end = (x, y)
    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        rect_end = (x, y)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        rect_end = (x, y)

def calculate_proportions(start, end, screen_width, screen_height):
    x1, y1 = start
    x2, y2 = end
    x1, x2 = sorted([x1, x2])
    y1, y2 = sorted([y1, y2])
    return (x1 / screen_width, y1 / screen_height, 
            (x2 - x1) / screen_width, (y2 - y1) / screen_height)

def get_cropped_frame(proportions, screen_width, screen_height):
    x, y, w, h = proportions
    x1, y1 = int(x * screen_width), int(y * screen_height)
    x2, y2 = int((x + w) * screen_width), int((y + h) * screen_height)
    screenshot = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    cropped = frame[y1:y2, x1:x2]
    return cropped

def copy_to_clipboard():
    global proportions
    if proportions is None:
        messagebox.showwarning("Błąd", "Proporcje nie zostały jeszcze wyznaczone!")
        return
    root.clipboard_clear()
    root.clipboard_append(str(proportions))
    root.update()

def update_text_widget():
    global proportions
    text_widget.config(state="normal")
    text_widget.delete("1.0", tk.END)
    if proportions:
        text_widget.insert("1.0", str(proportions))
    else:
        text_widget.insert("1.0", "Proporcje nie zostały jeszcze wyznaczone.")
    text_widget.config(state="disabled")

def opencv_main():
    global rect_start, rect_end, proportions

    screen_width, screen_height = pyautogui.size()
    screenshot = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    cv2.namedWindow("Zaznacz obszar")
    cv2.setMouseCallback("Zaznacz obszar", mouse_callback)

    last_update_time = time.time()
    live_preview_window = "Podgląd na żywo"

    while True:
        img_copy = frame.copy()
        if rect_start and rect_end:
            cv2.rectangle(img_copy, rect_start, rect_end, (0, 255, 0), 2)
        cv2.imshow("Zaznacz obszar", img_copy)
        key = cv2.waitKey(1)

        if key == ord('q'):
            break
        elif key == ord('s') and rect_start and rect_end:
            proportions = calculate_proportions(rect_start, rect_end, screen_width, screen_height)
            print(f"Proporcje zaznaczonego obszaru: {proportions}")
            update_text_widget()

        if proportions and (time.time() - last_update_time) > 2:
            cropped_frame = get_cropped_frame(proportions, screen_width, screen_height)
            cv2.imshow(live_preview_window, cropped_frame)
            last_update_time = time.time()

    cv2.destroyAllWindows()

# Tworzenie głównego okna
root = tk.Tk()
root.title("Wyświetl i kopiuj dane")

text_widget = tk.Text(root, height=10, width=50)
text_widget.insert("1.0", "Proporcje nie zostały jeszcze wyznaczone.")
text_widget.config(state="disabled")
text_widget.pack(pady=10)

button = tk.Button(root, text="Kopiuj dane", command=copy_to_clipboard)
button.pack(pady=5)

# Uruchomienie OpenCV w osobnym wątku
opencv_thread = threading.Thread(target=opencv_main)
opencv_thread.daemon = True
opencv_thread.start()

# Uruchomienie aplikacji Tkinter
root.mainloop()
