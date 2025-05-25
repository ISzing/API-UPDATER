document.addEventListener('DOMContentLoaded', function() {
  // Pobierz ustawienia z pamięci przeglądarki i zaktualizuj interfejs
  chrome.storage.sync.get({
    autoQuality: true,
    maxVolume: true,
    keyboardShortcuts: true,
    autoPlay: true
  }, function(items) {
    document.getElementById('autoQuality').checked = items.autoQuality;
    document.getElementById('maxVolume').checked = items.maxVolume;
    document.getElementById('keyboardShortcuts').checked = items.keyboardShortcuts;
    document.getElementById('autoPlay').checked = items.autoPlay;
  });

  // Dodaj nasłuchiwanie zmian przełączników
  document.getElementById('autoQuality').addEventListener('change', saveSettings);
  document.getElementById('maxVolume').addEventListener('change', saveSettings);
  document.getElementById('keyboardShortcuts').addEventListener('change', saveSettings);
  document.getElementById('autoPlay').addEventListener('change', saveSettings);

  // Funkcja zapisująca ustawienia
  function saveSettings() {
    const settings = {
      autoQuality: document.getElementById('autoQuality').checked,
      maxVolume: document.getElementById('maxVolume').checked,
      keyboardShortcuts: document.getElementById('keyboardShortcuts').checked,
      autoPlay: document.getElementById('autoPlay').checked
    };
    
    // Zapisz ustawienia w pamięci przeglądarki
    chrome.storage.sync.set(settings, function() {
      console.log('Ustawienia zapisane');
      
      // Powiadom content script o zmianach
      chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        if (tabs[0]) {
          chrome.tabs.sendMessage(tabs[0].id, {
            action: 'settingsUpdated',
            settings: settings
          });
        }
      });
    });
  }
});