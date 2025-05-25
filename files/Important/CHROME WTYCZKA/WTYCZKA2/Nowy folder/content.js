console.log("Wtyczka działa!");

// Domyślne ustawienia
let settings = {
    autoQuality: true,
    maxVolume: true,
    keyboardShortcuts: true,
    autoPlay: true
};

// Pobierz ustawienia przy starcie
chrome.storage.sync.get({
    autoQuality: true,
    maxVolume: true,
    keyboardShortcuts: true,
    autoPlay: true
}, function(items) {
    settings = items;
    console.log("Załadowane ustawienia:", settings);
});

// Nasłuchuj wiadomości z popup
chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
    if (message.action === 'settingsUpdated') {
        settings = message.settings;
        console.log("Zaktualizowano ustawienia:", settings);
    }
    return true;
});

function getEventListenersOnElement(element) {
    const events = {};
    const eventTypes = ['click', 'mousedown', 'mouseup', 'mousemove', 'touchstart', 'touchmove', 'touchend', 'input', 'change'];
    eventTypes.forEach(eventType => {
        const tempElement = document.createElement('div');
        let hasListener = false;
        tempElement.addEventListener(eventType, () => {
            hasListener = true;
        });
        element.dispatchEvent(new Event(eventType, { bubbles: true }));
        if (hasListener) {
            events[eventType] = true;
        }
    });
    return events;
}

function simulateClick(element) {
    if (element) {
        const events = ['mousedown', 'mouseup', 'click'];
        events.forEach(eventName => {
            const event = new MouseEvent(eventName, {
                view: window,
                bubbles: true,
                cancelable: true
            });
            element.dispatchEvent(event);
        });
    }
}

function unmuteSoundIfNeeded() {
    if (!settings.maxVolume) {
        console.log('Funkcja maksymalnej głośności wyłączona w ustawieniach');
        return Promise.resolve();
    }
    
    return new Promise((resolve) => {
        const muteButton = document.querySelector('.pb-volume-mute.pb-volume-mute-active');
        
        if (muteButton) {
            console.log('Wykryto wyciszony dźwięk, wyłączam wyciszenie...');
            
            // Symulujemy kliknięcie w przycisk wyciszenia aby go wyłączyć
            simulateClick(muteButton);
            
            // Dajemy czas na reakcję systemu
            setTimeout(async () => {
                // Po wyłączeniu wyciszenia, ustawiamy maksymalną głośność
                await setVolumeToMax();
                resolve();
            }, 300);
        } else {
            // Jeśli dźwięk nie jest wyciszony, po prostu ustawiamy maksymalną głośność
            setVolumeToMax().then(resolve);
        }
    });
}

function setVolumeToMax() {
    if (!settings.maxVolume) {
        console.log('Funkcja maksymalnej głośności wyłączona w ustawieniach');
        return Promise.resolve();
    }
    
    return new Promise((resolve) => {
        const volumeArea = document.querySelector('.pb-progress-bar-volume-area');
        const volumeBar = document.querySelector('.pb-progress-bar-volume');
        const volumeContainer = document.querySelector('.pb-volume');
        const videoElement = document.querySelector('video');
        
        // Zapisujemy stan odtwarzania
        const wasPlaying = videoElement && !videoElement.paused;
        const currentTime = videoElement ? videoElement.currentTime : 0;

        if (volumeArea && volumeBar) {
            console.log('Znaleziono elementy głośności, ustawiam...');

            const rect = volumeArea.getBoundingClientRect();
            
            // Sekwencja zdarzeń z opóźnieniami
            setTimeout(() => {
                const mousedown = new MouseEvent('mousedown', {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    clientX: rect.left,
                    clientY: rect.top + (rect.height / 2)
                });
                volumeArea.dispatchEvent(mousedown);

                setTimeout(() => {
                    const mousemove = new MouseEvent('mousemove', {
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        clientX: rect.left + (rect.width * 0.99),
                        clientY: rect.top + (rect.height / 2)
                    });
                    volumeArea.dispatchEvent(mousemove);

                    setTimeout(() => {
                        const mouseup = new MouseEvent('mouseup', {
                            bubbles: true,
                            cancelable: true,
                            view: window,
                            clientX: rect.left + (rect.width * 0.99),
                            clientY: rect.top + (rect.height / 2)
                        });
                        volumeArea.dispatchEvent(mouseup);
                        volumeBar.style.width = '99%';
                        volumeBar.setAttribute('data-click', 'none');

                        // Czekamy dodatkowe 200ms przed próbą wznowienia odtwarzania
                        setTimeout(() => {
                            if (wasPlaying && videoElement) {
                                videoElement.currentTime = currentTime;
                                videoElement.play().catch(error => {
                                    console.log('Błąd przy wznawianiu odtwarzania:', error);
                                });
                            }
                            resolve();
                        }, 200);
                    }, 50);
                }, 50);
            }, 50);
        } else {
            console.log('Nie znaleziono elementów kontroli głośności');
            resolve();
        }
    });
}

function addCustomCSS() {
    const style = document.createElement('style');
    style.innerHTML = `
        .box.episode-player-list .table-responsive {
            min-width: 1055px;
        }
    `;
    document.head.appendChild(style);
}

