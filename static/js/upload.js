// Upload functionality for AML Detection Platform
class UploadManager {
    constructor() {
        this.fileInput = document.getElementById('file-input');
        this.uploadZone = document.getElementById('upload-zone');
        this.fileInfo = document.getElementById('file-info');
        this.fileName = document.getElementById('file-name');
        this.fileSize = document.getElementById('file-size');
        this.uploadBtn = document.getElementById('upload-btn');
        this.browseFiles = document.getElementById('browse-files');
        this.removeFile = document.getElementById('remove-file');
        this.progressFill = document.getElementById('progress-fill');
        this.progressText = document.getElementById('progress-text');
        this.uploadProgress = document.getElementById('upload-progress');
        
        this.selectedFile = null;
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadRecentUploads();
    }
    
    setupEventListeners() {
        // File input change
        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }
        
        // Browse files click
        if (this.browseFiles) {
            this.browseFiles.addEventListener('click', () => this.fileInput.click());
        }
        
        // Upload zone drag and drop
        if (this.uploadZone) {
            this.uploadZone.addEventListener('dragover', (e) => this.handleDragOver(e));
            this.uploadZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
            this.uploadZone.addEventListener('drop', (e) => this.handleDrop(e));
        }
        
        // Remove file
        if (this.removeFile) {
            this.removeFile.addEventListener('click', () => this.clearFile());
        }
        
        // Upload button
        if (this.uploadBtn) {
            this.uploadBtn.addEventListener('click', () => this.uploadFile());
        }
        
