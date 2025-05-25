let currentServiceOrder = null;

// Opóźnione ładowanie całej logiki o 300 ms
setTimeout(() => {
    // Nasłuchuj wiadomości o aktualizacji kolejności
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.type === 'serviceOrderUpdated') {
            currentServiceOrder = message.order;
            sortTable();
        }
    });

    // Pobierz początkową kolejność
    chrome.storage.local.get(['serviceOrder'], function(result) {
        currentServiceOrder = result.serviceOrder || [
            "Cda", "Mp4upload", "Sibnet", "Gdrive", "Dailymotion","Aparat",
            "Crunchyroll", "Vk", "Aparat", "Dood", "Mega", "Supervideo"
        ];
        sortTable();
    });

    function compareService(aService, bService) {
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

    async function sortTable() {
        const table = document.querySelector('table.data-view-table-strips');
        if (table) {
            const rows = Array.from(table.querySelectorAll('tbody > tr'));

            rows.sort((a, b) => {
                const aService = a.querySelector('.ep-pl-name').textContent.trim();
                const bService = b.querySelector('.ep-pl-name').textContent.trim();
                const serviceComparison = compareService(aService, bService);

                if (serviceComparison !== 0) return serviceComparison;

                const aLanguage = a.querySelector('.ep-pl-alang > span.mobile-hidden').textContent.trim();
                const bLanguage = b.querySelector('.ep-pl-alang > span.mobile-hidden').textContent.trim();
                const languageComparison = compareLanguage(aLanguage, bLanguage);

                if (languageComparison !== 0) return languageComparison;

                const aSubtitle = a.querySelector('.ep-pl-slang > span.mobile-hidden').textContent.trim();
                const bSubtitle = b.querySelector('.ep-pl-slang > span.mobile-hidden').textContent.trim();
                const subtitleComparison = compareSubtitle(aSubtitle, bSubtitle);

                if (subtitleComparison !== 0) return subtitleComparison;

                const aQuality = a.querySelector('.ep-pl-res').textContent.trim();
                const bQuality = b.querySelector('.ep-pl-res').textContent.trim();
                const qualityComparison = compareQuality(aQuality, bQuality);

                if (qualityComparison !== 0) return qualityComparison;

                const aDate = a.querySelector('.ep-online-added').textContent.trim();
                const bDate = b.querySelector('.ep-online-added').textContent.trim();
                return compareDate(aDate, bDate);
            });

            const tbody = table.querySelector('tbody');
            tbody.innerHTML = '';

            chrome.storage.sync.get(['visibleRows'], function(result) {
                const visibleRows = result.visibleRows || 4;

                rows.forEach((row, index) => {
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

    sortTable();
    displayX();

    chrome.storage.onChanged.addListener(function(changes, namespace) {
        if (namespace === 'sync' && (changes.visibleRows || changes.serviceOrder)) {
            sortTable();
        }
    });
}, 300); // Opóźnienie 300 ms