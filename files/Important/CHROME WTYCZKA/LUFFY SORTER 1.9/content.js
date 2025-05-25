// Domyślne ustawienia sortowania
let currentServiceOrder = [
    "Mp4upload", "Dood", "Cda", "Mega", "Sibnet", "Gdrive", "Dailymotion", "Aparat",
    "Crunchyroll", "Vk", "Supervideo", "Default", "Lulustream", "Hqq", "Yourupload", "Pixeldrain"
];
function loadStorageData() {
    return new Promise((resolve) => {
        chrome.storage.local.get([
            'serviceOrder',
            'servicePriorities',
            'sortingHierarchy',
            'enableFiltering',
            'minPriorityToShow'
        ], function(result) {
            if (result.serviceOrder && result.serviceOrder.length > 0) {
                currentServiceOrder = result.serviceOrder;
            }
            if (result.servicePriorities && Object.keys(result.servicePriorities).length > 0) {
                servicePriorities = result.servicePriorities;
            }
            if (result.sortingHierarchy && result.sortingHierarchy.length > 0) {
                sortingHierarchy = result.sortingHierarchy;
            }
            if (result.enableFiltering !== undefined) {
                enableFiltering = result.enableFiltering;
            }
            if (result.minPriorityToShow !== undefined) {
                minPriorityToShow = result.minPriorityToShow;
            }
            console.log("Dane załadowane z chrome.storage:", result);
            resolve();
        });
    });
}
// Domyślne priorytety dla serwisów
let servicePriorities = {
    "Mp4upload": 9,
    "Dood": 9,
    "Cda": 8,
    "Mega": 9,
    "Sibnet": 7,
    "Gdrive": 5,
    "Dailymotion": 4,
    "Aparat": 4,
    "Crunchyroll": 4,
    "Vk": 3,
    "Supervideo": 3,
    "Default": 2,
    "Lulustream": 2,
    "Hqq": 1,
    "Yourupload": 1,
    "Pixeldrain": 1
};

let sortingHierarchy = ["subtitle", "language", "player", "quality", "date"];
let enableFiltering = false; // Domyślnie filtrowanie jest wyłączone
let minPriorityToShow = 5;   // Minimalna wartość priorytetu do wyświetlenia playera