        // Refresh uploads
        const refreshBtn = document.getElementById('refresh-uploads');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadRecentUploads());
        }
        
        // Upload another file
        const uploadAnotherBtn = document.getElementById('upload-another');
        if (uploadAnotherBtn) {
            uploadAnotherBtn.addEventListener('click', () => this.resetUploadForm());
        }
    }
    
    handleDragOver(e) {
        e.preventDefault();
        this.uploadZone.classList.add('dragover');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        this.uploadZone.classList.remove('dragover');
    }
    
    handleDrop(e) {
        e.preventDefault();
        this.uploadZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }
    
    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.processFile(file);
        }
    }
    
    processFile(file) {
        // Validate file type
        const allowedTypes = ['.csv', '.xlsx', '.xls'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            this.showAlert('Error', 'Please select a CSV, XLSX, or XLS file.', 'error');
            return;
        }
        
        // Validate file size (16MB limit)
        const maxSize = 16 * 1024 * 1024; // 16MB in bytes
        if (file.size > maxSize) {
            this.showAlert('Error', 'File size exceeds 16MB limit.', 'error');
            return;
        }
        
        this.selectedFile = file;
        this.displayFileInfo(file);
    }
    
    displayFileInfo(file) {
        if (this.fileName) this.fileName.textContent = file.name;
        if (this.fileSize) this.fileSize.textContent = this.formatFileSize(file.size);
        
        if (this.fileInfo) this.fileInfo.style.display = 'block';
        if (this.uploadBtn) this.uploadBtn.disabled = false;
    }
    
    clearFile() {
        this.selectedFile = null;
        if (this.fileInput) this.fileInput.value = '';
        if (this.fileInfo) this.fileInfo.style.display = 'none';
        if (this.uploadBtn) this.uploadBtn.disabled = true;
        if (this.uploadProgress) this.uploadProgress.style.display = 'none';
    }
    
    async uploadFile() {
        if (!this.selectedFile) {
            this.showAlert('Error', 'Please select a file to upload.', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', this.selectedFile);
        
        // Get upload options
        const runAnalysis = document.getElementById('run-analysis');
        const generateAlerts = document.getElementById('generate-alerts');
        
        if (runAnalysis && runAnalysis.checked) {
            formData.append('run_analysis', 'true');
        }
        
        if (generateAlerts && generateAlerts.checked) {
            formData.append('generate_alerts', 'true');
        }
        
        try {
            this.showUploadProgress();
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showUploadResults(result);
            } else {
                throw new Error(result.error || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showAlert('Upload Failed', error.message, 'error');
            this.hideUploadProgress();
        }
    }
    
    showUploadProgress() {
        if (this.uploadProgress) {
            this.uploadProgress.style.display = 'block';
        }
        
        if (this.uploadBtn) {
            this.uploadBtn.disabled = true;
            this.uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
        }
        
        // Simulate progress for better UX
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) {
                progress = 90;
                clearInterval(progressInterval);
            }
            this.updateProgress(progress);
        }, 200);
        
        // Store interval reference to clear it later
        this.progressInterval = progressInterval;
    }
    
    hideUploadProgress() {
        if (this.uploadProgress) {
            this.uploadProgress.style.display = 'none';
        }
        
        if (this.uploadBtn) {
            this.uploadBtn.disabled = false;
            this.uploadBtn.innerHTML = '<i class="fas fa-upload"></i> Upload Dataset';
        }
        
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
    }
    
    updateProgress(percentage) {
        if (this.progressFill) {
            this.progressFill.style.width = `${percentage}%`;
        }
        
        if (this.progressText) {
            this.progressText.textContent = `${Math.round(percentage)}%`;
        }
    }
    
    showUploadResults(result) {
        this.hideUploadProgress();
        this.updateProgress(100);
        
        const resultsDiv = document.getElementById('upload-results');
        const resultsContent = document.getElementById('results-content');
        
        if (resultsDiv && resultsContent) {
            resultsContent.innerHTML = this.generateResultsHTML(result);
            resultsDiv.style.display = 'block';
            
            // Scroll to results
            resultsDiv.scrollIntoView({ behavior: 'smooth' });
        }
        
        // Hide upload form
        const uploadCard = document.querySelector('.upload-card');
        if (uploadCard) {
            uploadCard.style.display = 'none';
        }
        
        // Refresh recent uploads
        this.loadRecentUploads();
    }
    
    generateResultsHTML(result) {
        const riskColor = result.average_risk > 0.7 ? 'danger' : result.average_risk > 0.4 ? 'warning' : 'success';
        
        return `
            <div class="results-summary">
                <div class="result-item">
                    <div class="result-icon success">
                        <i class="fas fa-check-circle"></i>
                    </div>
                    <div class="result-content">
                        <h4>Upload Successful</h4>
                        <p>File "${result.filename || 'Unknown'}" processed</p>
                    </div>
                </div>
                
                <div class="result-item">
                    <div class="result-icon">
                        <i class="fas fa-database"></i>
                    </div>
                    <div class="result-content">
                        <h4>Records Processed</h4>
                        <p>${result.records_processed || 0} transactions</p>
                    </div>
                </div>
                
                <div class="result-item">
                    <div class="result-icon warning">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <div class="result-content">
                        <h4>Suspicious Transactions</h4>
                        <p>${result.suspicious_count || 0} flagged for review</p>
                    </div>
                </div>
                
                <div class="result-item">
                    <div class="result-icon ${riskColor}">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <div class="result-content">
                        <h4>Average Risk Score</h4>
                        <p>${(result.average_risk * 100).toFixed(1)}%</p>
                    </div>
                </div>
                
                <div class="result-item">
                    <div class="result-icon">
                        <i class="fas fa-dollar-sign"></i>
                    </div>
                    <div class="result-content">
                        <h4>Total Volume</h4>
                        <p>$${result.total_volume ? result.total_volume.toLocaleString() : '0'}</p>
                    </div>
                </div>
                
                <div class="result-item">
                    <div class="result-icon">
                        <i class="fas fa-coins"></i>
                    </div>
                    <div class="result-content">
                        <h4>Currencies Found</h4>
                        <p>${result.currencies_found ? result.currencies_found.join(', ') : 'USD'}</p>
                    </div>
                </div>
            </div>
            
            ${result.errors && result.errors.length > 0 ? `
                <div class="upload-warnings">
                    <h4><i class="fas fa-exclamation-triangle"></i> Processing Warnings</h4>
                    <ul>
                        ${result.errors.slice(0, 10).map(error => `<li>${error}</li>`).join('')}
                        ${result.errors.length > 10 ? `<li>... and ${result.errors.length - 10} more warnings</li>` : ''}
                    </ul>
                </div>
            ` : ''}
            
            <div class="upload-summary">
                <div class="summary-stats">
                    <div class="stat-badge">
                        <span class="stat-label">AI Analysis</span>
                        <span class="stat-value ${result.ai_analysis_enabled ? 'enabled' : 'disabled'}">
                            ${result.ai_analysis_enabled ? 'Enabled' : 'Disabled'}
                        </span>
                    </div>
                    <div class="stat-badge">
                        <span class="stat-label">Alert Generation</span>
                        <span class="stat-value ${result.alert_generation_enabled ? 'enabled' : 'disabled'}">
                            ${result.alert_generation_enabled ? 'Enabled' : 'Disabled'}
                        </span>
                    </div>
                    ${result.alerts_generated ? `
                    <div class="stat-badge">
                        <span class="stat-label">Alerts Generated</span>
                        <span class="stat-value">${result.alerts_generated}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    resetUploadForm() {
        // Hide results
        const resultsDiv = document.getElementById('upload-results');
        if (resultsDiv) {
            resultsDiv.style.display = 'none';
        }
        
        // Show upload form
        const uploadCard = document.querySelector('.upload-card');
        if (uploadCard) {
            uploadCard.style.display = 'block';
        }
        
        // Clear file
        this.clearFile();
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    async loadRecentUploads() {
        try {
            const response = await fetch('/api/uploads/recent');
            const uploads = await response.json();
            
            const tbody = document.getElementById('recent-uploads-tbody');
            if (tbody && uploads) {
                tbody.innerHTML = uploads.map(upload => `
                    <tr>
                        <td>${upload.filename}</td>
                        <td>${new Date(upload.upload_date).toLocaleString()}</td>
                        <td>${upload.records_processed}</td>
                        <td>
                            <span class="badge ${upload.suspicious_count > 0 ? 'badge-warning' : 'badge-success'}">
                                ${upload.suspicious_count}
                            </span>
                        </td>
                        <td>
                            <span class="badge badge-${upload.status === 'completed' ? 'success' : 'warning'}">
                                ${upload.status}
                            </span>
                        </td>
                        <td>
                            <button class="btn btn-sm btn-outline" onclick="viewUploadDetails('${upload._id}')">
                                <i class="fas fa-eye"></i> View
                            </button>
                        </td>
                    </tr>
                `).join('');
            }
        } catch (error) {
            console.error('Error loading recent uploads:', error);
        }
    }
    
    formatFileSize(bytes) {
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Bytes';
        
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    showAlert(title, message, type = 'info') {
        // Create alert modal or notification
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.innerHTML = `
            <div class="alert-content">
                <h4>${title}</h4>
                <p>${message}</p>
                <button class="btn btn-sm btn-primary" onclick="this.parentElement.parentElement.remove()">
                    OK
                </button>
            </div>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentElement) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Global function for viewing upload details
function viewUploadDetails(uploadId) {
    // Implement upload details view
    window.location.href = `/uploads/${uploadId}`;
}

// Initialize upload manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.upload-page')) {
        new UploadManager();
    }
});

// Add custom styles for upload functionality
const uploadStyles = `
<style>
.upload-zone {
    border: 2px dashed var(--border-color);
    border-radius: var(--radius-lg);
    padding: 3rem;
    text-align: center;
    transition: all 0.3s ease;
    cursor: pointer;
}

.upload-zone:hover,
.upload-zone.dragover {
    border-color: var(--accent-color);
    background: rgba(255, 122, 69, 0.05);
}

.upload-icon {
    font-size: 4rem;
    color: var(--accent-color);
    margin-bottom: 1rem;
}

.upload-text h3 {
    margin-bottom: 0.5rem;
    color: var(--text-primary);
}

.upload-text p {
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
}

.upload-link {
    color: var(--accent-color);
    cursor: pointer;
    text-decoration: underline;
}

.upload-link:hover {
    color: var(--accent-hover);
}

.file-details {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: var(--background-color);
    border-radius: var(--radius-md);
    margin-bottom: 1rem;
}

.file-icon {
    font-size: 2rem;
    color: var(--accent-color);
}

.file-meta {
    flex: 1;
}

.file-name {
    font-weight: bold;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
}

.file-size {
    color: var(--text-secondary);
    font-size: 0.875rem;
}

.remove-file {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0.5rem;
    border-radius: var(--radius-md);
    transition: all 0.2s ease;
}

.remove-file:hover {
    background: var(--danger-color);
    color: white;
}

.progress-bar {
    width: 100%;
    height: 8px;
    background: var(--background-color);
    border-radius: var(--radius-sm);
    overflow: hidden;
    margin-bottom: 0.5rem;
}

.progress-fill {
    height: 100%;
    background: var(--accent-color);
    transition: width 0.3s ease;
}

.progress-text {
    text-align: center;
    color: var(--text-secondary);
    font-size: 0.875rem;
}

.results-summary {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}

.result-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: var(--background-color);
    border-radius: var(--radius-md);
}

.result-icon {
    font-size: 2rem;
    color: var(--text-secondary);
}

.result-icon.success {
    color: var(--success-color);
}

.result-icon.warning {
    color: var(--warning-color);
}

.result-content h4 {
    margin-bottom: 0.25rem;
    color: var(--text-primary);
}

.result-content p {
    color: var(--text-secondary);
    font-size: 0.875rem;
}

.upload-warnings {
    padding: 1rem;
    background: rgba(255, 193, 7, 0.1);
    border: 1px solid var(--warning-color);
    border-radius: var(--radius-md);
    margin-bottom: 1rem;
}

.upload-warnings h4 {
    color: var(--warning-color);
    margin-bottom: 0.5rem;
}

.upload-warnings ul {
    margin-left: 1rem;
    color: var(--text-secondary);
}

.alert {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: white;
    border-radius: var(--radius-lg);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    z-index: 10000;
    min-width: 300px;
}

.alert-content {
    padding: 2rem;
    text-align: center;
}

.alert-content h4 {
    margin-bottom: 1rem;
    color: var(--text-primary);
}

.alert-content p {
    margin-bottom: 1.5rem;
    color: var(--text-secondary);
}

.badge {
    padding: 0.25rem 0.5rem;
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: bold;
    text-transform: uppercase;
}

.badge-success {
    background: var(--success-color);
    color: white;
}

.badge-warning {
    background: var(--warning-color);
    color: white;
}

@media (max-width: 768px) {
    .upload-zone {
        padding: 2rem 1rem;
    }
    
    .upload-icon {
        font-size: 3rem;
    }
    
    .file-details {
        flex-direction: column;
        text-align: center;
    }
    
    .results-summary {
        grid-template-columns: 1fr;
    }
    
    .result-item {
        flex-direction: column;
        text-align: center;
    }
}
</style>
`;

// Inject styles
document.head.insertAdjacentHTML('beforeend', uploadStyles);