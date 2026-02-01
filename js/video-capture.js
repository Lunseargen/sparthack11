// Video Capture Module for Page 1
// Handles video streaming, frame capture, and saving

class VideoCaptureManager {
    constructor() {
        this.videoElement = document.getElementById('videoStream');
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.captureFrameBtn = document.getElementById('captureFrameBtn');
        this.speakerBtn = document.getElementById('speakerBtn');
        this.status = document.getElementById('status');
        this.textbox1 = document.getElementById('textbox1');
        this.textbox2 = document.getElementById('textbox2');
        
        this.mediaRecorder = null;
        this.recordedChunks = [];
        this.frameCount = 0;
        this.maxFrames = 300;
        this.isRecording = false;
        this.canvas = document.createElement('canvas');
        this.canvasContext = this.canvas.getContext('2d');

        this.streamMonitor = null;
        this.lastFrameAt = 0;

        this.initEventListeners();
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
            
            fetch('http://localhost:5000/send-frame', {
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
            // Try to play audio file from server
            const audio = new Audio('audio/speech.mp3');
            audio.play().catch(err => {
                this.updateStatus('No audio file found or error playing audio: ' + err.message, 'error');
                console.error('Audio playback error:', err);
            });
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
