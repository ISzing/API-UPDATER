console.log("Wtyczka działa w Chrome!");

function simulateClick(element) {
    if (element) {
        element.focus(); // Focus przed kliknięciem
        ['mousedown', 'mouseup', 'click'].forEach(eventName => {
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
    return new Promise((resolve) => {
        const muteButton = document.querySelector('.pb-volume-mute.pb-volume-mute-active');
        if (muteButton) {
            console.log('Dźwięk jest wyciszony, wyłączam...');
            simulateClick(muteButton);
            setTimeout(() => {
                setVolumeToMax().then(resolve);
            }, 300);
        } else {
            setVolumeToMax().then(resolve);
        }
    });
}

function setVolumeToMax() {
    return new Promise((resolve) => {
        const volumeArea = document.querySelector('.pb-progress-bar-volume-area');
        const volumeBar = document.querySelector('.pb-progress-bar-volume');
        const videoElement = document.querySelector('video');
        
        if (videoElement) {
            videoElement.muted = false;
            videoElement.volume = 1.0;
        }

        if (volumeArea && volumeBar) {
            console.log('Ustawiam maksymalną głośność...');
            const rect = volumeArea.getBoundingClientRect();
            setTimeout(() => {
                ['mousedown', 'mousemove', 'mouseup'].forEach(eventName => {
                    const event = new MouseEvent(eventName, {
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        clientX: rect.left + (rect.width * 0.99),
                        clientY: rect.top + (rect.height / 2)
                    });
                    volumeArea.dispatchEvent(event);
                });
                volumeBar.style.width = '99%';
                resolve();
            }, 100);
        } else {
            console.log('Nie znaleziono suwaka głośności');
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

function selectQuality(retryCount = 0) {
    const maxRetries = 5;
    const settingsButton = document.querySelector('.pb-settings-click');
    
    if (!settingsButton) {
        if (retryCount < maxRetries) {
            console.log(`Próba ${retryCount + 1}/${maxRetries} znalezienia ustawień...`);
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
            setTimeout(() => unmuteSoundIfNeeded(), 1000);
        } else if (retryCount < maxRetries) {
            console.log(`Próba ${retryCount + 1}/${maxRetries} ustawienia jakości...`);
            setTimeout(() => selectQuality(retryCount + 1), 1000);
        }
    }, 500);
}

function setupVideoListener() {
    let videoElement = document.querySelector('video');
    if (!videoElement) {
        console.log('Oczekiwanie na element wideo...');
        setTimeout(setupVideoListener, 1000);
        return;
    }
    
    ['loadeddata', 'canplay'].forEach(eventName => {
        videoElement.addEventListener(eventName, function handler() {
            console.log(`Zdarzenie ${eventName} wykryte, ustawiam jakość...`);
            selectQuality();
            videoElement.removeEventListener(eventName, handler);
        }, { once: true });
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupVideoListener);
} else {
    setupVideoListener();
}
