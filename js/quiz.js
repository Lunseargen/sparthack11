// Quiz Module for Page 2
// Handles quiz functionality, character detection, and scoring

class QuizManager {
    constructor() {
        this.videoElement = document.getElementById('quizVideo');
        this.startBtn = document.getElementById('startQuizBtn');
        this.stopBtn = document.getElementById('stopQuizBtn');
        this.nextBtn = document.getElementById('nextBtn');
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
        
        this.initCheckboxes();
        this.initEventListeners();
        this.loadQuestions();
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
        this.startBtn.addEventListener('click', () => this.startQuiz());
        this.stopBtn.addEventListener('click', () => this.stopQuiz());
        this.nextBtn.addEventListener('click', () => this.nextQuestion());
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
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 1280 }, height: { ideal: 720 } },
                audio: false
            });
            
            this.videoElement.srcObject = stream;
            
            this.isQuizActive = true;
            this.currentQuestionIndex = 0;
            this.correctAnswers = 0;
            this.totalAnswers = 0;
            this.frameCount = 0;
            
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
            this.nextBtn.disabled = false;
            
            this.loadQuestion(0);
            this.startFrameCapture();
            this.updateStatus('Quiz started!', 'info');
            
        } catch (err) {
            this.updateStatus('Error accessing camera: ' + err.message, 'error');
            console.error('Error:', err);
        }
    }
    
    stopQuiz() {
        this.isQuizActive = false;
        
        if (this.videoElement.srcObject) {
            this.videoElement.srcObject.getTracks().forEach(track => track.stop());
        }
        
        this.startBtn.disabled = false;
        this.stopBtn.disabled = true;
        this.nextBtn.disabled = true;
        
        this.updateStatus(`Quiz completed! Final Score: ${this.correctAnswers}/${this.totalAnswers}`, 'success');
    }
    
    loadQuestion(index) {
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
    }
    
    nextQuestion() {
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
    }
    
    validateAnswer(question) {
        // Check if any selected character is in the correct answers
        return this.selectedCharacters.some(char => 
            question.correctAnswers.includes(char)
        );
    }
    
    startFrameCapture() {
        const captureLoop = () => {
            if (!this.isQuizActive) return;
            
            if (this.frameCount < this.maxFrames) {
                this.captureFrameToServer();
                this.frameCount++;
            }
            
            setTimeout(captureLoop, 33); // ~30fps
        };
        
        captureLoop();
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
        if ('indexedDB' in window) {
            const request = indexedDB.open('QuizFrameDB', 1);
            
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
                    questionIndex: this.currentQuestionIndex,
                    timestamp: new Date().toISOString()
                });
            };
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
        this.status.textContent = message;
        this.status.className = 'status info';
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new QuizManager();
});
