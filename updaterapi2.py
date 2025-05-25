from flask import Flask, send_from_directory, jsonify, request, Response, stream_template
import os
import hashlib
import logging
import time
import json
import zipfile
import io
import gzip
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import threading

# Konfiguracja logowania z mniejszą ilością powiadomień
logging.basicConfig(
    level=logging.WARNING,  # Zmienione z INFO na WARNING
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('update_server.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
APP_FOLDER = "files"

# Konfiguracja zoptymalizowana pod Gunicorn
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 3600  # Cache na godzinę
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # Zwiększony limit do 500MB
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # Wyłącz pretty print dla JSON

# Zmienne globalne z thread-safe dostępem
MANIFEST_CACHE = None
MANIFEST_CACHE_PATH = "manifest_cache.json"
LAST_MODIFIED_TIMES = {}
CACHE_LOCK = threading.RLock()

# Konfiguracja grupowania plików
BATCH_SIZE = 50  # Pliki na paczkę
MAX_BATCH_SIZE_MB = 100  # Maksymalny rozmiar paczki w MB
FOLDER_COMPRESSION_THRESHOLD = 10  # Minimum plików w folderze do skompresowania

def file_hash_chunked(filepath, chunk_size=65536):
    """Oblicza SHA256 dla pliku w chunkach - bardziej wydajne dla dużych plików."""
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        logger.error(f"Błąd obliczania hash dla {filepath}: {str(e)}")
        return None

def get_folder_structure():
    """Analizuje strukturę folderów i grupuje pliki."""
    folder_structure = defaultdict(list)
    total_files = 0
    
    for root, _, files in os.walk(APP_FOLDER):
        if not files:
            continue
            
        # Pomijaj pliki systemowe
        filtered_files = [f for f in files if not f.startswith('.') and f != 'manifest.json']
        if not filtered_files:
            continue
            
        rel_root = os.path.relpath(root, APP_FOLDER)
        if rel_root == '.':
            rel_root = 'root'
            
        for file in filtered_files:
            full_path = os.path.join(root, file)
            try:
                size = os.path.getsize(full_path)
                folder_structure[rel_root].append({
                    'name': file,
                    'path': os.path.relpath(full_path, APP_FOLDER),
                    'size': size,
                    'full_path': full_path
                })
                total_files += 1
            except OSError:
                continue
    
    # Loguj tylko podsumowanie
    if total_files > 0:
        logger.info(f"Struktura: {len(folder_structure)} folderów, {total_files} plików")
    
    return dict(folder_structure)

def create_folder_batches(folder_structure):
    """Tworzy paczki plików zoptymalizowane pod rozmiar i liczbę."""
    batches = []
    batch_id = 0
    
    for folder_name, files in folder_structure.items():
        if not files:
            continue
            
        # Sortuj pliki według rozmiaru (małe najpierw)
        files.sort(key=lambda x: x['size'])
        
        current_batch = []
        current_size = 0
        max_size_bytes = MAX_BATCH_SIZE_MB * 1024 * 1024
        
        for file_info in files:
            file_size = file_info['size']
            
            # Jeśli plik jest większy niż limit paczki, utwórz osobną paczkę
            if file_size > max_size_bytes:
                if current_batch:
                    batches.append({
                        'id': f"batch_{batch_id}",
                        'folder': folder_name,
                        'files': current_batch.copy(),
                        'total_size': current_size,
                        'type': 'mixed'
                    })
                    batch_id += 1
                    current_batch = []
                    current_size = 0
                
                batches.append({
                    'id': f"batch_{batch_id}",
                    'folder': folder_name,
                    'files': [file_info],
                    'total_size': file_size,
                    'type': 'large_single'
                })
                batch_id += 1
                continue
            
            # Sprawdź czy dodanie pliku nie przekroczy limitów
            if (current_size + file_size > max_size_bytes or 
                len(current_batch) >= BATCH_SIZE):
                
                if current_batch:
                    batches.append({
                        'id': f"batch_{batch_id}",
                        'folder': folder_name,
                        'files': current_batch.copy(),
                        'total_size': current_size,
                        'type': 'compressed' if len(current_batch) >= FOLDER_COMPRESSION_THRESHOLD else 'mixed'
                    })
                    batch_id += 1
                    current_batch = []
                    current_size = 0
            
            current_batch.append(file_info)
            current_size += file_size
        
        # Dodaj ostatnią paczkę jeśli nie jest pusta
        if current_batch:
            batches.append({
                'id': f"batch_{batch_id}",
                'folder': folder_name,
                'files': current_batch,
                'total_size': current_size,
                'type': 'compressed' if len(current_batch) >= FOLDER_COMPRESSION_THRESHOLD else 'mixed'
            })
            batch_id += 1
    
    return batches

def calculate_batch_hash(batch):
    """Oblicza hash dla całej paczki plików."""
    hasher = hashlib.sha256()
    
    # Sortuj pliki według ścieżki dla konsystentnego hashowania
    sorted_files = sorted(batch['files'], key=lambda x: x['path'])
    
    for file_info in sorted_files:
        file_hash = file_hash_chunked(file_info['full_path'])
        if file_hash:
            hasher.update(f"{file_info['path']}:{file_hash}".encode())
    
    return hasher.hexdigest()

def check_for_changes_optimized():
    """Zoptymalizowana kontrola zmian - sprawdza tylko czasy modyfikacji folderów."""
    global LAST_MODIFIED_TIMES
    changes_detected = False
    current_times = {}
    
    # Sprawdź czas modyfikacji głównych folderów
    for root, dirs, files in os.walk(APP_FOLDER):
        if files:  # Tylko foldery z plikami
            try:
                folder_mtime = max(os.path.getmtime(os.path.join(root, f)) 
                                 for f in files if not f.startswith('.'))
                rel_path = os.path.relpath(root, APP_FOLDER)
                current_times[rel_path] = folder_mtime
                
                if rel_path not in LAST_MODIFIED_TIMES or LAST_MODIFIED_TIMES[rel_path] != folder_mtime:
                    changes_detected = True
            except OSError:
                continue
    
    # Sprawdź usunięte foldery
    if set(LAST_MODIFIED_TIMES.keys()) != set(current_times.keys()):
        changes_detected = True
    
    if changes_detected:
        LAST_MODIFIED_TIMES = current_times
        logger.info("Wykryto zmiany w strukturze plików")
    
    return changes_detected

def generate_manifest_optimized():
    """Generuje zoptymalizowany manifest z paczkami plików."""
    folder_structure = get_folder_structure()
    batches = create_folder_batches(folder_structure)
    
    # Oblicz hashe dla paczek (równoległe przetwarzanie)
    with ThreadPoolExecutor(max_workers=4) as executor:
        hash_futures = {executor.submit(calculate_batch_hash, batch): batch for batch in batches}
        
        for future in hash_futures:
            batch = hash_futures[future]
            try:
                batch['hash'] = future.result(timeout=30)
            except Exception as e:
                logger.error(f"Błąd obliczania hash dla paczki {batch['id']}: {str(e)}")
                batch['hash'] = "error"
    
    manifest = {
        "version": "2.0.0",
        "optimization": "batched",
        "batches": batches,
        "total_batches": len(batches),
        "total_files": sum(len(batch['files']) for batch in batches),
        "total_size": sum(batch['total_size'] for batch in batches)
    }
    
    logger.info(f"Manifest: {len(batches)} paczek, {manifest['total_files']} plików, "
               f"{manifest['total_size']/(1024*1024):.1f}MB")
    
    return manifest

def get_manifest():
    """Thread-safe pobieranie manifestu."""
    global MANIFEST_CACHE
    
    with CACHE_LOCK:
        if MANIFEST_CACHE is None:
            load_cached_manifest()
        
        if MANIFEST_CACHE is None or check_for_changes_optimized():
            logger.info("Regeneracja manifestu...")
            MANIFEST_CACHE = generate_manifest_optimized()
            save_cached_manifest()
        
        return MANIFEST_CACHE

def load_cached_manifest():
    """Ładuje manifest z cache."""
    global MANIFEST_CACHE, LAST_MODIFIED_TIMES
    
    if os.path.exists(MANIFEST_CACHE_PATH):
        try:
            with open(MANIFEST_CACHE_PATH, 'r') as f:
                cache_data = json.load(f)
                MANIFEST_CACHE = cache_data['manifest']
                LAST_MODIFIED_TIMES = cache_data.get('file_times', {})
                return True
        except Exception as e:
            logger.warning(f"Błąd ładowania cache: {str(e)}")
    return False

def save_cached_manifest():
    """Zapisuje manifest do cache."""
    try:
        with open(MANIFEST_CACHE_PATH, 'w') as f:
            json.dump({
                'manifest': MANIFEST_CACHE,
                'file_times': LAST_MODIFIED_TIMES
            }, f, separators=(',', ':'))  # Kompaktowy JSON
    except Exception as e:
        logger.error(f"Błąd zapisu cache: {str(e)}")

@app.route("/manifest.json")
def manifest():
    """Zwraca zoptymalizowany manifest."""
    manifest_data = get_manifest()
    
    # Kompresja JSON dla dużych manifestów
    response = jsonify(manifest_data)
    if request.headers.get('Accept-Encoding', '').find('gzip') != -1:
        response.headers['Content-Encoding'] = 'gzip'
    
    return response

@app.route("/batch/<batch_id>")
def download_batch(batch_id):
    """Pobiera całą paczkę plików jako ZIP."""
    manifest_data = get_manifest()
    
    # Znajdź paczkę
    batch = None
    for b in manifest_data['batches']:
        if b['id'] == batch_id:
            batch = b
            break
    
    if not batch:
        return "Paczka nie znaleziona", 404
    
    def generate_zip():
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for file_info in batch['files']:
                try:
                    # Dodaj plik do ZIP z zachowaniem struktury folderów
                    arcname = file_info['path']
                    zf.write(file_info['full_path'], arcname)
                except Exception as e:
                    logger.error(f"Błąd dodawania {file_info['path']} do ZIP: {str(e)}")
                    continue
        
        zip_buffer.seek(0)
        return zip_buffer.read()
    
    try:
        zip_data = generate_zip()
        
        response = Response(
            zip_data,
            mimetype='application/zip',
            headers={'Content-Disposition': f'attachment; filename="{batch_id}.zip"'}
        )
        
        # Nagłówki optymalizujące transfer
        response.headers['Content-Length'] = str(len(zip_data))
        response.headers['Accept-Ranges'] = 'bytes'
        
        logger.info(f"Wysłano paczkę {batch_id}: {len(zip_data)} bajtów")
        return response
        
    except Exception as e:
        logger.error(f"Błąd generowania paczki {batch_id}: {str(e)}")
        return f"Błąd generowania paczki: {str(e)}", 500

@app.route("/file/<path:filename>")
def download_single_file(filename):
    """Pobiera pojedynczy plik (tylko dla kompatybilności wstecznej)."""
    file_path = os.path.join(APP_FOLDER, filename)
    
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return "Plik nie znaleziony", 404
    
    try:
        directory = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        
        response = send_from_directory(directory or APP_FOLDER, file_name)
        
        # Optymalizacja transferu
        response.headers["Content-Length"] = str(os.path.getsize(file_path))
        response.headers["Accept-Ranges"] = "bytes"
        
        return response
        
    except Exception as e:
        logger.error(f"Błąd wysyłania pliku {filename}: {str(e)}")
        return f"Błąd: {str(e)}", 500

@app.route("/health")
def health_check():
    """Endpoint zdrowia dla load balancera."""
    return {"status": "healthy", "cache_loaded": MANIFEST_CACHE is not None}

@app.route("/")
def index():
    """Strona główna z informacjami o API."""
    return """
    <html>
        <head>
            <title>Zoptymalizowany Serwer Aktualizacji v2.0</title>
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; line-height: 1.6; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
                .endpoint { background: #ecf0f1; padding: 10px; margin: 10px 0; border-radius: 5px; font-family: monospace; }
                .feature { background: #e8f5e8; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #27ae60; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Zoptymalizowany Serwer Aktualizacji v2.0</h1>
                
                <div class="feature">
                    <h3>✨ Nowe funkcje:</h3>
                    <ul>
                        <li><strong>Paczki plików</strong> - Grupowanie w ZIP zamiast pojedynczych plików</li>
                        <li><strong>Inteligentne cache'owanie</strong> - Minimalne przebudowy manifestu</li>
                        <li><strong>Kompresja</strong> - Automatyczna kompresja dużych paczek</li>
                        <li><strong>Równoległe przetwarzanie</strong> - Szybsze generowanie hashów</li>
                    </ul>
                </div>
                
                <h3>📡 Dostępne endpointy:</h3>
                <div class="endpoint">/manifest.json - Manifest z paczkami plików</div>
                <div class="endpoint">/batch/&lt;batch_id&gt; - Pobieranie paczki jako ZIP</div>
                <div class="endpoint">/file/&lt;path&gt; - Pojedynczy plik (legacy)</div>
                <div class="endpoint">/health - Status serwera</div>
                
                <p><em>Zoptymalizowane dla Gunicorn i dużych zbiorów plików</em></p>
            </div>
        </body>
    </html>
    """

# Inicjalizacja przy starcie
if __name__ == "__main__":
    logger.info("🚀 Uruchamianie zoptymalizowanego serwera...")
    
    # Załaduj cache przy starcie
    if not load_cached_manifest():
        logger.info("Generowanie początkowego manifestu...")
        with CACHE_LOCK:
            MANIFEST_CACHE = generate_manifest_optimized()
            save_cached_manifest()
    
    # Uruchom serwer zoptymalizowany pod Gunicorn
    app.run(host='0.0.0.0', threaded=True, debug=False)
