const defaultServiceOrder = [
    "Mp4upload", "Dood", "Cda","Mega","Sibnet", "Gdrive", "Dailymotion", "Aparat",
    "Crunchyroll", "Vk", "Supervideo","Default","Lulustream","Hqq","Yourupload","Pixeldrain"
];

// Added default priorities for services
const defaultServicePriorities = {
    "Mp4upload": 9,
    "Dood": 9,
    "Cda": 8,
    "Mega": 7,
    "Sibnet": 5,
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

const defaultHierarchy = ["subtitle","language","player","quality","date"];
const defaultEnableFiltering = false;
const defaultMinPriorityToShow = 5;

// Kolory dla priorytetow
function getPriorityColor(priority) {
    if (priority >= 8) return "high-priority";
    if (priority >= 5) return "medium-priority";
    return "normal-priority";
}

// Inicjalizacja interakcji dla kart
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            
            // Ukryj wszystkie zakladki i dezaktywuj przyciski
            tabContents.forEach(content => content.classList.remove('active'));
            tabButtons.forEach(btn => btn.classList.remove('active'));
            
            // Aktywuj wybrana zakladke i przycisk
            document.getElementById(`${tabId}-tab`).classList.add('active');
            button.classList.add('active');
        });
    });
}

// Inicjalizacja drag and drop dla list
function initializeDragAndDrop(listId, saveKey) {
    const list = document.getElementById(listId);
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

    list.addEventListener('dragover', handleDragOver);
    
    return {
        handleDragStart,
        handleDragEnd
    };
}

// Inicjalizacja listy playerow
function initializeServiceList() {
    const list = document.getElementById('serviceList');
    const { handleDragStart, handleDragEnd } = initializeDragAndDrop('serviceList', 'serviceOrder');
    
    chrome.storage.local.get(['serviceOrder', 'servicePriorities'], function(result) {
        const services = result.serviceOrder || defaultServiceOrder;
        const priorities = result.servicePriorities || defaultServicePriorities;
        
        list.innerHTML = ''; // Wyczysc istniejace elementy
        
        services.forEach(service => {
            const li = document.createElement('li');
            li.className = 'draggable-item';
            li.draggable = true;
            
            const serviceNameSpan = document.createElement('span');
            serviceNameSpan.textContent = service;
            
            const priorityDiv = document.createElement('div');
            priorityDiv.className = 'priority';
            
            const priorityIndicator = document.createElement('span');
            const priority = priorities[service] || defaultServicePriorities[service] || 5;
            priorityIndicator.className = `priority-indicator ${getPriorityColor(priority)}`;
            
            const priorityInput = document.createElement('input');
            priorityInput.type = 'number';
            priorityInput.min = 1;
            priorityInput.max = 10;
            priorityInput.value = priority;
            priorityInput.addEventListener('change', function() {
                priorityIndicator.className = `priority-indicator ${getPriorityColor(parseInt(this.value))}`;
            });
            
            priorityDiv.appendChild(priorityIndicator);
            priorityDiv.appendChild(priorityInput);
            
            li.appendChild(serviceNameSpan);
            li.appendChild(priorityDiv);
            
            li.addEventListener('dragstart', handleDragStart);
            li.addEventListener('dragend', handleDragEnd);
            
            list.appendChild(li);
        });
    });
}

// Inicjalizacja listy hierarchii
function initializeHierarchyList() {
    const list = document.getElementById('hierarchyList');
    const { handleDragStart, handleDragEnd } = initializeDragAndDrop('hierarchyList', 'sortingHierarchy');
    
    chrome.storage.local.get(['sortingHierarchy'], function(result) {
        const hierarchy = result.sortingHierarchy || defaultHierarchy;
        
        list.innerHTML = ''; // Wyczysc istniejace elementy
        
        const hierarchyLabels = {
            'player': 'Player',
            'quality': 'Jakosc',
            'language': 'Jezyk',
            'subtitle': 'Napisy',
            'date': 'Data dodania'
        };
        
        hierarchy.forEach(item => {
            const li = document.createElement('li');
            li.textContent = hierarchyLabels[item] || item;
            li.className = 'draggable-item';
            li.draggable = true;
            li.dataset.value = item;
            
            li.addEventListener('dragstart', handleDragStart);
            li.addEventListener('dragend', handleDragEnd);
            
            list.appendChild(li);
        });
    });
}

