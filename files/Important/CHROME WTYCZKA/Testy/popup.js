document.getElementById('saveSettings').addEventListener('click', function() {
    var visibleRows = document.getElementById('visibleRows').value;
    chrome.storage.sync.set({visibleRows: visibleRows}, function() {
        console.log('Settings saved');
        window.close();
    });
});

chrome.storage.sync.get(['visibleRows'], function(result) {
    document.getElementById('visibleRows').value = result.visibleRows || 4;
});