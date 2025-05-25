import os
import json
from tkinter import Tk, ttk, Text, Button, Label, Entry, StringVar, OptionMenu, filedialog, PhotoImage, messagebox
from tkinter.messagebox import showerror, showinfo
import cv2
import pyautogui
import numpy as np
import threading
import time

CONFIG_FILE = "config.json"
PROPORTIONS_FILE = os.path.join("..", "config.txt")
Pad_FILE = os.path.join("..", "pad.json")
preview_thread = None
preview_running = False

def load_config():
    """Wczytuje ścieżkę z pliku konfiguracyjnego."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            data = json.load(file)
            return data.get("path")
    return None
def padjsonop():
    if os.path.exists(Pad_FILE):
        with open(Pad_FILE,"r") as f:
            configpad = json.load(f)
            return configpad
def load_proportions():
    config = {}
    try:
        with open(PROPORTIONS_FILE, "r") as file:
            for line in file:
                line = line.strip()
                if line and "=" in line:
                    name, values = line.split("=", 1)
                    values = [v.strip() for v in values.strip().split(",")]  # DODAJ .strip() do każdej wartości
                    if len(values) == 4:
                        config[name.strip()] = [float(v) for v in values]
    except FileNotFoundError:
        print("Plik proporcji nie istnieje.")
    return config


#def save_proportions(config):
    try:
        with open(PROPORTIONS_FILE, "w") as file:
            for key, proportions in config.items():
                # Formatujemy z kontrolą liczby miejsc po przecinku
                formatted_proportions = ", ".join([f"{p:.16f}" for p in proportions])
                file.write(f"{key} = {formatted_proportions}\n")
                print(f"Zapisano: {key} = {formatted_proportions}")
    except Exception as e:
        print(f"Błąd przy zapisywaniu pliku proporcji: {e}")


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
def save_config(path):
    """Zapisuje ścieżkę do pliku konfiguracyjnego."""
    with open(CONFIG_FILE, "w") as file:
        json.dump({"path": path}, file)

def read_config_sections(path):
    config_path = os.path.join(path, "config.txt")
    if os.path.exists(config_path):
        with open(config_path, "r") as file:
            lines = file.readlines()
        print(f"Wczytano linie: {lines}")
        # Podział na sekcje: przed i po #proporcje
        before_proporcje = []
        after_proporcje = []
        proporcje_found = False

        for line in lines:
            if "#proporcje" in line:
                proporcje_found = True
                continue  # Pomijamy linię "#proporcje"
            if proporcje_found:
                after_proporcje.append(line)
            else:
                before_proporcje.append(line)

        return before_proporcje, after_proporcje
    return None, None

def write_config_sections(path, before_proporcje, after_proporcje):
    """Zapisuje sekcje do pliku config.txt, zachowując linie odstępów."""
    config_path = os.path.join(path, "config.txt")
    with open(config_path, "w") as file:
        file.writelines([line if line.endswith("\n") else line + "\n" for line in before_proporcje])
        file.write("#proporcje\n")
        file.writelines([line if line.endswith("\n") else line + "\n" for line in after_proporcje])

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Konfiguracja Klawiatury i Pada")
        
        # Load configuration and screen dimensions first
        self.config_path = load_config()
        
        # Load proportions configuration
        self.proportions_config = load_proportions()
        
        # Get screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        
        self.proporcje_mode = False  # Flaga do przełączania widoku proporcji

        # Tworzymy zakładki
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both")

        # Zakładki
        self.settings_tab = ttk.Frame(self.notebook)
        self.keyboard_tab = ttk.Frame(self.notebook)
        self.proportions_tab = ttk.Frame(self.notebook)
        self.pad_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.settings_tab, text="Ustawienia")
        self.notebook.add(self.proportions_tab, text="Proporcje")
        self.notebook.add(self.keyboard_tab, text="Klawiatura")
        self.notebook.add(self.pad_tab, text="Pad")

        # Wywołujemy funkcje do każdej zakładki
        self.create_settings_tab()
        self.create_proportions_tab()
        self.create_keyboard_tab()
        self.create_pad_tab()

    def create_proportions_tab(self):
        """Zakładka proporcji."""
        Label(self.proportions_tab, text="Wybierz konfigurację:").grid(row=0, column=0, padx=10, pady=5)
        self.config_var = StringVar(self.proportions_tab)
        self.config_var.set(next(iter(self.proportions_config.keys())) if self.proportions_config else "")

        OptionMenu(self.proportions_tab, self.config_var, *self.proportions_config.keys(), command=self.load_selected).grid(row=0, column=1, padx=10, pady=5)

        Label(self.proportions_tab, text="X:").grid(row=1, column=0, padx=10, pady=5)
        self.x_entry = Entry(self.proportions_tab, width=10)
        self.x_entry.grid(row=1, column=1, padx=10, pady=5)

        Label(self.proportions_tab, text="Y:").grid(row=2, column=0, padx=10, pady=5)
        self.y_entry = Entry(self.proportions_tab, width=10)
        self.y_entry.grid(row=2, column=1, padx=10, pady=5)

        Label(self.proportions_tab, text="W:").grid(row=3, column=0, padx=10, pady=5)
        self.w_entry = Entry(self.proportions_tab, width=10)
        self.w_entry.grid(row=3, column=1, padx=10, pady=5)

        Label(self.proportions_tab, text="H:").grid(row=4, column=0, padx=10, pady=5)
        self.h_entry = Entry(self.proportions_tab, width=10)
        self.h_entry.grid(row=4, column=1, padx=10, pady=5)

        Button(self.proportions_tab, text="Zapisz", command=self.save_changes).grid(row=5, column=0, padx=10, pady=10)
        Button(self.proportions_tab, text="Podgląd", command=self.update_proportions).grid(row=5, column=1, padx=10, pady=10)

    def create_settings_tab(self):
        """Zakładka ustawień."""
        Label(self.settings_tab, text="Ustawienia Config.txt").pack(pady=10)

        self.config_text = Text(self.settings_tab, height=20, width=80)
        self.config_text.pack(padx=10, pady=10)

        self.proporcje_button = Button(
            self.settings_tab,
            text="Pokaż Proporcje",
            command=self.toggle_proporcje,
        )
        self.proporcje_button.pack(pady=10)

        Button(
            self.settings_tab,
            text="Zapisz Zmiany",
            command=self.save_changes,
        ).pack(pady=5)

        Button(
            self.settings_tab,
            text="Wybierz Nową Ścieżkę",
            command=self.select_new_path,
        ).pack(pady=5)

        self.load_config_file()

    def create_keyboard_tab(self):
        """Zakładka klawiatury."""
        Label(self.keyboard_tab, text="Mapowanie klawiatury").pack(pady=10)

        # Obraz klawiatury
        self.keyboard_image = PhotoImage(file="keyboard_placeholder.png")  # Wstaw swój obraz
        Label(self.keyboard_tab, image=self.keyboard_image).pack(side="right", padx=10)

        # Lista funkcji do mapowania
        Label(self.keyboard_tab, text="Funkcje:").pack(side="left", anchor="n", pady=10, padx=10)
        self.function_list = Text(self.keyboard_tab, height=20, width=30)
        self.function_list.pack(side="left", padx=10)

    def create_pad_tab(self):
        """Zakładka pada z konfiguracją z pad.json i obrazem pada."""
        # Główna ramka dla całej zakładki
        main_frame = ttk.Frame(self.pad_tab)
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # Ramka dla funkcji i wyboru
        function_frame = ttk.Frame(main_frame)
        function_frame.pack(side="left", expand=True, fill="both", padx=10, pady=10)

        # Ramka dla obrazu pada
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(side="right", padx=10, pady=10)

        # Wczytaj obraz pada
        self.pad_image = PhotoImage(file="pad_image.png")
        pad_image_label = Label(image_frame, image=self.pad_image)
        pad_image_label.pack()

        # Wczytaj konfigurację pada
        pad_config = padjsonop() or {}
        
        # Lista dostępnych przycisków z JSONa
        available_buttons = list(pad_config.keys())

        # Lista funkcji do mapowania
        functions = [
            "next", "uspij", "x", "z", "speedup", "speeddown", 
            "pause", "skipauto", "nextauto", "skipnij", "rskipnij", 
            "ekranl", "ekranp", 
            "nextend","on_quit2"
        ]

        # Nagłówki
        ttk.Label(function_frame, text="Funkcja", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(function_frame, text="Aktualny Przycisk", font=('Helvetica', 10, 'bold')).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(function_frame, text="Nowy Przycisk", font=('Helvetica', 10, 'bold')).grid(row=0, column=2, padx=5, pady=5)

        # Słownik do przechowywania aktualnych przypisań i kontrolek
        self.pad_mappings = {}
        self.pad_button_vars = {}

        # Dynamiczne tworzenie wierszy dla każdej funkcji
        for i, function in enumerate(functions, 1):
            # Etykieta funkcji
            ttk.Label(function_frame, text=function).grid(row=i, column=0, padx=5, pady=2)

            # Znajdź aktualnie przypisany przycisk dla funkcji
            current_button = ""
            for btn, func in pad_config.items():
                if func == function:
                    current_button = btn
                    break

            # Etykieta aktualnego przycisku
            current_button_label = ttk.Label(function_frame, text=current_button or "Nie przypisano")
            current_button_label.grid(row=i, column=1, padx=5, pady=2)

            # Lista rozwijana do wyboru przycisku
            button_var = StringVar()
            button_dropdown = ttk.Combobox(function_frame, textvariable=button_var, values=available_buttons, width=10, state="readonly")
            button_dropdown.grid(row=i, column=2, padx=5, pady=2)

            # Domyślnie wybierz aktualny przycisk
            if current_button:
                button_var.set(current_button)

            # Przechowujemy referencje
            self.pad_mappings[function] = current_button_label
            self.pad_button_vars[function] = button_var

        # Funkcja zapisu mapowania
        def save_pad_mapping():
            try:
                # Wczytaj aktualną konfigurację
                pad_config = padjsonop() or {}

                # Wyczyść poprzednie mapowania funkcji
                for btn in pad_config:
                    pad_config[btn] = ""

                # Zaktualizuj konfigurację nowymi wartościami
                for function, button_var in self.pad_button_vars.items():
                    selected_button = button_var.get()
                    if selected_button:
                        pad_config[selected_button] = function

                # Zapisz do pliku JSON
                with open(Pad_FILE, "w") as f:
                    json.dump(pad_config, f, indent=4)

                # Odśwież widok aktualnych przycisków
                for function, label in self.pad_mappings.items():
                    current_button = ""
                    for btn, func in pad_config.items():
                        if func == function:
                            current_button = btn
                            break
                    label.config(text=current_button or "Nie przypisano")

                messagebox.showinfo("Sukces", "Mapowanie pada zostało zaktualizowane!")

            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się zapisać mapowania: {e}")

        # Ramka dla przycisku Zapisz
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Zapisz", command=save_pad_mapping).pack()
    def toggle_proporcje(self):
        """Przełącza między widokiem przed i po #proporcje w config.txt."""
        if not self.config_path:
            showerror("Błąd", "Nie wybrano żadnej ścieżki!")
            return

        before_proporcje, after_proporcje = read_config_sections(self.config_path)
        if before_proporcje is None:
            showerror("Błąd", "Nie znaleziono pliku config.txt!")
            return

        self.proporcje_mode = not self.proporcje_mode
        self.proporcje_button.config(
            text="Pokaż Ustawienia" if self.proporcje_mode else "Pokaż Proporcje"
        )

        if self.proporcje_mode:
            # Wyświetlamy zawartość od #proporcje w dół
            self.update_config_text(after_proporcje)
        else:
            # Wyświetlamy zawartość od początku do #proporcje
            self.update_config_text(before_proporcje)

    def update_config_text(self, lines):
        """Aktualizuje zawartość pola tekstowego."""
        self.config_text.delete(1.0, "end")
        self.config_text.insert(1.0, "".join(lines))

    def load_config_file(self):
        """Ładuje zawartość pliku config.txt (domyślnie przed #proporcje)."""
        if self.config_path:
            before_proporcje, _ = read_config_sections(self.config_path)
            if before_proporcje:
                self.update_config_text(before_proporcje)
            else:
                showerror("Błąd", "Nie znaleziono sekcji ustawień w config.txt!")
        else:
            showerror("Błąd", "Nie wybrano żadnej ścieżki!")
    def load_selected(self, _=None):
        """Ładuje wybraną konfigurację proporcji."""
        selection = self.config_var.get()
        if selection in self.proportions_config:
            proportions = self.proportions_config[selection]
            self.x_entry.delete(0, "end")
            self.y_entry.delete(0, "end")
            self.w_entry.delete(0, "end")
            self.h_entry.delete(0, "end")
            self.x_entry.insert(0, proportions[0])
            self.y_entry.insert(0, proportions[1])
            self.w_entry.insert(0, proportions[2])
            self.h_entry.insert(0, proportions[3])

    def save_changes(self):
        """Zapisuje zmiany tylko dla wybranej konfiguracji proporcji."""
        if not self.config_path:
            showerror("Błąd", "Nie wybrano żadnej ścieżki!")
            return

        try:
            # Pobieramy zmodyfikowane proporcje z pól tekstowych
            def safe_float_convert(value):
                try:
                    cleaned_value = value.strip().replace(',', '.')
                    return float(cleaned_value)
                except (ValueError, TypeError):
                    print(f"Błąd konwersji wartości: {value}")
                    return 0.0  # Domyślna wartość w razie błędu

            x = safe_float_convert(self.x_entry.get())
            y = safe_float_convert(self.y_entry.get())
            w = safe_float_convert(self.w_entry.get())
            h = safe_float_convert(self.h_entry.get())
            
            selection = self.config_var.get()

            # Zaktualizuj tylko wybrane proporcje w słowniku
            if selection in self.proportions_config:
                self.proportions_config[selection] = [x, y, w, h]
            else:
                showerror("Błąd", f"Wybrana konfiguracja '{selection}' nie istnieje!")
                return

            # Zapisz tylko wybraną konfigurację proporcji
            def save_selected_proportion(config, selection):
                try:
                    with open(PROPORTIONS_FILE, "r+") as file:
                        lines = file.readlines()
                        file.seek(0)
                        inside_proportions_section = False

                        for line in lines:
                            if line.strip() == "#proporcje":
                                inside_proportions_section = True
                            if inside_proportions_section and line.startswith(selection):
                                # Znaleziono wybraną konfigurację, nadpisujemy ją
                                formatted_proportions = ", ".join([f"{p:.3f}" for p in config[selection]])  # Zaokrąglamy do 3 miejsc po przecinku
                                file.write(f"{selection} = {formatted_proportions}\n")
                                print(f"Zaktualizowano proporcje: {selection} = {formatted_proportions}")
                                inside_proportions_section = False  # Koniec sekcji proporcji
                            else:
                                file.write(line)

                        # Jeśli sekcja proporcji nie została zakończona, zakończ ją
                        if inside_proportions_section:
                            file.write("\n")

                except Exception as e:
                    print(f"Błąd przy zapisywaniu pliku proporcji: {e}")
                    showerror("Błąd", f"Błąd przy zapisywaniu pliku proporcji: {e}")

            # Wywołanie funkcji zapisującej wybraną konfigurację
            save_selected_proportion(self.proportions_config, selection)
            
            showinfo("Sukces", "Zmiany zostały zapisane!")

        except Exception as e:
            print(f"Błąd podczas zapisu: {e}")
            showerror("Błąd", f"Wystąpił błąd podczas zapisu: {e}")
    def update_proportions(self):
        """Aktualizuje proporcje i uruchamia podgląd."""
        global preview_thread
        try:
            x = float(self.x_entry.get())
            y = float(self.y_entry.get())
            w = float(self.w_entry.get())
            h = float(self.h_entry.get())

            if preview_thread and preview_thread.is_alive():
                stop_preview()
                preview_thread.join()

            preview_thread = threading.Thread(
                target=preview_changes,
                args=([x, y, w, h], self.screen_width, self.screen_height),
            )
            preview_thread.start()
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowe wartości!")
    def select_new_path(self):
        """Pozwala użytkownikowi wybrać nową ścieżkę do config.txt i zapisuje ją do config.json."""
        path = filedialog.askdirectory(title="Wybierz ścieżkę do config.txt")
        if path:  # Jeśli użytkownik wybierze ścieżkę
            save_config(path)  # Zapisujemy nową ścieżkę w pliku config.json
            self.config_path = path  # Aktualizujemy ścieżkę w aplikacji
            self.load_config_file()  # Ładujemy nową zawartość config.txt

if __name__ == "__main__":
    root = Tk()
    app = App(root)
    root.mainloop()
