const defaultServiceOrder = [
    "Cda", "Mp4upload", "Sibnet", "Gdrive", "Dailymotion",
    "Crunchyroll", "Vk", "Aparat", "Dood", "Mega", "Supervideo"
];

function initializeDragAndDrop() {
    const list = document.getElementById('serviceList');
    let draggedItem = null;

    function handleDragStart(e) {
        draggedItem = e.target;
        e.target.classList.add('dragging');
    }

    function handleDragEnd(e) {
        e.target.classList.remove('dragging');
        draggedItem = null;
    }

    function handleDragOver(e) {
        e.preventDefault();
        const afterElement = getDragAfterElement(list, e.clientY);
        const item = draggedItem;
        if (afterElement == null) {
            list.appendChild(item);
        } else {
            list.insertBefore(item, afterElement);
        }
    }

    function getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.draggable-item:not(.dragging)')]
        
        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    // Load current order and create list items
    chrome.storage.local.get(['serviceOrder'], function(result) {
        const services = result.serviceOrder || defaultServiceOrder;
        list.innerHTML = ''; // Clear existing items
        services.forEach(service => {
            const li = document.createElement('li');
            li.textContent = service;
            li.className = 'draggable-item';
            li.draggable = true;
            li.addEventListener('dragstart', handleDragStart);
            li.addEventListener('dragend', handleDragEnd);
            list.appendChild(li);
        });
    });

    list.addEventListener('dragover', handleDragOver);
}

document.addEventListener('DOMContentLoaded', function() {
    initializeDragAndDrop();
    
    chrome.storage.sync.get(['visibleRows'], function(result) {
        document.getElementById('visibleRows').value = result.visibleRows || 4;
    });
});

document.getElementById('saveSettings').addEventListener('click', function() {
    const visibleRows = document.getElementById('visibleRows').value;
    const serviceList = document.getElementById('serviceList');
    const newOrder = Array.from(serviceList.children).map(item => item.textContent);

    // Zapisz widoczne wiersze w sync storage
    chrome.storage.sync.set({ visibleRows: visibleRows });

    // Zapisz kolejność w local storage
    chrome.storage.local.set({ serviceOrder: newOrder }, function() {
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            if (tabs[0]) {
                chrome.tabs.sendMessage(tabs[0].id, { 
                    type: 'serviceOrderUpdated',
                    order: newOrder 
                });
            }
            window.close();
        });
    });
});