function autoPlayVideo() {
    if (!settings.autoPlay) {
        console.log('Funkcja automatycznego odtwarzania wyłączona w ustawieniach');
        return Promise.resolve();
    }
    
    return new Promise((resolve) => {
        const videoElement = document.querySelector('video');
        const playButton = document.querySelector('.pb-play-pause') || 
                            document.querySelector('.play-button') || 
                            document.querySelector('.vjs-play-control') ||
                            document.querySelector('[aria-label="Play"]') ||
                            document.querySelector('[title="Play"]');
        
        if (videoElement) {
            console.log('Włączam automatyczne odtwarzanie wideo...');
            
            // Próba bezpośredniego odtworzenia wideo
            videoElement.play().then(() => {
                console.log('Automatyczne odtwarzanie uruchomione');
                resolve();
            }).catch(error => {
                console.log('Nie udało się automatycznie odtworzyć, próbuję przycisk odtwarzania:', error);
                
                // Jeśli bezpośrednie odtwarzanie nie zadziałało, próbujemy kliknąć przycisk odtwarzania
                if (playButton) {
                    console.log('Znaleziono przycisk odtwarzania, klikam...');
                    simulateClick(playButton);
                    setTimeout(resolve, 500);
                } else {
                    console.log('Nie znaleziono przycisku odtwarzania');
                    resolve();
                }
            });
        } else {
            console.log('Nie znaleziono elementu wideo');
            resolve();
        }
    });
}

addCustomCSS();

function selectQuality(retryCount = 0) {
    if (!settings.autoQuality) {
        console.log('Funkcja automatycznej jakości wyłączona w ustawieniach');
        return;
    }
    
    const maxRetries = 5;
    const settingsButton = document.querySelector('.pb-settings-click');
    
    if (!settingsButton) {
        if (retryCount < maxRetries) {
            console.log(`Próba ${retryCount + 1}/${maxRetries} znalezienia przycisku ustawień...`);
            setTimeout(() => selectQuality(retryCount + 1), 1000);
        }
        return;
    }

    simulateClick(settingsButton);
    
    setTimeout(() => {
        const qualityOptions = {
            hd: document.querySelector('li[data-value="hd"] a'),
            sd: document.querySelector('li[data-value="sd"] a')
        };

        const selectedQuality = qualityOptions.hd || qualityOptions.sd;
        
        if (selectedQuality) {
            simulateClick(selectedQuality);
            
            // Czekamy na zastosowanie zmiany jakości
            setTimeout(async () => {
                if (settings.maxVolume) {
                    await unmuteSoundIfNeeded(); // Sprawdzamy i wyłączamy wyciszenie jeśli potrzeba
                }
                if (settings.autoPlay) {
                    await autoPlayVideo(); // Uruchamiamy automatyczne odtwarzanie
                }
            }, 1000);
        } else if (retryCount < maxRetries) {
            console.log(`Próba ${retryCount + 1}/${maxRetries} ustawienia jakości...`);
            setTimeout(() => selectQuality(retryCount + 1), 1000);
        }
    }, 500);
}

function setupVideoListener() {
    let videoElement = document.querySelector('video');
    
    if (!videoElement) {
        console.log('Oczekiwanie na pojawienie się elementu wideo...');
        setTimeout(setupVideoListener, 1000);
        return;
    }

    const videoEvents = ['loadeddata', 'loadedmetadata', 'canplay'];
    
    videoEvents.forEach(eventName => {
        videoElement.addEventListener(eventName, function handler() {
            console.log(`Zdarzenie ${eventName} wykryte`);
            
            // Uruchamiamy sekwencję czynności
            async function setupVideo() {
                if (settings.autoQuality) {
                    await selectQuality();
                } else {
                    if (settings.maxVolume) {
                        await unmuteSoundIfNeeded();
                    }
                    if (settings.autoPlay) {
                        await autoPlayVideo();
                    }
                }
            }
            
            setupVideo();
            
            videoEvents.forEach(e => videoElement.removeEventListener(e, handler));
        }, { once: true });
    });

    // Nasłuchiwanie klawiszy do przewijania
    document.addEventListener('keydown', function(event) {
        if (!videoElement || !settings.keyboardShortcuts) return;
        
        const timeSkips = {
            'x': 10,
            'z': -10,
            'e': 5,
            'q': -5
        };

        if (event.key in timeSkips) {
            videoElement.currentTime += timeSkips[event.key];
            console.log(`Przewinięto o ${Math.abs(timeSkips[event.key])} sekund ${timeSkips[event.key] > 0 ? 'do przodu' : 'do tyłu'}`);
        }
    });
}

// Próba automatycznego odtwarzania wideo bez czekania na zdarzenia wideo
setTimeout(() => {
    if (settings.autoPlay) {
        autoPlayVideo();
    }
}, 1500);

// Rozpocznij nasłuchiwanie po załadowaniu strony
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupVideoListener);
} else {
    setupVideoListener();
}

// Dodatkowe nasłuchiwanie zmian w DOM - na wypadek dynamicznie ładowanych elementów
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.addedNodes && mutation.addedNodes.length > 0) {
            for (let i = 0; i < mutation.addedNodes.length; i++) {
                const node = mutation.addedNodes[i];
                if (node.nodeName.toLowerCase() === 'video' || 
                    (node.nodeType === Node.ELEMENT_NODE && node.querySelector('video'))) {
                    console.log('Wykryto nowo dodany element wideo');
                    setTimeout(() => {
                        setupVideoListener();
                    }, 500);
                    break;
                }
            }
        }
    });
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});