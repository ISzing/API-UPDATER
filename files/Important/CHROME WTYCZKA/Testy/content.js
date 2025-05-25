function compareService(aService, bService) {
  const serviceOrder = [
    "Mp4upload","Sibnet","Cda", "Gdrive","Dailymotion", 
    "Crunchyroll", "Vk", "Aparat", "Dood", "Mega", "Supervideo"
  ];

  const aIndex = serviceOrder.indexOf(aService);
  const bIndex = serviceOrder.indexOf(bService);

  if (aIndex === -1 && bIndex === -1) {
    return aService.localeCompare(bService); // Alfabetyczne sortowanie dla nieznanych usług
  } else if (aIndex === -1) {
    return 1; // Usługa A nieznana -> na koniec
  } else if (bIndex === -1) {
    return -1; // Usługa B nieznana -> na koniec
  }

  return aIndex - bIndex; // Sortowanie według indeksu w liście
}
function compareQuality(aQuality, bQuality) {
  const qualityOrder = ["1080p", "720p", "480p"];
  const aIndex = qualityOrder.indexOf(aQuality);
  const bIndex = qualityOrder.indexOf(bQuality);

  return aIndex - bIndex; // Indeksy w liście decydują o kolejności
}
function compareLanguage(aLanguage, bLanguage) {
  const languageOrder = ["Japoński", "Chiński", "Angielski", "Polski","Polski Maszynowy"];
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

  return dateB - dateA; // Od najnowszej do najstarszej
}
function sortTable() {
  const table = document.querySelector('table.data-view-table-strips');
  if (table) {
    const rows = Array.from(table.querySelectorAll('tbody > tr'));

    const sortedRows = rows.sort((a, b) => {
      // Pobierz dane z odpowiednich kolumn
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

    // Wyczyść tabelę
    table.querySelector('tbody').innerHTML = '';

    chrome.storage.sync.get(['visibleRows'], function(result) {
      const visibleRows = result.visibleRows || 4;

      // Dodaj posortowane wiersze z powrotem do tabeli i ukryj resztę
      sortedRows.forEach((row, index) => {
        if (index < visibleRows) {
          row.style.display = ''; // Upewnij się, że wiersze są widoczne
        } else {
          row.style.display = 'none'; // Ukryj pozostałe wiersze
        }
        table.querySelector('tbody').appendChild(row);
      });
    });
  }
}

function displayX() {
  // Tworzenie elementu div
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

  // Tworzenie elementu X
  const xElement = document.createElement('div');
  xElement.textContent = 'X';
  xElement.style.fontSize = '30px';
  xElement.style.color = 'white';

  // Dodanie X do tła
  overlay.appendChild(xElement);

  // Dodanie elementu do dokumentu
  document.body.appendChild(overlay);
  function closeOverlay() {
    document.body.removeChild(overlay);
}

// Obsługa kliknięcia na stronę, ale nie na X
document.addEventListener('click', function(event) {
    if (!overlay.contains(event.target)) {
        closeOverlay(); // Zamknij tło, jeśli kliknięto poza elementem overlay
    }
});
}
sortTable();
displayX();
// Nasłuchuj zmian w storage i ponownie sortuj tabelę
chrome.storage.onChanged.addListener(function(changes, namespace) {
  if (namespace === 'sync' && changes.visibleRows) {
    sortTable();
  }
});