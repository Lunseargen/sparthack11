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
        this.maxFrames = 1000;
        this.isRecording = false;
        this.canvas = document.createElement('canvas');
        this.canvasContext = this.canvas.getContext('2d');
        
        this.initEventListeners();
    }
    
    initEventListeners() {
        this.startBtn.addEventListener('click', () => this.startRecording());
        this.stopBtn.addEventListener('click', () => this.stopRecording());
        this.captureFrameBtn.addEventListener('click', () => this.captureFrame());
        this.speakerBtn.addEventListener('click', () => this.playAudio());
    }
    
    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 1280 }, height: { ideal: 720 } },
                audio: false
            });
            
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
                this.startFrameCapture();
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
    
    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
            
            // Stop video stream
            if (this.videoElement.srcObject) {
                this.videoElement.srcObject.getTracks().forEach(track => track.stop());
            }
        }
    }
    
    startFrameCapture() {
        const captureLoop = () => {
            if (!this.isRecording) return;
            
            if (this.frameCount < this.maxFrames) {
                this.captureFrameToServer();
                this.frameCount++;
                this.updateStatus(`Recording... ${this.frameCount}/${this.maxFrames} frames captured. Textbox 1: ${this.textbox1.value.substring(0, 20)}...`, 'recording');
            }
            
            setTimeout(captureLoop, 33); // ~30fps
        };
        
        captureLoop();
    }
    
    captureFrame() {
        if (!this.videoElement.srcObject) {
            this.updateStatus('No video stream active. Start recording first.', 'error');
            return;
        }
        
        this.canvas.width = this.videoElement.videoWidth;
        this.canvas.height = this.videoElement.videoHeight;
        this.canvasContext.drawImage(this.videoElement, 0, 0);
        
        this.canvas.toBlob((blob) => {
            this.sendFrameToServer(blob);
            this.updateStatus('Frame captured and saved!', 'success');
        }, 'image/jpeg', 0.9);
    }
    
    captureFrameToServer() {
        if (!this.videoElement.srcObject) return;
        
        this.canvas.width = this.videoElement.videoWidth;
        this.canvas.height = this.videoElement.videoHeight;
        this.canvasContext.drawImage(this.videoElement, 0, 0);
        
        this.canvas.toBlob((blob) => {
            this.sendFrameToServer(blob);
        }, 'image/jpeg', 0.8);
    }
    
    async sendFrameToServer(blob) {
        try {
            const formData = new FormData();
            formData.append('frame', blob);
            
            fetch('http://localhost:5000/send-frame', {
                method: 'POST',
                body: formData
            }).catch(err => {
                // Silently fallback to local storage
                this.storeFrameLocally(blob);
            });
        } catch (err) {
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
