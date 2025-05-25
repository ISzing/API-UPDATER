from flask import Flask, send_from_directory, jsonify, request
import os
import hashlib
import logging
import time
import json

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('update_server.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
APP_FOLDER = "files"  # Folder z plikami aplikacji na serwerze

# Konfiguracja odporna na timeouty
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Wyłącz cache dla plików
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # Limit 100MB

# Zmienne do zarządzania manifestem
MANIFEST_CACHE = None
MANIFEST_CACHE_PATH = "manifest_cache.json"
LAST_MODIFIED_TIMES = {}

def file_hash(filepath):
    """Oblicza SHA256 dla pliku."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def check_for_changes():
    """Sprawdza, czy pliki w katalogu APP_FOLDER zostały zmienione od ostatniego generowania manifestu."""
    global LAST_MODIFIED_TIMES
    changes_detected = False
    current_files = {}
    
    # Przeszukaj wszystkie pliki w katalogu
    for root, _, files in os.walk(APP_FOLDER):
        for file in files:
            # Pomijaj pliki manifestu i inne pliki systemowe
            if file == "manifest.json" or file.startswith("."):
                continue
            
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, APP_FOLDER)
            mtime = os.path.getmtime(full_path)
            
            # Zapisz aktualny czas modyfikacji
            current_files[rel_path] = mtime
            
            # Sprawdź, czy plik jest nowy lub zmodyfikowany
            if rel_path not in LAST_MODIFIED_TIMES or LAST_MODIFIED_TIMES[rel_path] != mtime:
                logger.info(f"Wykryto zmianę w pliku: {rel_path}")
                changes_detected = True
    
    # Sprawdź, czy jakieś pliki zostały usunięte
    for old_file in LAST_MODIFIED_TIMES:
        if old_file not in current_files:
            logger.info(f"Wykryto usunięcie pliku: {old_file}")
            changes_detected = True
    
    # Aktualizuj słownik czasów modyfikacji
    if changes_detected:
        LAST_MODIFIED_TIMES = current_files
    
    return changes_detected

def load_cached_manifest():
    """Ładuje buforowany manifest z pliku, jeśli istnieje."""
    global MANIFEST_CACHE, LAST_MODIFIED_TIMES
    
    if os.path.exists(MANIFEST_CACHE_PATH):
        try:
            with open(MANIFEST_CACHE_PATH, 'r') as f:
                cache_data = json.load(f)
                MANIFEST_CACHE = cache_data['manifest']
                LAST_MODIFIED_TIMES = cache_data['file_times']
                logger.info(f"Załadowano buforowany manifest z {len(MANIFEST_CACHE['files'])} plikami")
                return True
        except Exception as e:
            logger.warning(f"Błąd ładowania buforowanego manifestu: {str(e)}")
    
    logger.info("Buforowany manifest nie istnieje lub nie jest poprawny")
    return False

def save_cached_manifest(manifest):
    """Zapisuje manifest i czasy modyfikacji plików do bufora."""
    try:
        with open(MANIFEST_CACHE_PATH, 'w') as f:
            json.dump({
                'manifest': manifest,
                'file_times': LAST_MODIFIED_TIMES
            }, f)
        logger.info(f"Zapisano buforowany manifest z {len(manifest['files'])} plikami")
    except Exception as e:
        logger.error(f"Błąd podczas zapisywania buforowanego manifestu: {str(e)}")

def generate_manifest():
    """Generuje manifest zawierający informacje o wszystkich plikach."""
    manifest = {"version": "1.0.0", "files": []}
    
    # Lista folderów do przeszukania - upewnij się, że zawiera build
    folders_to_check = [APP_FOLDER]
    build_folder = os.path.join(APP_FOLDER, "build")
    
    if os.path.exists(build_folder) and os.path.isdir(build_folder):
        logger.info(f"Dodaję pliki z folderu build: {build_folder}")
    
    # Przeszukaj wszystkie foldery
    for folder in folders_to_check:
        for root, dirs, files in os.walk(folder):
            for file in files:
                # Pomijaj pliki manifestu i inne pliki systemowe
                if file == "manifest.json" or file.startswith("."):
                    continue
                
                full_path = os.path.join(root, file)
                # Oblicz relatywną ścieżkę względem głównego folderu
                rel_path = os.path.relpath(full_path, APP_FOLDER)
                file_hash_value = file_hash(full_path)
                
                logger.debug(f"Dodaję do manifestu: {rel_path}")
                
                manifest["files"].append({
                    "path": rel_path,
                    "hash": file_hash_value,
                    "size": os.path.getsize(full_path)
                })
    
    # Sprawdź czy manifest nie jest pusty
    if not manifest["files"]:
        logger.warning("UWAGA: Manifest jest pusty! Sprawdź ścieżki folderów.")
    else:
        logger.info(f"Manifest zawiera {len(manifest['files'])} plików")
    
    # Zapisz nowy manifest do bufora
    save_cached_manifest(manifest)
    
    return manifest

def get_manifest():
    """Pobiera manifest, generując go tylko gdy wykryto zmiany."""
    global MANIFEST_CACHE
    
    # Jeśli manifest nie jest buforowany, załaduj go z pliku
    if MANIFEST_CACHE is None:
        load_cached_manifest()
    
    # Jeśli nadal jest None lub wykryto zmiany, wygeneruj nowy
    if MANIFEST_CACHE is None or check_for_changes():
        logger.info("Wykryto zmiany lub brak bufora - generowanie nowego manifestu")
        MANIFEST_CACHE = generate_manifest()
    else:
        logger.info("Używam buforowanego manifestu - brak zmian w plikach")
    
    return MANIFEST_CACHE

@app.route("/manifest.json")
def manifest():
    """Zwraca manifest z informacjami o plikach."""
    manifest_data = get_manifest()
    return jsonify(manifest_data)

@app.route("/hash/<path:filename>")
def get_hash(filename):
    """Zwraca hash pliku z obsługą podfolderów."""
    file_path = os.path.join(APP_FOLDER, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        logger.info(f"Generowanie hash dla pliku: {filename}")
        return file_hash(file_path)
    logger.error(f"Żądanie hash dla nieistniejącego pliku: {filename}")
    return "File not found", 404

@app.route("/<path:filename>")
def files(filename):
    """Obsługuje pobieranie plików z poprawioną obsługą połączeń i wsparciem dla podfolderów."""
    logger.info(f"Żądanie pliku: {filename}")
    
    # Sprawdź, czy plik istnieje
    file_path = os.path.join(APP_FOLDER, filename)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        logger.error(f"Plik nie istnieje: {file_path}")
        return f"Plik {filename} nie został znaleziony", 404
    
    try:
        # Określ folder bazowy i względną ścieżkę
        directory = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        
        # Jeśli plik jest w podfolderze (np. build)
        if directory != APP_FOLDER:
            # Użyj względnej ścieżki dla send_from_directory
            rel_directory = os.path.relpath(directory, APP_FOLDER)
            if rel_directory == '.':
                # Plik jest bezpośrednio w APP_FOLDER
                response = send_from_directory(APP_FOLDER, file_name)
            else:
                # Plik jest w podfolderze
                logger.info(f"Plik w podfolderze: {rel_directory}/{file_name}")
                response = send_from_directory(directory, file_name)
        else:
            # Standardowe zachowanie dla plików w głównym folderze
            response = send_from_directory(APP_FOLDER, file_name)
        
        # Ustaw nagłówki zwiększające stabilność połączenia
        response.headers["Connection"] = "keep-alive"
        response.headers["Keep-Alive"] = "timeout=120, max=1000"
        response.headers["X-Accel-Buffering"] = "no"  # Dla reverse proxy (np. Nginx)
        
        # Dodaj nagłówek content-length
        response.headers["Content-Length"] = str(os.path.getsize(file_path))
        
        logger.info(f"Wysyłanie pliku: {filename}, rozmiar: {response.headers['Content-Length']} bajtów")
        return response
    
    except Exception as e:
        logger.exception(f"Błąd podczas wysyłania pliku {filename}: {str(e)}")
        return f"Błąd podczas wysyłania pliku: {str(e)}", 500

@app.route("/")
def index():
    """Strona główna serwera."""
    return """
    <html>
        <head>
            <title>Serwer Aktualizacji</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                h1 { color: #333; }
                pre { background: #f4f4f4; padding: 15px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>Serwer Aktualizacji</h1>
            <p>Ten serwer służy do dystrybucji aktualizacji aplikacji.</p>
            <p>Dostępne endpointy:</p>
            <ul>
                <li><a href="/manifest.json">/manifest.json</a> - Lista dostępnych plików i ich hashe</li>
                <li><code>/hash/&lt;ścieżka&gt;</code> - Hash konkretnego pliku</li>
                <li><code>/&lt;ścieżka&gt;</code> - Pobieranie pliku</li>
            </ul>
        </body>
    </html>
    """

# Załaduj buforowany manifest przy starcie serwera
if __name__ == "__main__":
    # Spróbuj załadować buforowany manifest
    if not load_cached_manifest():
        # Jeśli nie istnieje, wygeneruj nowy
        logger.info("Generowanie początkowego manifestu...")
        MANIFEST_CACHE = generate_manifest()
    
    # Uruchom serwer
    app.run(host='0.0.0.0', threaded=True)
