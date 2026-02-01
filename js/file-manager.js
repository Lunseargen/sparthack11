// File Manager Module for Page 3
// Handles MP4 file upload and download

class FileManager {
    constructor() {
        this.uploadZone = document.getElementById('uploadZone');
        this.fileInput = document.getElementById('fileInput');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.fileListContainer = document.getElementById('fileListContainer');
        this.uploadStatus = document.getElementById('uploadStatus');
        this.processVideoBtn = document.getElementById('processVideoBtn');
        this.progressBar = document.getElementById('progressBar');
        this.progressFill = document.getElementById('progressFill');
        this.fileInfo = document.getElementById('fileInfo');
        this.annotateBtn = document.getElementById('annotateBtn');
        this.annotateStatus = document.getElementById('annotateStatus');
        this.downloadAnnotatedBtn = document.getElementById('downloadAnnotatedBtn');
        this.backendBaseUrl = this.getBackendBaseUrl();
        this.annotatedFrames = [];
        
        this.selectedFile = null;
        // Backend removed: file listing disabled
        this.displayFiles([]); // Optionally display an empty file list
        this.showStatus('File listing is currently disabled', 'info');

        if (this.uploadZone && this.fileInput) {
            // Upload zone click
            this.uploadZone.addEventListener('click', () => this.fileInput.click());

            // File input change
            this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

            // Drag and drop
            this.uploadZone.addEventListener('dragover', (e) => this.handleDragOver(e));
            this.uploadZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
            this.uploadZone.addEventListener('drop', (e) => this.handleDrop(e));
        }

        // Prevent browser from opening files on drop outside the zone
        document.addEventListener('dragover', (e) => {
            e.preventDefault();
        });
        document.addEventListener('drop', (e) => {
            e.preventDefault();
        });
        
        // Upload button
        if (this.uploadBtn) {
            this.uploadBtn.addEventListener('click', () => this.uploadFile());
        }

        // Process video button
        if (this.processVideoBtn) {
            this.processVideoBtn.addEventListener('click', () => this.processVideo());
        }

        if (this.annotateBtn) {
            this.annotateBtn.addEventListener('click', () => this.annotateFrames());
        }

        if (this.downloadAnnotatedBtn) {
            this.downloadAnnotatedBtn.addEventListener('click', () => this.downloadAnnotatedFrames());
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
    
    handleFileSelect(event) {
        const files = event.target.files;
        if (files.length > 0) {
            this.selectFile(files[0]);
        }
    }
    
    selectFile(file) {
        // Validate file type
        if (!file.name.toLowerCase().endsWith('.mp4')) {
            this.showStatus('Please select an MP4 file', 'error');
            return;
        }
        
        // Validate file size (500MB max)
        if (file.size > 500 * 1024 * 1024) {
            this.showStatus('File size exceeds 500MB limit', 'error');
            return;
        }
        
        this.selectedFile = file;
        this.uploadBtn.disabled = false;
        if (this.processVideoBtn) {
            this.processVideoBtn.disabled = false;
        }
        
        // Show file info
        const sizeMB = (file.size / 1024 / 1024).toFixed(2);
        this.fileInfo.textContent = `Selected: ${file.name} (${sizeMB} MB)`;
        this.fileInfo.style.color = '#28a745';
        
        this.showStatus('File selected. Click "Upload File" to proceed.', 'success');
    }
    
    handleDragOver(event) {
        event.preventDefault();
        event.stopPropagation();
        this.uploadZone.classList.add('drag-over');
    }
    
    handleDragLeave(event) {
        event.preventDefault();
        event.stopPropagation();
        this.uploadZone.classList.remove('drag-over');
    }
    
    handleDrop(event) {
        event.preventDefault();
        event.stopPropagation();
        this.uploadZone.classList.remove('drag-over');
        
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            this.selectFile(files[0]);
        }
    }
    
    async uploadFile() {
        if (!this.selectedFile) {
            this.showStatus('No file selected', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', this.selectedFile);
        
        this.uploadBtn.disabled = true;
        this.progressBar.style.display = 'block';
        this.showStatus('Uploading...', 'uploading');
        
        try {
            const xhr = new XMLHttpRequest();
            
            // Progress update
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                    const percentComplete = (event.loaded / event.total) * 100;
                    this.progressFill.style.width = percentComplete + '%';
                }
            });
            
            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    this.showStatus('File uploaded successfully!', 'success');
                    this.progressFill.style.width = '0%';
                    this.progressBar.style.display = 'none';
                    this.fileInfo.textContent = '';
                    this.fileInput.value = '';
                    this.selectedFile = null;
                    this.uploadBtn.disabled = true;
                    
                    // Reload file list
                    setTimeout(() => this.loadFileList(), 500);
                } else {
                    this.showStatus('Upload failed: ' + xhr.statusText, 'error');
                    this.uploadBtn.disabled = false;
                }
            });
            
            xhr.addEventListener('error', () => {
                this.showStatus('Upload error occurred', 'error');
                this.uploadBtn.disabled = false;
            });
            
            // Store file locally
            // Backend upload removed
            xhr.send(formData);
            
        } catch (err) {
            // Fallback: Store in IndexedDB
            this.storeFileLocally(this.selectedFile);
            this.showStatus('File stored locally', 'success');
            this.uploadBtn.disabled = true;
            setTimeout(() => this.loadFileList(), 500);
        }
    }
    
    async storeFileLocally(file) {
        if ('indexedDB' in window) {
            const request = indexedDB.open('FileDB', 1);
            
            request.onupgradeneeded = () => {
                const db = request.result;
                if (!db.objectStoreNames.contains('files')) {
                    db.createObjectStore('files', { keyPath: 'id', autoIncrement: true });
                }
            };
            
            request.onsuccess = () => {
                const db = request.result;
                const transaction = db.transaction(['files'], 'readwrite');
                const store = transaction.objectStore('files');
                store.add({
                    name: file.name,
                    size: file.size,
                    type: file.type,
                    data: file,
                    uploadDate: new Date().toISOString()
                });
            };
        }
    }
    
    loadFileList() {
        // Load files from local storage only
        this.loadFilesFromIndexedDB();
    }
    
    loadFilesFromIndexedDB() {
        if ('indexedDB' in window) {
            const request = indexedDB.open('FileDB', 1);
            
            request.onsuccess = () => {
                const db = request.result;
                const transaction = db.transaction(['files'], 'readonly');
                const store = transaction.objectStore('files');
                const getAllRequest = store.getAll();
                
                getAllRequest.onsuccess = () => {
                    this.displayFiles(getAllRequest.result);
                };
            };
        }
    }
    
    displayFiles(files) {
        if (!files || files.length === 0) {
            this.fileListContainer.innerHTML = '<div class="empty-message">No files uploaded yet</div>';
            return;
        }
        
        this.fileListContainer.innerHTML = '';
        
        files.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            const fileName = document.createElement('div');
            fileName.className = 'file-name';
            fileName.textContent = file.name;
            
            const fileSize = document.createElement('div');
            fileSize.className = 'file-size';
            fileSize.textContent = this.formatFileSize(file.size);
            
            const downloadBtn = document.createElement('button');
            downloadBtn.className = 'download-btn';
            downloadBtn.textContent = '⬇️ Download';
            downloadBtn.addEventListener('click', () => this.downloadFile(file, index));
            
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-btn';
            deleteBtn.textContent = '🗑️ Delete';
            deleteBtn.addEventListener('click', () => this.deleteFile(index));
            
            fileItem.appendChild(fileName);
            fileItem.appendChild(fileSize);
            fileItem.appendChild(downloadBtn);
            fileItem.appendChild(deleteBtn);
            
            this.fileListContainer.appendChild(fileItem);
        });
    }
    
    downloadFile(file, index) {
        if (file.data instanceof Blob) {
            // Local file from IndexedDB
            const url = URL.createObjectURL(file.data);
            const a = document.createElement('a');
            a.href = url;
            a.download = file.name;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } else {
            // Server file
            const a = document.createElement('a');
            a.href = `api/download/${index}`;
            a.download = file.name;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }
    }
    
    deleteFile(index) {
        if (confirm('Are you sure you want to delete this file?')) {
            if ('indexedDB' in window) {
                const request = indexedDB.open('FileDB', 1);
                
                request.onsuccess = () => {
                    const db = request.result;
                    const transaction = db.transaction(['files'], 'readwrite');
                    const store = transaction.objectStore('files');
                    store.delete(index + 1);
                    
                    this.loadFileList();
                };
            }
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }
    
    showStatus(message, type = '') {
        this.uploadStatus.textContent = message;
        this.uploadStatus.className = 'status ' + type;
    }

    showAnnotateStatus(message, type = '') {
        if (!this.annotateStatus) return;
        this.annotateStatus.textContent = message;
        this.annotateStatus.className = 'status ' + type;
    }

    async loadFramesFromIndexedDB() {
        if (!('indexedDB' in window)) return [];

        return new Promise((resolve) => {
            const request = indexedDB.open('FrameDB', 1);

            request.onerror = () => resolve([]);
            request.onsuccess = () => {
                try {
                    const db = request.result;
                    const transaction = db.transaction(['frames'], 'readonly');
                    const store = transaction.objectStore('frames');
                    const getAllRequest = store.getAll();
                    getAllRequest.onsuccess = () => resolve(getAllRequest.result || []);
                    getAllRequest.onerror = () => resolve([]);
                } catch (err) {
                    resolve([]);
                }
            };
        });
    }

    async annotateFrameBlob(blob, label) {
        const image = await createImageBitmap(blob);
        const canvas = document.createElement('canvas');
        canvas.width = image.width;
        canvas.height = image.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(image, 0, 0);

        const fontScale = Math.max(0.6, Math.min(1.2, canvas.width / 800));
        const fontSize = Math.round(24 * fontScale);
        ctx.font = `${fontSize}px Arial`;
        ctx.fillStyle = '#00ff00';
        ctx.strokeStyle = '#003300';
        ctx.lineWidth = 2;
        const margin = 20;
        const x = margin;
        const y = canvas.height - margin;
        ctx.strokeText(label, x, y);
        ctx.fillText(label, x, y);

        return new Promise((resolve) => {
            canvas.toBlob((outBlob) => resolve(outBlob), 'image/jpeg', 0.9);
        });
    }

    async annotateFrames() {
        this.showAnnotateStatus('Applying corrected labels...', 'uploading');
        try {
            const utils = window.DetectionUtils;
            if (!utils) throw new Error('Detection utilities not available');

            const corrected = utils.getCorrectedLog();
            if (!Array.isArray(corrected) || corrected.length === 0) {
                throw new Error('No corrected log entries available');
            }

            const frames = await this.loadFramesFromIndexedDB();
            if (!frames.length) {
                throw new Error('No frames available in local storage');
            }

            const frameIndex = new Map();
            frames.forEach((entry) => {
                if (entry && Number.isFinite(entry.frameNumber)) {
                    frameIndex.set(entry.frameNumber, entry.frame);
                }
            });

            const annotated = [];
            for (const entry of corrected) {
                const range = entry.frame || entry.frameRange;
                const label = entry.string || entry.label;
                if (!range || !label) continue;

                const [startStr, endStr] = range.split('-', 2);
                const start = parseInt(startStr, 10);
                const end = parseInt(endStr, 10);
                if (!Number.isFinite(start) || !Number.isFinite(end)) continue;

                for (let frameNum = start; frameNum <= end; frameNum++) {
                    const blob = frameIndex.get(frameNum);
                    if (!blob) continue;
                    const annotatedBlob = await this.annotateFrameBlob(blob, label);
                    if (annotatedBlob) {
                        annotated.push({
                            name: `frame_${String(frameNum).padStart(5, '0')}.jpg`,
                            blob: annotatedBlob
                        });
                    }
                }
            }

            this.annotatedFrames = annotated;
            this.showAnnotateStatus(`Annotated ${annotated.length} frames.`, 'success');
        } catch (err) {
            this.showAnnotateStatus('Annotation error: ' + err.message, 'error');
        }
    }

    async downloadAnnotatedFrames() {
        this.showAnnotateStatus('Preparing download...', 'uploading');
        try {
            if (!window.JSZip) {
                throw new Error('JSZip not available');
            }
            if (!this.annotatedFrames || this.annotatedFrames.length === 0) {
                throw new Error('No annotated frames available. Run annotation first.');
            }

            const zip = new window.JSZip();
            this.annotatedFrames.forEach((item) => {
                if (item?.name && item?.blob) {
                    zip.file(item.name, item.blob);
                }
            });

            const blob = await zip.generateAsync({ type: 'blob' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'annotated_frames.zip';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            this.showAnnotateStatus('Download ready.', 'success');
        } catch (err) {
            this.showAnnotateStatus('Download error: ' + err.message, 'error');
        }
    }

    async processVideo() {
        if (!this.selectedFile) {
            this.showStatus('No file selected', 'error');
            return;
        }

        if (this.processVideoBtn) this.processVideoBtn.disabled = true;
        this.showStatus('Video processing is unavailable in browser-only mode.', 'error');

        setTimeout(() => {
            if (this.processVideoBtn) this.processVideoBtn.disabled = false;
        }, 1000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new FileManager();
});
