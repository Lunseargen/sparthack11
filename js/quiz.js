// Quiz Module for Page 2
// Handles quiz functionality, character detection, and scoring

class QuizManager {
    constructor() {
        this.videoElement = document.getElementById('quizVideo');
        this.startBtn = document.getElementById('startQuizBtn');
        this.stopBtn = document.getElementById('stopQuizBtn');
        this.nextBtn = document.getElementById('nextBtn');
        this.selectAllBtn = document.getElementById('selectAllBtn');
        this.clearAllBtn = document.getElementById('clearAllBtn');
        this.charBox = document.getElementById('charBox');
        this.detBox = document.getElementById('detBox');
        this.scoreBox = document.getElementById('scoreBox');
        this.checkboxGrid = document.getElementById('checkboxGrid');
        this.status = document.getElementById('status');
        
        this.isQuizActive = false;
        this.selectedCharacters = [];
        this.currentQuestionIndex = 0;
        this.correctAnswers = 0;
        this.totalAnswers = 0;
        this.questions = [];
        this.frameCount = 0;
        this.maxFrames = 1000;
        this.canvas = document.createElement('canvas');
        this.canvasContext = this.canvas.getContext('2d');
        
        // Request throttling to prevent memory buildup
        this.pendingFrameUploads = 0;
        this.maxPendingFrames = 3; // Only allow 3 concurrent frame uploads
        
        this.initCheckboxes();
        this.initEventListeners();
        this.loadQuestions();
        
        // Add window error listener to catch uncaught errors
        window.addEventListener('error', (e) => {
            console.error('Uncaught error:', e.error);
            try {
                this.updateStatus('Error: ' + (e.error?.message || e.message || 'Unknown error'), 'error');
            } catch (err) {
                console.error('Failed to update status on error:', err);
            }
            // Prevent default error behavior (page reload)
            e.preventDefault();
        });
        
        // Add unhandled promise rejection listener
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Unhandled promise rejection:', e.reason);
            try {
                this.updateStatus('Promise error: ' + (e.reason?.message || e.reason || 'Unknown'), 'error');
            } catch (err) {
                console.error('Failed to update status on promise error:', err);
            }
            // Prevent default rejection behavior
            e.preventDefault();
        });
        
        // Completely block all navigation while quiz is active
        window.addEventListener('beforeunload', (e) => {
            if (this.isQuizActive) {
                console.error('🚨 beforeunload triggered! Stack:', new Error().stack);
                // Block without showing dialog
                e.preventDefault();
                e.returnValue = undefined;
                return undefined;
            }
        });
        
        // Block all link clicks
        document.addEventListener('click', (e) => {
            if (this.isQuizActive) {
                const link = e.target.closest('a[href]');
                if (link) {
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }
            }
        }, true);
        
        // Block all form submissions
        document.addEventListener('submit', (e) => {
            if (this.isQuizActive) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }
        }, true);
        
        // Monitor for any hidden reloads
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            if (this.isQuizActive && args[0] && args[0].toString().includes('page2')) {
                console.warn('Blocked fetch to page2:', args);
                return Promise.reject(new Error('Navigation blocked'));
            }
            return originalFetch.apply(window, args);
        }.bind(this);
        
        // Trap XMLHttpRequest navigations
        const self = this;
        const originalOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(method, url, ...args) {
            if (self.isQuizActive && url.includes('page2')) {
                console.warn('Blocked XMLHttpRequest to page2:', url);
                return;
            }
            return originalOpen.apply(this, [method, url, ...args]);
        };
    }
    
    initCheckboxes() {
        const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
        
        alphabet.forEach(char => {
            const checkboxItem = document.createElement('div');
            checkboxItem.className = 'checkbox-item';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `char-${char}`;
            checkbox.value = char;
            
            const label = document.createElement('label');
            label.htmlFor = `char-${char}`;
            label.textContent = char;
            
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.selectedCharacters.push(char);
                } else {
                    this.selectedCharacters = this.selectedCharacters.filter(c => c !== char);
                }
            });
            
            checkboxItem.appendChild(checkbox);
            checkboxItem.appendChild(label);
            this.checkboxGrid.appendChild(checkboxItem);
        });
    }
    
    initEventListeners() {
        this.startBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.startQuiz();
        });
        this.stopBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.stopQuiz();
        });
        this.nextBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.nextQuestion();
        });
        this.selectAllBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.selectAllCharacters();
        });
        this.clearAllBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.clearAllCharacters();
        });
    }
    
    selectAllCharacters() {
        try {
            document.querySelectorAll('#checkboxGrid input[type="checkbox"]').forEach(cb => {
                if (!cb.checked) {
                    cb.checked = true;
                    const char = cb.value;
                    if (!this.selectedCharacters.includes(char)) {
                        this.selectedCharacters.push(char);
                    }
                }
            });
        } catch (err) {
            console.error('Error selecting all characters:', err);
        }
    }
    
    clearAllCharacters() {
        try {
            document.querySelectorAll('#checkboxGrid input[type="checkbox"]').forEach(cb => {
                cb.checked = false;
            });
            this.selectedCharacters = [];
        } catch (err) {
            console.error('Error clearing characters:', err);
        }
    }
    
    loadQuestions() {
        // Sample questions - in a real app, these would come from a server
        this.questions = [
            { id: 1, question: 'Which character appears first?', correctAnswers: ['A', 'B', 'C'] },
            { id: 2, question: 'What is the second character?', correctAnswers: ['D', 'E', 'F'] },
            { id: 3, question: 'Which character comes after G?', correctAnswers: ['H', 'I'] },
            { id: 4, question: 'Identify the next character', correctAnswers: ['J', 'K'] },
            { id: 5, question: 'What character do you see?', correctAnswers: ['L', 'M', 'N'] }
        ];
    }
    
    async startQuiz() {
        try {
            console.log('═══ startQuiz() called ═══');
            console.log('Step 1: Updating status to "Requesting camera access..."');
            this.updateStatus('Requesting camera access...', 'info');
            
            console.log('Step 2: Calling getUserMedia...');
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 1280 }, height: { ideal: 720 } },
                audio: false
            });
            console.log('Step 3: Camera stream obtained, stream ID:', stream.id);
            
            console.log('Step 4: Setting videoElement.srcObject');
            this.videoElement.srcObject = stream;
            console.log('Step 5: videoElement.srcObject set successfully');
            
            console.log('Step 6: Setting quiz state variables');
            this.isQuizActive = true;
            console.log('  - isQuizActive = true');
            this.currentQuestionIndex = 0;
            console.log('  - currentQuestionIndex = 0');
            this.correctAnswers = 0;
            console.log('  - correctAnswers = 0');
            this.totalAnswers = 0;
            console.log('  - totalAnswers = 0');
            this.frameCount = 0;
            console.log('  - frameCount = 0');
            
            console.log('Step 7: Disabling/enabling buttons');
            this.startBtn.disabled = true;
            console.log('  - startBtn disabled');
            this.stopBtn.disabled = false;
            console.log('  - stopBtn enabled');
            this.nextBtn.disabled = false;
            console.log('  - nextBtn enabled');
            
            console.log('Step 8: Loading question...');
            this.loadQuestion(0);
            console.log('Step 9: Question loaded');
            
            console.log('Step 10: Starting frame capture...');
            this.startFrameCapture();
            console.log('Step 11: Frame capture started');
            
            console.log('Step 12: Updating status to "Quiz started!"');
            this.updateStatus('Quiz started!', 'info');
            
            console.log('═══ Quiz started successfully ═══');
            
        } catch (err) {
            console.error('❌ ERROR in startQuiz:', err);
            console.error('Stack trace:', err.stack);
            try {
                this.updateStatus('Error accessing camera: ' + err.message, 'error');
            } catch (statusErr) {
                console.error('Failed to update status:', statusErr);
            }
        }
    }
    
    stopQuiz() {
        try {
            this.isQuizActive = false;
            
            if (this.videoElement.srcObject) {
                this.videoElement.srcObject.getTracks().forEach(track => track.stop());
            }
            
            this.startBtn.disabled = false;
            this.stopBtn.disabled = true;
            this.nextBtn.disabled = true;
            
            this.updateStatus(`Quiz completed! Final Score: ${this.correctAnswers}/${this.totalAnswers}`, 'success');
        } catch (err) {
            console.error('Error stopping quiz:', err);
        }
    }
    
    loadQuestion(index) {
        try {
            if (index >= this.questions.length) {
                this.stopQuiz();
                return;
            }
            
            const question = this.questions[index];
            this.currentQuestionIndex = index;
            
            // Reset character selection
            this.selectedCharacters = [];
            document.querySelectorAll('#checkboxGrid input[type="checkbox"]').forEach(cb => {
                cb.checked = false;
            });
            
            this.charBox.textContent = String.fromCharCode(65 + index); // A, B, C...
            this.updateScore();
        } catch (err) {
            console.error('Error loading question:', err);
        }
    }
    
    nextQuestion() {
        try {
            if (this.currentQuestionIndex >= this.questions.length) {
                this.updateStatus('Quiz completed!', 'success');
                return;
            }
            
            // Check if answer was correct
            const currentQuestion = this.questions[this.currentQuestionIndex];
            const isCorrect = this.validateAnswer(currentQuestion);
            
            if (isCorrect) {
                this.correctAnswers++;
            }
            
            this.totalAnswers++;
            this.currentQuestionIndex++;
            
            if (this.currentQuestionIndex < this.questions.length) {
                this.loadQuestion(this.currentQuestionIndex);
            } else {
                this.stopQuiz();
            }
        } catch (err) {
            console.error('Error in nextQuestion:', err);
        }
    }
    
    validateAnswer(question) {
        // Check if any selected character is in the correct answers
        return this.selectedCharacters.some(char => 
            question.correctAnswers.includes(char)
        );
    }
    
    startFrameCapture() {
        console.log('🎥 Frame capture started');
        let logCounter = 0;
        let captureAttempts = 0;
        
        const captureLoop = () => {
            try {
                captureAttempts++;
                
                if (!this.isQuizActive) {
                    console.log('Quiz not active, stopping capture loop (attempt', captureAttempts, ')');
                    return;
                }
                
                if (this.frameCount < this.maxFrames) {
                    logCounter++;
                    if (logCounter % 10 === 0) {
                        console.log(`[Frame ${this.frameCount}] Pending uploads: ${this.pendingFrameUploads}/${this.maxPendingFrames}`);
                        // Log memory usage if available
                        if (performance.memory) {
                            const memoryMB = (performance.memory.usedJSHeapSize / 1048576).toFixed(2);
                            console.log(`Memory: ${memoryMB}MB (limit: ~128MB)`);
                        }
                    }
                    
                    this.captureFrameToServer();
                    this.frameCount++;
                }
                
                setTimeout(captureLoop, 33); // ~30fps
            } catch (err) {
                console.error('❌ Frame capture loop error (attempt', captureAttempts, '):', err);
                console.error('Stack:', err.stack);
                // Continue capture even if there's an error
                if (this.isQuizActive) {
                    setTimeout(captureLoop, 33);
                }
            }
        };
        
        console.log('🎥 Starting capture loop');
        captureLoop();
    }
    
    captureFrameToServer() {
        try {
            if (!this.videoElement.srcObject) {
                console.warn('No video source object');
                return;
            }
            
            this.canvas.width = this.videoElement.videoWidth;
            this.canvas.height = this.videoElement.videoHeight;
            
            if (this.canvas.width === 0 || this.canvas.height === 0) {
                // Video stream not ready yet
                console.debug(`Video not ready: ${this.canvas.width}x${this.canvas.height}`);
                return;
            }
            
            this.canvasContext.drawImage(this.videoElement, 0, 0);
            
            this.canvas.toBlob((blob) => {
                try {
                    if (!blob) {
                        console.warn('Blob is null after toBlob');
                        return;
                    }
                    
                    if (blob.size === 0) {
                        console.warn('Blob is empty after toBlob');
                        return;
                    }
                    
                    if (this.isQuizActive) {
                        this.sendFrameToServer(blob).catch(err => {
                            console.error('Unhandled error in sendFrameToServer:', err);
                        });
                    }
                } catch (err) {
                    console.error('Error in toBlob callback:', err);
                }
            }, 'image/jpeg', 0.6); // Reduced quality from 0.8 to 0.6 to reduce blob size
            
            // Clear canvas to prevent memory buildup
            this.canvasContext.clearRect(0, 0, this.canvas.width, this.canvas.height);
        } catch (err) {
            console.error('❌ Error in captureFrameToServer:', err);
            console.error('Stack:', err.stack);
        }
    }
    
    async sendFrameToServer(blob) {
        if (!blob || blob.size === 0) {
            console.warn('Invalid blob:', blob ? `size ${blob.size}` : 'null');
            return;
        }
        
        // Throttle requests if too many are pending
        if (this.pendingFrameUploads >= this.maxPendingFrames) {
            console.warn(`Too many pending frames (${this.pendingFrameUploads}), skipping upload`);
            return;
        }
        
        this.pendingFrameUploads++;
        
        try {
            const formData = new FormData();
            formData.append('frame', blob, 'frame.jpg');
            
            console.log('📤 Sending frame to MJPEG server (pending:', this.pendingFrameUploads, ')');
            
            const response = await fetch('http://localhost:5000/send-mjpeg', {
                method: 'POST',
                body: formData,
                signal: AbortSignal.timeout(5000) // 5 second timeout
            });
            
            if (!response.ok) {
                console.warn('⚠️ Frame upload returned status:', response.status);
                this.storeFrameLocally(blob);
            } else {
                console.log('✅ Frame queued for MJPEG stream');
            }
        } catch (err) {
            console.error('❌ Fetch error (server may not be running):', err.message);
            // Store locally without throwing
            try {
                this.storeFrameLocally(blob);
            } catch (storageErr) {
                console.error('Also failed to store locally:', storageErr);
            }
        } finally {
            this.pendingFrameUploads--;
            blob = null;
        }
    }
    
    storeFrameLocally(blob) {
        try {
            if ('indexedDB' in window) {
                const request = indexedDB.open('QuizFrameDB', 1);
                
                request.onupgradeneeded = () => {
                    try {
                        const db = request.result;
                        if (!db.objectStoreNames.contains('frames')) {
                            db.createObjectStore('frames', { autoIncrement: true });
                        }
                    } catch (err) {
                        console.error('Error in indexedDB onupgradeneeded:', err);
                    }
                };
                
                request.onsuccess = () => {
                    try {
                        const db = request.result;
                        const transaction = db.transaction(['frames'], 'readwrite');
                        const store = transaction.objectStore('frames');
                        store.add({
                            frame: blob,
                            frameNumber: this.frameCount,
                            questionIndex: this.currentQuestionIndex,
                            timestamp: new Date().toISOString()
                        });
                    } catch (err) {
                        console.error('Error in indexedDB onsuccess:', err);
                    }
                };
                
                request.onerror = () => {
                    console.error('IndexedDB error:', request.error);
                };
            }
        } catch (err) {
            console.error('Error storing frame locally:', err);
        }
    }
    
    updateDetection(detectionResult) {
        this.detBox.textContent = detectionResult || 'No detection';
        
        // Simulate vision detection API call
        this.callVisionAPI().then(result => {
            if (result) {
                this.detBox.textContent = result;
            }
        });
    }
    
    async callVisionAPI() {
        // Vision API backend removed
        return null;
    }
    
    updateScore() {
        this.scoreBox.textContent = `${this.correctAnswers}/${this.totalAnswers}`;
    }
    
    updateStatus(message, className = '') {
        try {
            this.status.textContent = message;
            this.status.className = 'status info';
        } catch (err) {
            console.error('Error updating status:', err);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new QuizManager();
});