// Inicjalizacja sortowania
function initializeSortingOrder() {
    const container = document.getElementById('sortingOrder');
    
    chrome.storage.local.get(['sortingHierarchy'], function(result) {
        const hierarchy = result.sortingHierarchy || defaultHierarchy;
        
        container.innerHTML = ''; // Wyczysc istniejace elementy
        
        const hierarchyLabels = {
            'player': 'Player',
            'quality': 'Jakosc',
            'language': 'Jezyk',
            'subtitle': 'Napisy',
            'date': 'Data dodania'
        };
        
        hierarchy.forEach((item, index) => {
            const div = document.createElement('div');
            div.className = 'sorting-order-item';
            
            const label = document.createElement('span');
            label.textContent = `${index + 1}. ${hierarchyLabels[item] || item}`;
            
            div.appendChild(label);
            container.appendChild(div);
        });
    });
}

// Inicjalizacja filtrowania
function initializeFilteringOptions() {
    const enableFilteringCheckbox = document.getElementById('enableFiltering');
    const filteringOptionsDiv = document.getElementById('filteringOptions');
    const minPriorityInput = document.getElementById('minPriorityToShow');
    
    chrome.storage.local.get(['enableFiltering', 'minPriorityToShow'], function(result) {
        const enableFiltering = result.enableFiltering !== undefined ? result.enableFiltering : defaultEnableFiltering;
        const minPriority = result.minPriorityToShow !== undefined ? result.minPriorityToShow : defaultMinPriorityToShow;
        
        enableFilteringCheckbox.checked = enableFiltering;
        minPriorityInput.value = minPriority;
        
        filteringOptionsDiv.style.display = enableFiltering ? 'block' : 'none';
    });
    
    // Dodaj nasłuchiwanie zmiany stanu checkboxa
    enableFilteringCheckbox.addEventListener('change', function() {
        filteringOptionsDiv.style.display = this.checked ? 'block' : 'none';
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Inicjalizacja zakladek
    initializeTabs();
    
    // Inicjalizacja rożnych sekcji
    initializeServiceList();
    initializeHierarchyList();
    initializeSortingOrder();
    initializeFilteringOptions();
    
    // Pobierz zapisane wartosci dla podstawowych ustawien
    chrome.storage.sync.get(['visibleRows'], function(result) {
        document.getElementById('visibleRows').value = result.visibleRows || 2;
    });
    
    // Obsluga przycisku zapisu
    document.getElementById('saveSettings').addEventListener('click', function() {
        // Pobierz liczbe widocznych wierszy
        const visibleRows = document.getElementById('visibleRows').value;
        
        // Pobierz kolejnosc playerow i ich priorytety
        const serviceList = document.getElementById('serviceList');
        const services = Array.from(serviceList.children).map(item => {
            const serviceName = item.querySelector('span').textContent;
            const priority = parseInt(item.querySelector('input').value);
            return { name: serviceName, priority: priority };
        });
        
        const serviceOrder = services.map(s => s.name);
        const servicePriorities = services.reduce((acc, s) => {
            acc[s.name] = s.priority;
            return acc;
        }, {});
        
        // Pobierz hierarchie sortowania
        const hierarchyList = document.getElementById('hierarchyList');
        const sortingHierarchy = Array.from(hierarchyList.children).map(item => item.dataset.value);
        
        // Pobierz ustawienia filtrowania
        const enableFiltering = document.getElementById('enableFiltering').checked;
        const minPriorityToShow = parseInt(document.getElementById('minPriorityToShow').value);
        
        // Zapisz widoczne wierszy w sync storage
        chrome.storage.sync.set({ visibleRows: visibleRows });
        
        // Zapisz pozostale ustawienia w local storage
        chrome.storage.local.set({
            serviceOrder: serviceOrder,
            servicePriorities: servicePriorities,
            sortingHierarchy: sortingHierarchy,
            enableFiltering: enableFiltering,
            minPriorityToShow: minPriorityToShow
        }, function() {
            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                if (tabs[0]) {
                    chrome.tabs.sendMessage(tabs[0].id, { 
                        type: 'settingsUpdated',
                        serviceOrder: serviceOrder,
                        servicePriorities: servicePriorities,
                        sortingHierarchy: sortingHierarchy,
                        enableFiltering: enableFiltering,
                        minPriorityToShow: minPriorityToShow
                    });
                }
                // Powiadomienie o zapisie
                const savedNotification = document.createElement('div');
                savedNotification.textContent = 'Ustawienia zapisane!';
                savedNotification.style.position = 'fixed';
                savedNotification.style.bottom = '10px';
                savedNotification.style.left = '50%';
                savedNotification.style.transform = 'translateX(-50%)';
                savedNotification.style.backgroundColor = '#4CAF50';
                savedNotification.style.color = 'white';
                savedNotification.style.padding = '10px 20px';
                savedNotification.style.borderRadius = '5px';
                savedNotification.style.zIndex = '1000';
                
                document.body.appendChild(savedNotification);
                
                setTimeout(function() {
                    document.body.removeChild(savedNotification);
                }, 2000);
            });
        });
    });
});