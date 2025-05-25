import cv2
import pyautogui
import numpy as np
import tkinter as tk
from tkinter import messagebox
import threading
import time
import os
CONFIG_FILE = os.path.join("..", "config.txt")
preview_thread = None
preview_running = False


def load_config():
    config = {}
    try:
        with open(CONFIG_FILE, "r") as file:
            for line in file:
                line = line.strip()
                if line and "=" in line:
                    name, values = line.split("=", 1)
                    values = values.strip().split(",")
                    if len(values) == 4:
                        config[name.strip()] = [float(v) for v in values]
    except FileNotFoundError:
        print("Plik konfiguracyjny nie istnieje.")
    return config


def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as file:
            for key, proportions in config.items():
                file.write(f"{key} = {', '.join(map(str, proportions))}\n")
    except Exception as e:
        print(f"Błąd przy zapisywaniu pliku konfiguracyjnego: {e}")


def get_cropped_frame(proportions, screen_width, screen_height):
    x, y, w, h = proportions
    x1, y1 = int(x * screen_width), int(y * screen_height)
    x2, y2 = int((x + w) * screen_width), int((y + h) * screen_height)

    screenshot = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    cropped = frame[y1:y2, x1:x2]
    return cropped


def preview_changes(proportions, screen_width, screen_height):
    global preview_running
    preview_running = True
    while preview_running:
        cropped_frame = get_cropped_frame(proportions, screen_width, screen_height)
        cv2.imshow("Preview", cropped_frame)
        if cv2.waitKey(1) & 0xFF == 27:  # Escape key to close
            break
    cv2.destroyAllWindows()


def stop_preview():
    global preview_running
    preview_running = False
    time.sleep(0.1)  # Daj czas na zakończenie wątku


def create_gui():
    global preview_thread

    screen_width, screen_height = pyautogui.size()
    config = load_config()

    root = tk.Tk()
    root.title("Konfigurator Proporcji")

    tk.Label(root, text="Wybierz konfigurację:").grid(row=0, column=0, padx=10, pady=5)
    config_var = tk.StringVar(root)
    config_var.set(next(iter(config.keys())) if config else "")

    # Dodaj śledzenie zmian w config_var
    config_var.trace('w', lambda *args: load_selected())

    # Dodaj OptionMenu
    tk.OptionMenu(root, config_var, *config.keys()).grid(row=0, column=1, padx=10, pady=5)

    tk.Label(root, text="X:").grid(row=1, column=0, padx=10, pady=5)
    x_entry = tk.Entry(root, width=10)
    x_entry.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(root, text="Y:").grid(row=2, column=0, padx=10, pady=5)
    y_entry = tk.Entry(root, width=10)
    y_entry.grid(row=2, column=1, padx=10, pady=5)

    tk.Label(root, text="W:").grid(row=3, column=0, padx=10, pady=5)
    w_entry = tk.Entry(root, width=10)
    w_entry.grid(row=3, column=1, padx=10, pady=5)

    tk.Label(root, text="H:").grid(row=4, column=0, padx=10, pady=5)
    h_entry = tk.Entry(root, width=10)
    h_entry.grid(row=4, column=1, padx=10, pady=5)

    def load_selected():
        selection = config_var.get()
        if selection in config:
            proportions = config[selection]
            x_entry.delete(0, tk.END)
            y_entry.delete(0, tk.END)
            w_entry.delete(0, tk.END)
            h_entry.delete(0, tk.END)
            x_entry.insert(0, proportions[0])
            y_entry.insert(0, proportions[1])
            w_entry.insert(0, proportions[2])
            h_entry.insert(0, proportions[3])
        else:
            messagebox.showerror("Błąd", "Wybrana konfiguracja nie istnieje!")

    def save_changes():
        try:
            x = float(x_entry.get())
            y = float(y_entry.get())
            w = float(w_entry.get())
            h = float(h_entry.get())
            selection = config_var.get()
            config[selection] = [x, y, w, h]
            save_config(config)
            messagebox.showinfo("Sukces", "Zapisano zmiany!")
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowe wartości!")

    def update_proportions():
        global preview_thread
        try:
            # Pobieranie aktualnych wartości bezpośrednio przed uruchomieniem podglądu
            x = float(x_entry.get())
            y = float(y_entry.get())
            w = float(w_entry.get())
            h = float(h_entry.get())
            
            # Zatrzymaj poprzedni podgląd
            if preview_thread and preview_thread.is_alive():
                stop_preview()
                preview_thread.join()

            # Uruchom nowy podgląd w wątku z aktualnie wprowadzonymi wartościami
            preview_thread = threading.Thread(
                target=preview_changes, 
                args=([x, y, w, h], screen_width, screen_height)
            )
            preview_thread.start()
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowe wartości!")

    tk.Button(root, text="Załaduj", command=load_selected).grid(row=5, column=0, padx=10, pady=10)
    tk.Button(root, text="Zapisz", command=save_changes).grid(row=5, column=1, padx=10, pady=10)
    tk.Button(root, text="Aktualizuj", command=update_proportions).grid(row=6, column=0, columnspan=2, pady=10)

    root.mainloop()


if __name__ == "__main__":
    create_gui()
