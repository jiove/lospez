document.addEventListener('DOMContentLoaded', () => {
    // Elementi DOM
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-input');
    const uploadProgress = document.getElementById('upload-progress');
    const progressFill = document.querySelector('.progress-fill');
    const progressText = document.getElementById('progress-text');
    const resultsSection = document.getElementById('results-section');
    const scenesContainer = document.getElementById('scenes-container');
    const videoInfoContainer = document.getElementById('video-info');
    const downloadBtn = document.getElementById('download-btn');
    const downloadVideosBtn = document.getElementById('download-videos-btn');
    const sensitivitySlider = document.getElementById('sensitivity');
    const sensitivityValue = document.getElementById('sensitivity-value');
    const errorModal = document.getElementById('error-modal');
    const errorMessage = document.getElementById('error-message');
    const closeModal = document.querySelector('.close');
    const normalModeBtn = document.getElementById('normal-mode');
    const mode10sBtn = document.getElementById('mode-10s');

    // Variabili globali
    let currentResultId = null;
    let currentSensitivity = 30;
    let currentMode = 'normal'; // 'normal' o '10s'

    // Gestione dei pulsanti di modalità
    normalModeBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (!fileInput.files.length) {
            normalModeBtn.classList.add('active');
            mode10sBtn.classList.remove('active');
            currentMode = 'normal';
        } else {
            normalModeBtn.classList.add('active');
            mode10sBtn.classList.remove('active');
            currentMode = 'normal';
            handleFiles(fileInput.files[0]);
        }
    });

    mode10sBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (!fileInput.files.length) {
            mode10sBtn.classList.add('active');
            normalModeBtn.classList.remove('active');
            currentMode = '10s';
        } else {
            mode10sBtn.classList.add('active');
            normalModeBtn.classList.remove('active');
            currentMode = '10s';
            handleFiles(fileInput.files[0]);
        }
    });

    // Gestione del drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropArea.classList.add('highlight');
    }

    function unhighlight() {
        dropArea.classList.remove('highlight');
    }

    // Gestione del caricamento file
    dropArea.addEventListener('drop', handleDrop, false);
    fileInput.addEventListener('change', handleFileSelect, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            handleFiles(files[0]);
        }
    }
    
    function handleFileSelect(e) {
        const files = e.target.files;
        
        if (files.length > 0) {
            handleFiles(files[0]);
        }
    }
    
    function handleFiles(file) {
        // Controlla il tipo di file
        const validTypes = ['video/mp4', 'video/avi', 'video/quicktime'];
        if (!validTypes.includes(file.type)) {
            showError('Formato file non supportato. Formati supportati: MP4, AVI, MOV');
            return;
        }
        
        // Controlla la dimensione del file (max 500MB)
        if (file.size > 500 * 1024 * 1024) {
            showError('Il file è troppo grande. La dimensione massima è 500MB');
            return;
        }
        
        uploadFile(file);
    }
    
    function uploadFile(file) {
        // Mostra la barra di progresso
        dropArea.style.display = 'none';
        uploadProgress.style.display = 'block';
        
        const formData = new FormData();
        formData.append('file', file);
        
        // Simula un caricamento progressivo
        let progress = 0;
        const interval = setInterval(() => {
            progress += 5;
            if (progress > 90) {
                clearInterval(interval);
            }
            updateProgress(progress);
        }, 500);
        
        // Determina l'endpoint in base alla modalità corrente
        const endpoint = currentMode === 'normal' ? '/upload' : '/upload10s';
        
        // Invia il file al server
        fetch(endpoint, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            clearInterval(interval);
            
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Errore durante il caricamento');
                });
            }
            
            return response.json();
        })
        .then(data => {
            updateProgress(100);
            
            // Salva l'ID del risultato
            currentResultId = data.id;
            
            // Mostra i risultati
            setTimeout(() => {
                displayResults(data);
            }, 500);
        })
        .catch(error => {
            clearInterval(interval);
            showError(error.message);
            resetUploadArea();
        });
    }
    
    function updateProgress(percent) {
        progressFill.style.width = `${percent}%`;
        progressText.textContent = `${percent}%`;
    }
    
    function displayResults(data) {
        // Nascondi la barra di progresso
        uploadProgress.style.display = 'none';
        
        // Mostra la sezione dei risultati
        resultsSection.style.display = 'block';
        
        // Visualizza le informazioni sul video
        displayVideoInfo(data.video_info);
        
        // Visualizza le scene rilevate
        displayScenes(data.scenes);
        
        // Imposta l'URL di download per le immagini
        downloadBtn.onclick = () => {
            window.location.href = `/download/${currentResultId}`;
        };
        
        // Imposta l'URL di download per i video
        downloadVideosBtn.onclick = () => {
            window.location.href = `/download-videos/${currentResultId}`;
        };
    }
    
    function displayVideoInfo(videoInfo) {
        videoInfoContainer.innerHTML = `
            <div class="video-info-item">
                <span class="video-info-label">Durata:</span>
                <span>${formatTime(videoInfo.duration)}</span>
            </div>
            <div class="video-info-item">
                <span class="video-info-label">Risoluzione:</span>
                <span>${videoInfo.resolution}</span>
            </div>
            <div class="video-info-item">
                <span class="video-info-label">FPS:</span>
                <span>${videoInfo.fps.toFixed(2)}</span>
            </div>
            <div class="video-info-item">
                <span class="video-info-label">Formato:</span>
                <span>${videoInfo.format}</span>
            </div>
        `;
    }
    
    function displayScenes(scenes) {
        scenesContainer.innerHTML = '';
        
        scenes.forEach(scene => {
            const sceneCard = document.createElement('div');
            sceneCard.className = 'scene-card';
            
            sceneCard.innerHTML = `
                <img src="${scene.thumbnail}" alt="Scene ${scene.id}" class="scene-thumbnail">
                <div class="scene-info">
                    <h3>Scena ${scene.id}</h3>
                    <p class="scene-time">Inizio: ${formatTime(scene.start_time)}</p>
                    <p class="scene-time">Fine: ${formatTime(scene.end_time)}</p>
                    <p class="scene-time">Durata: ${formatTime(scene.duration)}</p>
                    <a href="${scene.video}" class="btn-small" download>Scarica video</a>
                </div>
            `;
            
            scenesContainer.appendChild(sceneCard);
        });
    }
    
    function formatTime(seconds) {
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    
    function resetUploadArea() {
        uploadProgress.style.display = 'none';
        dropArea.style.display = 'block';
        fileInput.value = '';
    }
    
    // Funzioni aggiuntive per la gestione dell'interfaccia
    function hideResults() {
        resultsSection.style.display = 'none';
    }

    function showLoadingMessage(message) {
        uploadProgress.style.display = 'block';
        progressText.textContent = message || 'Caricamento in corso...';
        progressFill.style.width = '0%';
        
        // Simula un caricamento progressivo
        let progress = 0;
        window.loadingInterval = setInterval(() => {
            progress += 5;
            if (progress > 90) {
                clearInterval(window.loadingInterval);
            }
            updateProgress(progress);
        }, 300);
    }

    function hideLoadingMessage() {
        if (window.loadingInterval) {
            clearInterval(window.loadingInterval);
        }
        uploadProgress.style.display = 'none';
    }

    function setModeButtonActive() {
        if (currentMode === '10s') {
            normalModeBtn.classList.remove('active');
            mode10sBtn.classList.add('active');
        } else {
            normalModeBtn.classList.add('active');
            mode10sBtn.classList.remove('active');
        }
    }

    // Gestione degli errori
    function showError(message) {
        errorMessage.textContent = message;
        errorModal.style.display = 'block';
    }
    
    closeModal.addEventListener('click', () => {
        errorModal.style.display = 'none';
    });
    
    window.addEventListener('click', (e) => {
        if (e.target === errorModal) {
            errorModal.style.display = 'none';
        }
    });
    
    // Gestione della sensibilità
    sensitivitySlider.addEventListener('input', () => {
        currentSensitivity = sensitivitySlider.value;
        sensitivityValue.textContent = currentSensitivity;
    });
    
    sensitivitySlider.addEventListener('change', () => {
        // Se abbiamo già un risultato, riprocessa il video con la nuova sensibilità
        if (currentResultId) {
            // Qui potremmo implementare una chiamata API per riprocessare il video
            // con la nuova sensibilità, ma per semplicità non lo implementiamo in questo esempio
            console.log(`Nuova sensibilità: ${currentSensitivity}`);
        }
    });

    // Ascolta l'evento di caricamento da YouTube
    document.addEventListener('load-youtube-video', (event) => {
        const videoId = event.detail.videoId;
        const mode = event.detail.mode;
        console.log(`Loading YouTube video: ${videoId}, Mode: ${mode}`);

        resetUploadArea();
        hideResults();
        showLoadingMessage('Caricamento e elaborazione video YouTube...');

        // Determina l'endpoint API corretto da chiamare
        let endpoint = '';
        if (mode === '10s') {
            currentMode = '10s'; // Imposta la modalità corrente
            setModeButtonActive(); // Aggiorna il pulsante della modalità
            endpoint = `/process-yt/${videoId}`; // API endpoint per la modalità 10s
        } else {
            currentMode = 'normal'; // Imposta la modalità corrente
            setModeButtonActive(); // Aggiorna il pulsante della modalità
            endpoint = `/process-youtube/${videoId}`; // API endpoint per la modalità normale (rilevamento scene)
        }

        // Chiama l'endpoint API corretto
        fetch(endpoint)
            .then(response => {
                if (!response.ok) {
                    // Prova a leggere l'errore JSON se disponibile
                    return response.json().then(err => {
                        throw new Error(err.error || `Errore HTTP: ${response.status}`);
                    }).catch(() => {
                        // Se non c'è JSON, lancia un errore generico
                        throw new Error(`Errore HTTP: ${response.status}`);
                    });
                }
                return response.json(); // Ora dovremmo ricevere JSON
            })
            .then(data => {
                hideLoadingMessage();
                if (data.success) {
                    console.log('Video data received:', data);
                    displayResults(data);
                } else {
                    showError(data.error || 'Errore sconosciuto durante l\'elaborazione del video');
                    resetUploadArea();
                }
            })
            .catch(error => {
                console.error('Error fetching or processing video data:', error);
                hideLoadingMessage();
                // Mostra l'errore specifico catturato o un messaggio generico
                showError(`Non è stato possibile caricare il video: ${error.message}`);
                resetUploadArea();
            });
    });
}); 