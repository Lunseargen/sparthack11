// Video Capture Module for Page 1
// Handles video streaming, frame capture, and saving

class VideoCaptureManager {
    constructor() {
        this.videoElement = document.getElementById('videoStream');
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.captureFrameBtn = document.getElementById('captureFrameBtn');
        this.speakerBtn = document.getElementById('speakerBtn');
        this.refreshLogsBtn = document.getElementById('refreshLogsBtn');
        this.loadDemoBtn = document.getElementById('loadDemoBtn');
        this.demoFileInput = document.getElementById('demoFileInput');
        this.clearDataBtn = document.getElementById('clearDataBtn');
        this.status = document.getElementById('status');
        this.textbox1 = document.getElementById('textbox1');
        this.textbox2 = document.getElementById('textbox2');
        this.textbox3 = document.getElementById('textbox3');
        
        this.mediaRecorder = null;
        this.recordedChunks = [];
        this.frameCount = 0;
        this.maxFrames = 300;
        this.isRecording = false;
        this.canvas = document.createElement('canvas');
        this.canvasContext = this.canvas.getContext('2d');

        this.streamMonitor = null;
        this.lastFrameAt = 0;
        this.logPoller = null;
        this.backendBaseUrl = this.getBackendBaseUrl();

        this.initEventListeners();
        this.startLogPolling();
    }
    
