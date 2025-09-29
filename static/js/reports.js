// Reports JavaScript
class ReportsManager {
    constructor() {
        this.currentReport = null;
        this.reportTemplates = [];
        this.scheduledReports = [];
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadReportTemplates();
        this.loadScheduledReports();
    }
    
    setupEventListeners() {
        // Generate report button
        const generateBtn = document.querySelector('[data-action="generate-report"]');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generateReport());
        }
        
        // Schedule report button
        const scheduleBtn = document.querySelector('[data-action="schedule-report"]');
        if (scheduleBtn) {
            scheduleBtn.addEventListener('click', () => this.showScheduleModal());
        }
        
        // Export buttons
        document.querySelectorAll('[data-export]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const format = e.target.dataset.export;
                this.exportReport(format);
            });
        });
        
        // Report type selector
        const reportTypeSelect = document.querySelector('[name="report_type"]');
        if (reportTypeSelect) {
            reportTypeSelect.addEventListener('change', () => this.updateReportOptions());
        }
        
        // Date range inputs
        document.querySelectorAll('[name="start_date"], [name="end_date"]').forEach(input => {
            input.addEventListener('change', () => this.validateDateRange());
        });
        
        // Quick date buttons
        document.querySelectorAll('[data-quick-date]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const period = e.target.dataset.quickDate;
                this.setQuickDateRange(period);
            });
        });
    }
    
    async loadReportTemplates() {
        try {
            const response = await fetch('/api/reports/templates');
            
            if (response.ok) {
                this.reportTemplates = await response.json();
                this.populateTemplateSelector();
            }
            
        } catch (error) {
            console.error('Error loading report templates:', error);
        }
    }
    
    async loadScheduledReports() {
        try {
            const response = await fetch('/api/reports/scheduled');
            
            if (response.ok) {
                this.scheduledReports = await response.json();
                this.displayScheduledReports();
            }
            
        } catch (error) {
            console.error('Error loading scheduled reports:', error);
        }
    }
    
    populateTemplateSelector() {
        const templateSelect = document.querySelector('[name="template"]');
        if (!templateSelect) return;
        
        templateSelect.innerHTML = '<option value="">Select a template...</option>';
        
        this.reportTemplates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.name;
            templateSelect.appendChild(option);
        });
    }
    
    updateReportOptions() {
        const reportType = document.querySelector('[name="report_type"]')?.value;
        const optionsContainer = document.querySelector('#report-options');
        
        if (!optionsContainer || !reportType) return;
        
        let optionsHTML = '';
        
        switch(reportType) {
            case 'transaction_summary':
                optionsHTML = `
                    <h6>Transaction Summary Options</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="include_risk_analysis" checked>
                                <label class="form-check-label">Include Risk Analysis</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="include_volume_trends" checked>
                                <label class="form-check-label">Include Volume Trends</label>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="include_geographic_data">
                                <label class="form-check-label">Include Geographic Data</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="include_currency_breakdown" checked>
                                <label class="form-check-label">Include Currency Breakdown</label>
                            </div>
                        </div>
                    </div>
                `;
                break;
                
            case 'risk_assessment':
                optionsHTML = `
                    <h6>Risk Assessment Options</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <label class="form-label">Risk Threshold</label>
                            <select class="form-select" name="risk_threshold">
                                <option value="all">All Risk Levels</option>
                                <option value="high" selected>High Risk Only (≥70%)</option>
                                <option value="medium">Medium Risk and Above (≥30%)</option>
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Include Accounts</label>
                            <select class="form-select" name="include_accounts">
                                <option value="flagged">Flagged Accounts Only</option>
                                <option value="high_risk" selected>High Risk Accounts</option>
                                <option value="all">All Accounts</option>
                            </select>
                        </div>
                    </div>
                `;
                break;
                
            case 'compliance_report':
                optionsHTML = `
                    <h6>Compliance Report Options</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="include_regulatory_summary" checked>
                                <label class="form-check-label">Regulatory Summary</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="include_alert_history" checked>
                                <label class="form-check-label">Alert History</label>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="include_investigation_log">
                                <label class="form-check-label">Investigation Log</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="include_action_items">
                                <label class="form-check-label">Action Items</label>
                            </div>
                        </div>
                    </div>
                `;
                break;
        }
        
        optionsContainer.innerHTML = optionsHTML;
    }
    
    setQuickDateRange(period) {
        const startDateInput = document.querySelector('[name="start_date"]');
        const endDateInput = document.querySelector('[name="end_date"]');
        
        if (!startDateInput || !endDateInput) return;
        
        const endDate = new Date();
        let startDate = new Date();
        
        switch(period) {
            case '7d':
                startDate.setDate(endDate.getDate() - 7);
                break;
            case '30d':
                startDate.setDate(endDate.getDate() - 30);
                break;
            case '90d':
                startDate.setDate(endDate.getDate() - 90);
                break;
            case '1y':
                startDate.setFullYear(endDate.getFullYear() - 1);
                break;
            case 'ytd':
                startDate = new Date(endDate.getFullYear(), 0, 1);
                break;
        }
        
        startDateInput.value = this.formatDateForInput(startDate);
        endDateInput.value = this.formatDateForInput(endDate);
        
        // Update active button
        document.querySelectorAll('[data-quick-date]').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-quick-date="${period}"]`)?.classList.add('active');
    }
    
    validateDateRange() {
        const startDate = document.querySelector('[name="start_date"]')?.value;
        const endDate = document.querySelector('[name="end_date"]')?.value;
        
        if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
            this.showNotification('Start date cannot be after end date', 'warning');
            return false;
        }
        
        return true;
    }
    
    async generateReport() {
        if (!this.validateDateRange()) return;
        
        try {
            const formData = this.getReportParameters();
            
            // Show loading state
            this.showLoadingState();
            
            const response = await fetch('/api/reports/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const reportData = await response.json();
            this.currentReport = reportData;
            this.displayReport(reportData);
            
        } catch (error) {
            console.error('Error generating report:', error);
            this.showError('Failed to generate report. Please try again.');
        } finally {
            this.hideLoadingState();
        }
    }
    
    getReportParameters() {
        const form = document.querySelector('#report-form');
        if (!form) return {};
        
        const formData = new FormData(form);
        const parameters = {};
        
        // Convert FormData to object
        for (let [key, value] of formData.entries()) {
            if (parameters[key]) {
                // Handle multiple values (checkboxes)
                if (!Array.isArray(parameters[key])) {
                    parameters[key] = [parameters[key]];
                }
                parameters[key].push(value);
            } else {
                parameters[key] = value;
            }
        }
        
        return parameters;
    }
    
    displayReport(reportData) {
        const reportContainer = document.querySelector('#report-display');
        if (!reportContainer) return;
        
        reportContainer.innerHTML = `
            <div class="report-header border-bottom pb-3 mb-4">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h4>${reportData.title}</h4>
                        <p class="text-muted mb-0">
                            Generated on ${this.formatDateTime(reportData.generated_at)} | 
                            Period: ${this.formatDate(reportData.start_date)} - ${this.formatDate(reportData.end_date)}
                        </p>
                    </div>
                    <div class="btn-group">
                        <button class="btn btn-outline-primary" data-export="pdf">
                            <i class="fas fa-file-pdf"></i> PDF
                        </button>
                        <button class="btn btn-outline-success" data-export="excel">
                            <i class="fas fa-file-excel"></i> Excel
                        </button>
                        <button class="btn btn-outline-info" data-export="csv">
                            <i class="fas fa-file-csv"></i> CSV
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="report-content">
                ${this.generateReportContent(reportData)}
            </div>
        `;
        
        // Re-attach event listeners for export buttons
        reportContainer.querySelectorAll('[data-export]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const format = e.target.dataset.export;
                this.exportReport(format);
            });
        });
    }
    
    generateReportContent(reportData) {
        let content = '';
        
        // Executive Summary
        if (reportData.summary) {
            content += `
                <div class="report-section mb-4">
                    <h5>Executive Summary</h5>
                    <div class="row">
                        <div class="col-md-3">
                            <div class="stat-card text-center p-3 border rounded">
                                <h4 class="text-primary">${reportData.summary.total_transactions || 0}</h4>
                                <small class="text-muted">Total Transactions</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="stat-card text-center p-3 border rounded">
                                <h4 class="text-success">${this.formatCurrency(reportData.summary.total_volume || 0)}</h4>
                                <small class="text-muted">Total Volume</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="stat-card text-center p-3 border rounded">
                                <h4 class="text-warning">${reportData.summary.suspicious_transactions || 0}</h4>
                                <small class="text-muted">Suspicious Transactions</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="stat-card text-center p-3 border rounded">
                                <h4 class="text-danger">${(reportData.summary.avg_risk_score * 100 || 0).toFixed(1)}%</h4>
                                <small class="text-muted">Avg Risk Score</small>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Risk Analysis
        if (reportData.risk_analysis) {
            content += `
                <div class="report-section mb-4">
                    <h5>Risk Analysis</h5>
                    <div class="row">
                        <div class="col-md-6">
                            <canvas id="risk-distribution-chart" width="400" height="200"></canvas>
                        </div>
                        <div class="col-md-6">
                            <div class="risk-breakdown">
                                <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                                    <span>High Risk (≥70%)</span>
                                    <span class="badge bg-danger">${reportData.risk_analysis.high || 0}</span>
                                </div>
                                <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                                    <span>Medium Risk (30-70%)</span>
                                    <span class="badge bg-warning text-dark">${reportData.risk_analysis.medium || 0}</span>
                                </div>
                                <div class="d-flex justify-content-between align-items-center py-2">
                                    <span>Low Risk (<30%)</span>
                                    <span class="badge bg-success">${reportData.risk_analysis.low || 0}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Volume Trends
        if (reportData.volume_trends) {
            content += `
                <div class="report-section mb-4">
                    <h5>Volume Trends</h5>
                    <canvas id="volume-trends-chart" width="800" height="300"></canvas>
                </div>
            `;
        }
        
        // Top Accounts
        if (reportData.top_accounts && reportData.top_accounts.length > 0) {
            content += `
                <div class="report-section mb-4">
                    <h5>Top Risk Accounts</h5>
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Account ID</th>
                                    <th>Risk Score</th>
                                    <th>Transaction Count</th>
                                    <th>Total Volume</th>
                                    <th>Country</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${reportData.top_accounts.map(account => `
                                    <tr>
                                        <td>${account.account_id}</td>
                                        <td>
                                            <span class="badge ${this.getRiskClass(account.risk_score)}">
                                                ${(account.risk_score * 100).toFixed(1)}%
                                            </span>
                                        </td>
                                        <td>${account.transaction_count}</td>
                                        <td>${this.formatCurrency(account.total_volume)}</td>
                                        <td>${account.country || 'N/A'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }
        
        // Currency Breakdown
        if (reportData.currency_breakdown) {
            content += `
                <div class="report-section mb-4">
                    <h5>Currency Breakdown</h5>
                    <div class="row">
                        <div class="col-md-6">
                            <canvas id="currency-chart" width="400" height="200"></canvas>
                        </div>
                        <div class="col-md-6">
                            <div class="currency-list">
                                ${reportData.currency_breakdown.map(currency => `
                                    <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                                        <span>${currency.currency}</span>
                                        <div>
                                            <span class="fw-bold">${this.formatCurrency(currency.total_amount, currency.currency)}</span>
                                            <small class="text-muted ms-2">${currency.percentage.toFixed(1)}%</small>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        return content;
    }
    
    async exportReport(format) {
        if (!this.currentReport) {
            this.showNotification('No report to export', 'warning');
            return;
        }
        
        try {
            const response = await fetch(`/api/reports/export/${format}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.currentReport)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            // Download the file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `aml_report_${new Date().toISOString().split('T')[0]}.${format}`;
            a.click();
            window.URL.revokeObjectURL(url);
            
            this.showNotification(`Report exported as ${format.toUpperCase()}`, 'success');
            
        } catch (error) {
            console.error('Error exporting report:', error);
            this.showNotification('Error exporting report', 'error');
        }
    }
    
    showScheduleModal() {
        const modal = document.getElementById('schedule-modal');
        if (!modal) return;
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
    
    async scheduleReport() {
        const form = document.querySelector('#schedule-form');
        if (!form) return;
        
        try {
            const formData = new FormData(form);
            const scheduleData = Object.fromEntries(formData.entries());
            
            const response = await fetch('/api/reports/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(scheduleData)
            });
            
            if (response.ok) {
                this.showNotification('Report scheduled successfully', 'success');
                this.loadScheduledReports();
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('schedule-modal'));
                modal?.hide();
            }
            
        } catch (error) {
            console.error('Error scheduling report:', error);
            this.showNotification('Error scheduling report', 'error');
        }
    }
    
    displayScheduledReports() {
        const container = document.querySelector('#scheduled-reports');
        if (!container) return;
        
        if (this.scheduledReports.length === 0) {
            container.innerHTML = '<p class="text-muted">No scheduled reports</p>';
            return;
        }
        
        container.innerHTML = this.scheduledReports.map(report => `
            <div class="scheduled-report-item border rounded p-3 mb-2">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${report.name}</h6>
                        <small class="text-muted">${report.frequency} • Next run: ${this.formatDateTime(report.next_run)}</small>
                    </div>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="reportsManager.editScheduledReport('${report.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="reportsManager.deleteScheduledReport('${report.id}')">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    async deleteScheduledReport(reportId) {
        if (!confirm('Are you sure you want to delete this scheduled report?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/reports/schedule/${reportId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showNotification('Scheduled report deleted', 'success');
                this.loadScheduledReports();
            }
            
        } catch (error) {
            console.error('Error deleting scheduled report:', error);
            this.showNotification('Error deleting scheduled report', 'error');
        }
    }
    
    // Helper functions
    showLoadingState() {
        const reportContainer = document.querySelector('#report-display');
        if (reportContainer) {
            reportContainer.innerHTML = `
                <div class="text-center py-5">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="text-muted">Generating report...</p>
                </div>
            `;
        }
    }
    
    hideLoadingState() {
        // Loading state will be replaced by report content
    }
    
    showError(message) {
        const reportContainer = document.querySelector('#report-display');
        if (reportContainer) {
            reportContainer.innerHTML = `
                <div class="error-state text-center py-5">
                    <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                    <h5>Report Generation Failed</h5>
                    <p class="text-muted">${message}</p>
                    <button class="btn btn-primary" onclick="reportsManager.generateReport()">
                        <i class="fas fa-sync"></i> Try Again
                    </button>
                </div>
            `;
        }
    }
    
    getRiskClass(riskScore) {
        if (riskScore >= 0.7) return 'bg-danger';
        if (riskScore >= 0.3) return 'bg-warning text-dark';
        return 'bg-success';
    }
    
    formatCurrency(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    }
    
    formatDateTime(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
    
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString();
    }
    
    formatDateForInput(date) {
        return date.toISOString().split('T')[0];
    }
    
    showNotification(message, type = 'info') {
        const alertContainer = document.querySelector('#notification-container') || document.body;
        const notification = document.createElement('div');
        
        const typeClass = type === 'error' ? 'danger' : type;
        
        notification.className = `alert alert-${typeClass} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.reportsManager = new ReportsManager();
});