function initSorter() {
    // Nasłuchuj wiadomości o aktualizacji ustawień
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.type === 'serviceOrderUpdated') {
            currentServiceOrder = message.order;
            sortAndFilterTable();
        } else if (message.type === 'settingsUpdated') {
            currentServiceOrder = message.serviceOrder;
            servicePriorities = message.servicePriorities;
            sortingHierarchy = message.sortingHierarchy;

            if (message.enableFiltering !== undefined) {
                enableFiltering = message.enableFiltering;
            }
            if (message.minPriorityToShow !== undefined) {
                minPriorityToShow = message.minPriorityToShow;
            }
            sortAndFilterTable();
        }
    });

    // Pobierz wszystkie ustawienia z chrome.storage
    chrome.storage.local.get([
        'serviceOrder',
        'servicePriorities',
        'sortingHierarchy',
        'enableFiltering',
        'minPriorityToShow'
    ], function(result) {
        if (result.serviceOrder && result.serviceOrder.length > 0) {
            currentServiceOrder = result.serviceOrder;
        }
        if (result.servicePriorities && Object.keys(result.servicePriorities).length > 0) {
            servicePriorities = result.servicePriorities;
        }
        if (result.sortingHierarchy && result.sortingHierarchy.length > 0) {
            sortingHierarchy = result.sortingHierarchy;
        }
        if (result.enableFiltering !== undefined) {
            enableFiltering = result.enableFiltering;
        }
        if (result.minPriorityToShow !== undefined) {
            minPriorityToShow = result.minPriorityToShow;
        }
        sortAndFilterTable(); // Sortowanie i filtrowanie po ustawieniu wszystkich parametrów
    });

    function compareService(aService, bService) {
        // Uwzględnij priorytety playerów
        const aPriority = servicePriorities[aService] || 0;
        const bPriority = servicePriorities[bService] || 0;

        if (aPriority !== bPriority) {
            return bPriority - aPriority; // Wyższy priorytet numeryczny ma pierwszeństwo
        }

        // Sortuj według domyślnej kolejności
        if (!currentServiceOrder) {
            return aService.localeCompare(bService);
        }

        const aIndex = currentServiceOrder.indexOf(aService);
        const bIndex = currentServiceOrder.indexOf(bService);

        if (aIndex === -1 && bIndex === -1) {
            return aService.localeCompare(bService);
        } else if (aIndex === -1) {
            return 1;
        } else if (bIndex === -1) {
            return -1;
        }

        return aIndex - bIndex;
    }

    function compareQuality(aQuality, bQuality) {
        const qualityOrder = ["1080p", "720p", "480p"];
        const aIndex = qualityOrder.indexOf(aQuality);
        const bIndex = qualityOrder.indexOf(bQuality);

        return aIndex - bIndex;
    }

    function compareLanguage(aLanguage, bLanguage) {
        const languageOrder = ["Japoński", "Chiński", "Angielski", "Polski", "Polski Maszynowy"];
        const aIndex = languageOrder.indexOf(aLanguage);
        const bIndex = languageOrder.indexOf(bLanguage);

        return aIndex - bIndex;
    }

    function compareSubtitle(aSubtitle, bSubtitle) {
        const subtitleOrder = ["Polski", "Polski Maszynowy", "Angielski", "--"];
        const aIndex = subtitleOrder.indexOf(aSubtitle);
        const bIndex = subtitleOrder.indexOf(bSubtitle);

        return aIndex - bIndex;
    }

    function compareDate(aDate, bDate) {
        const dateA = new Date(aDate);
        const dateB = new Date(bDate);

        return dateB - dateA;
    }

    // Funkcja filtrująca wiersze z niewystarczającym priorytetem
    function filterRowsByPriority(rows) {
        if (!enableFiltering) {
            return rows; // Jeśli filtrowanie jest wyłączone, zwróć wszystkie wiersze
        }
        
        return rows.filter(row => {
            const service = row.querySelector('.ep-pl-name').textContent.trim();
            const priority = servicePriorities[service] || 0;
            return priority >= minPriorityToShow;
        });
    }

    // Główna funkcja sortowania i filtrowania wykorzystująca hierarchię sortowania
    async function sortAndFilterTable() {
        const table = document.querySelector('table.data-view-table-strips');
        if (table) {
            const rows = Array.from(table.querySelectorAll('tbody > tr'));
            
            // Najpierw filtruj wiersze jeśli filtrowanie jest włączone
            const filteredRows = filterRowsByPriority(rows);

            filteredRows.sort((a, b) => {
                // Sortuj zgodnie z hierarchią
                for (const criterion of sortingHierarchy) {
                    let comparison = 0;

                    switch (criterion) {
                        case 'player':
                            const aService = a.querySelector('.ep-pl-name').textContent.trim();
                            const bService = b.querySelector('.ep-pl-name').textContent.trim();
                            comparison = compareService(aService, bService);
                            break;
                        case 'quality':
                            const aQuality = a.querySelector('.ep-pl-res').textContent.trim();
                            const bQuality = b.querySelector('.ep-pl-res').textContent.trim();
                            comparison = compareQuality(aQuality, bQuality);
                            break;
                        case 'language':
                            const aLanguage = a.querySelector('.ep-pl-alang > span.mobile-hidden').textContent.trim();
                            const bLanguage = b.querySelector('.ep-pl-alang > span.mobile-hidden').textContent.trim();
                            comparison = compareLanguage(aLanguage, bLanguage);
                            break;
                        case 'subtitle':
                            const aSubtitle = a.querySelector('.ep-pl-slang > span.mobile-hidden').textContent.trim();
                            const bSubtitle = b.querySelector('.ep-pl-slang > span.mobile-hidden').textContent.trim();
                            comparison = compareSubtitle(aSubtitle, bSubtitle);
                            break;
                        case 'date':
                            const aDate = a.querySelector('.ep-online-added').textContent.trim();
                            const bDate = b.querySelector('.ep-online-added').textContent.trim();
                            comparison = compareDate(aDate, bDate);
                            break;
                    }

                    if (comparison !== 0) {
                        return comparison;
                    }
                }

                return 0; // Jeśli wszystkie kryteria są równe
            });

            const tbody = table.querySelector('tbody');
            tbody.innerHTML = '';

            chrome.storage.sync.get(['visibleRows'], function(result) {
                const visibleRows = result.visibleRows || 2;
                
                // Tutaj możesz ograniczyć liczbę widocznych wierszy lub pokazać wszystkie posortowane i przefiltrowane
                filteredRows.forEach((row, index) => {
                    row.style.display = index < visibleRows ? '' : 'none';
                    tbody.appendChild(row);
                });
            });
        }
    }

    function displayX() {
        const overlay = document.createElement('div');
        overlay.style.position = 'fixed';
        overlay.style.top = '10px';
        overlay.style.right = '10px';
        overlay.style.width = '50px';
        overlay.style.height = '50px';
        overlay.style.backgroundColor = 'green';
        overlay.style.zIndex = '9999';
        overlay.style.display = 'flex';
        overlay.style.justifyContent = 'center';
        overlay.style.alignItems = 'center';
        overlay.style.borderRadius = '5px';
        overlay.style.cursor = 'pointer';
        overlay.title = "Wtyczka sortująca jest aktywna";

        const xElement = document.createElement('div');
        xElement.textContent = 'X';
        xElement.style.fontSize = '30px';
        xElement.style.color = 'white';

        overlay.appendChild(xElement);
        document.body.appendChild(overlay);

        function closeOverlay() {
            document.body.removeChild(overlay);
        }

        document.addEventListener('click', function(event) {
            if (!overlay.contains(event.target)) {
                closeOverlay();
            }
        });
    }
    loadStorageData().then(() => {
        sortAndFilterTable();
        displayX();
    });

    chrome.storage.onChanged.addListener(function(changes, namespace) {
        console.log("Wykryto zmiany w storage:", changes, "namespace:", namespace);
        
        if (namespace === 'sync' && changes.visibleRows) {
            loadStorageData().then(() => sortAndFilterTable());
        } else if (namespace === 'local' && (
            changes.serviceOrder || 
            changes.servicePriorities || 
            changes.sortingHierarchy || 
            changes.enableFiltering || 
            changes.minPriorityToShow
        )) {
            loadStorageData().then(() => sortAndFilterTable());
        }
    });
}

// Uruchomienie skryptu po załadowaniu strony
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSorter);
} else {
    initSorter();
}