    initEventListeners() {
        this.startBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.startRecording();
        });
        this.stopBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.stopRecording();
        });
        this.captureFrameBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.captureFrame();
        });
        this.speakerBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.playAudio();
        });
        if (this.refreshLogsBtn) {
            this.refreshLogsBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.manualRefreshLogs();
            });
        }
        if (this.loadDemoBtn) {
            this.loadDemoBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.demoFileInput.click();
            });
        }
        if (this.demoFileInput) {
            this.demoFileInput.addEventListener('change', (e) => {
                this.loadDemoDataFromFile(e);
            });
        }
        if (this.clearDataBtn) {
            this.clearDataBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.clearDetectionData();
            });
        }
    }

    getBackendBaseUrl() {
        const params = new URLSearchParams(window.location.search);
        const override = params.get('backend');
        if (override) return override.replace(/\/$/, '');
        const stored = window.localStorage.getItem('backendUrl');
        if (stored) return stored.replace(/\/$/, '');
        return 'http://localhost:5000';
    }

    startLogPolling() {
        if (this.logPoller) return;
        const poll = async () => {
            try {
                await this.refreshLogs();
            } catch (err) {
                // ignore poll errors
            }
        };
        poll();
        this.logPoller = setInterval(poll, 1000);
    }

    async refreshLogs() {
        const utils = window.DetectionUtils;
        if (!utils) return;

        const logs = utils.getLogs();
        if (this.textbox1) this.textbox1.value = logs.rawLabels || '';

        if (Array.isArray(logs.compacted) && this.textbox2) {
            const labels = logs.compacted.map(item => item.label).filter(Boolean).join('');
            this.textbox2.value = labels;
        }

        if (Array.isArray(logs.corrected) && this.textbox3) {
            const words = logs.corrected.map(item => item.string).filter(Boolean).join(' ');
            this.textbox3.value = words;
        }
    }

    async manualRefreshLogs() {
        this.updateStatus('Refreshing logs...', 'recording');
        try {
            await this.refreshLogs();
            this.updateStatus('Logs refreshed successfully!', 'success');
        } catch (err) {
            this.updateStatus('Error refreshing logs: ' + err.message, 'error');
        }
    }

    async loadDemoDataFromFile(event) {
        const file = event.target.files[0];
        if (!file) return;

        this.updateStatus('Loading demo data...', 'recording');
        try {
            const text = await file.text();
            const data = JSON.parse(text);

            if (!Array.isArray(data)) {
                throw new Error('Invalid format: expected an array of detection entries');
            }

            const utils = window.DetectionUtils;
            if (!utils) throw new Error('Detection utilities not available');

            utils.saveDetections(data);
            await this.refreshLogs();
            this.updateStatus(`Demo data loaded: ${data.length} entries`, 'success');
        } catch (err) {
            this.updateStatus('Error loading demo data: ' + err.message, 'error');
        } finally {
            // Reset file input so the same file can be loaded again
            event.target.value = '';
        }
    }

    async clearDetectionData() {
        this.updateStatus('Clearing detection data...', 'recording');
        try {
            const utils = window.DetectionUtils;
            if (!utils) throw new Error('Detection utilities not available');

            utils.clearDetections();

            // Clear textboxes
            if (this.textbox1) this.textbox1.value = '';
            if (this.textbox2) this.textbox2.value = '';
            if (this.textbox3) this.textbox3.value = '';

            this.updateStatus('Detection data cleared!', 'success');
        } catch (err) {
            this.updateStatus('Error clearing data: ' + err.message, 'error');
        }
    }

    
    
    async startRecording() {
        try {
            const stream = await this.getPreferredVideoStream();
            
            this.videoElement.srcObject = stream;
            
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'video/webm;codecs=vp8,opus'
            });
            
            this.recordedChunks = [];
            this.frameCount = 0;
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.recordedChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstart = () => {
                this.isRecording = true;
                this.startBtn.disabled = true;
                this.stopBtn.disabled = false;
                this.updateStatus('Recording... ' + this.frameCount + ' frames captured', 'recording');
                this.lastFrameAt = Date.now();
            this.startFrameCapture();
            this.startStreamMonitor();
            };
            
            this.mediaRecorder.onstop = () => {
                this.isRecording = false;
                this.startBtn.disabled = false;
                this.stopBtn.disabled = true;
                this.updateStatus('Recording stopped. ' + this.frameCount + ' frames saved.', 'success');
            };
            
            this.mediaRecorder.start();
        } catch (err) {
            this.updateStatus('Error: ' + err.message, 'error');
            console.error('Error accessing camera:', err);
        }
    }
    

    async getPreferredVideoStream() {
        const baseConstraints = {
            video: { width: { ideal: 1280 }, height: { ideal: 720 } },
            audio: false
        };

        // First request permission with generic constraints.
        const initialStream = await navigator.mediaDevices.getUserMedia(baseConstraints);
        const currentTrack = initialStream.getVideoTracks()[0];
        const currentSettings = currentTrack ? currentTrack.getSettings() : {};
        const currentDeviceId = currentSettings.deviceId || '';

        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoInputs = devices.filter(d => d.kind === 'videoinput');

            if (videoInputs.length === 0) {
                return initialStream;
            }

            // Prefer common built-in webcam labels if available.
            const preferPattern = /integrated|webcam|usb|hd|camera/i;
            const avoidPattern = /phone|mobile|virtual|loopback|continuity/i;

            let chosen = videoInputs.find(d => d.label && preferPattern.test(d.label) && !avoidPattern.test(d.label));

            if (!chosen) {
                // Avoid the current device if multiple cameras exist.
                const alternate = videoInputs.find(d => d.deviceId && d.deviceId !== currentDeviceId && !avoidPattern.test(d.label || ''));
                chosen = alternate || videoInputs.find(d => !avoidPattern.test(d.label || '')) || videoInputs[0];
            }

            if (chosen && chosen.deviceId) {
                // Stop the initial stream before opening the selected device.
                initialStream.getTracks().forEach(track => track.stop());
                return await navigator.mediaDevices.getUserMedia({
                    video: {
                        deviceId: { exact: chosen.deviceId },
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    },
                    audio: false
                });
            }
        } catch (err) {
            console.warn('Camera selection failed, using initial stream.', err);
        }

        return initialStream;
    }

    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
            
            // Stop video stream
            if (this.videoElement.srcObject) {
                this.videoElement.srcObject.getTracks().forEach(track => track.stop());
            }
        }

        if (this.streamMonitor) {
            clearInterval(this.streamMonitor);
            this.streamMonitor = null;
        }
    }
    
    startFrameCapture() {
        const captureLoop = () => {
            try {
                if (!this.isRecording) return;
                
                this.captureFrameToServer();
                this.frameCount++;
                this.updateStatus(`Recording... ${this.frameCount}/${this.maxFrames} frames captured. Textbox 1: ${this.textbox1.value.substring(0, 20)}...`, 'recording');
                
                setTimeout(captureLoop, 33); // ~30fps
            } catch (err) {
                console.error('Frame capture loop error:', err);
                // Continue capture even if there's an error
                if (this.isRecording) {
                    setTimeout(captureLoop, 33);
                }
            }
        };
        
        captureLoop();
    }
    
    captureFrame() {
        if (!this.videoElement.srcObject) {
            this.updateStatus('No video stream active. Start recording first.', 'error');
            return;
        }
        
        try {
            this.canvas.width = this.videoElement.videoWidth;
            this.canvas.height = this.videoElement.videoHeight;
            this.canvasContext.drawImage(this.videoElement, 0, 0);
            this.lastFrameAt = Date.now();
            
            this.canvas.toBlob((blob) => {
                if (blob) {
                    this.sendFrameToServer(blob);
                    this.updateStatus('Frame captured and saved!', 'success');
                }
            }, 'image/jpeg', 0.9);
        } catch (err) {
            console.error('Error capturing frame:', err);
            this.updateStatus('Error capturing frame: ' + err.message, 'error');
        }
    }
    
    captureFrameToServer() {
        if (!this.videoElement.srcObject) return;
        
        try {
            this.canvas.width = this.videoElement.videoWidth;
            this.canvas.height = this.videoElement.videoHeight;
            
            if (this.canvas.width === 0 || this.canvas.height === 0) {
                // Video stream not ready yet
                return;
            }
            
            this.canvasContext.drawImage(this.videoElement, 0, 0);
            this.lastFrameAt = Date.now();
            
            this.canvas.toBlob((blob) => {
                if (blob && this.isRecording) {
                    this.sendFrameToServer(blob);
                }
            }, 'image/jpeg', 0.8);
        } catch (err) {
            console.error('Error capturing frame:', err);
        }
    }
    
    async sendFrameToServer(blob) {
        if (!blob || blob.size === 0) return;
        
        try {
            const formData = new FormData();
            formData.append('frame', blob, 'frame.jpg');
            
            fetch(`${this.backendBaseUrl}/send-frame`, {
                method: 'POST',
                body: formData
            }).then(response => {
                if (!response.ok) {
                    console.warn('Frame upload returned status:', response.status);
                }
            }).catch(err => {
                // Silently fallback to local storage
                this.storeFrameLocally(blob);
            });
        } catch (err) {
            console.error('Error sending frame:', err);
            this.storeFrameLocally(blob);
        }
    }
    
    storeFrameLocally(blob) {
        // Store frames in IndexedDB as fallback
        if ('indexedDB' in window) {
            const request = indexedDB.open('FrameDB', 1);
            
            request.onupgradeneeded = () => {
                const db = request.result;
                if (!db.objectStoreNames.contains('frames')) {
                    db.createObjectStore('frames', { autoIncrement: true });
                }
            };
            
            request.onsuccess = () => {
                const db = request.result;
                const transaction = db.transaction(['frames'], 'readwrite');
                const store = transaction.objectStore('frames');
                store.add({
                    frame: blob,
                    frameNumber: this.frameCount,
                    textbox1: this.textbox1.value,
                    textbox2: this.textbox2.value,
                    timestamp: new Date().toISOString()
                });
            };
        }
    }
    
    async playAudio() {
        try {
            const text = (this.textbox2 && this.textbox2.value.trim())
                ? this.textbox2.value.trim()
                : (this.textbox1 ? this.textbox1.value.trim() : '');

            if (!text) {
                this.updateStatus('No text available for speech.', 'error');
                return;
            }

            if (!('speechSynthesis' in window)) {
                throw new Error('Speech synthesis not supported in this browser');
            }

            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            window.speechSynthesis.speak(utterance);
        } catch (err) {
            this.updateStatus('Error: ' + err.message, 'error');
        }
    }
    
    updateStatus(message, className = '') {
        this.status.textContent = message;
        this.status.className = 'status ' + className;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new VideoCaptureManager();
});
