// Alerts Management JavaScript
class AlertsManager {
    constructor() {
        this.currentFilters = {
            status: 'active',
            priority: 'all',
            type: 'all',
            search: ''
        };
        this.alertsContainer = null;
        this.currentOffset = 0;
        this.loadLimit = 20;
        
        this.init();
    }
    
    init() {
        this.alertsContainer = document.querySelector('#alerts-container');
        this.setupEventListeners();
        this.loadAlerts();
        this.loadAlertStats();
        this.startAutoRefresh();
    }
    
    setupEventListeners() {
        // Filter controls
        const applyFiltersBtn = document.querySelector('#apply-filters');
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', () => this.applyFilters());
        }
        
        const clearFiltersBtn = document.querySelector('#clear-filters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => this.clearFilters());
        }
        
        // Search button
        const searchBtn = document.querySelector('#search-button');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.performSearch());
        }
        
        // Refresh button
        const refreshBtn = document.querySelector('#refresh-alerts');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshAlerts());
        }
        
        // Mark all read
        const markAllReadBtn = document.querySelector('#mark-all-read');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => this.markAllRead());
        }
        
        // Load more button
        const loadMoreBtn = document.querySelector('#load-more');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', () => this.loadMoreAlerts());
        }
        
        // Export button
        const exportBtn = document.querySelector('#export-alerts');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportAlerts());
        }
        
        // Filter inputs
        document.querySelectorAll('select[name], input[name]').forEach(input => {
            if (input.name !== 'search') {
                input.addEventListener('change', () => {
                    this.currentFilters[input.name] = input.value;
                    this.applyFilters();
                });
            }
        });
        
        // Search with debounce
        const searchInput = document.querySelector('#search-input');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.currentFilters.search = e.target.value;
                    this.performSearch();
                }, 300);
            });
            
            // Enter key support for search
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch();
                }
            });
        }
    }
    
    async loadAlerts(reset = false) {
        try {
            if (reset) {
                this.currentOffset = 0;
                if (this.alertsContainer) {
                    this.alertsContainer.innerHTML = '';
                }
            }
            
            const params = new URLSearchParams({
                ...this.currentFilters,
                offset: this.currentOffset,
                limit: this.loadLimit
            });
            
            const response = await fetch(`/api/alerts?${params}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.renderAlerts(data.alerts || [], reset);
            this.updateLoadMoreButton(data.has_more || false);
            
        } catch (error) {
            console.error('Error loading alerts:', error);
            this.showError('Failed to load alerts. Please try again.');
        }
    }
    
    async loadAlertStats() {
        try {
            const response = await fetch('/api/alerts/stats');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const stats = await response.json();
            this.updateStatsDisplay(stats);
            
        } catch (error) {
            console.error('Error loading alert stats:', error);
        }
    }
    
    renderAlerts(alerts, reset = false) {
        if (!this.alertsContainer) return;
        
        if (reset) {
            this.alertsContainer.innerHTML = '';
        }
        
        if (alerts.length === 0 && reset) {
            this.alertsContainer.innerHTML = `
                <div class="empty-state text-center py-5">
                    <i class="fas fa-bell-slash fa-3x text-muted mb-3"></i>
                    <h5>No Alerts Found</h5>
                    <p class="text-muted">Try adjusting your filters or check back later.</p>
                </div>
            `;
            return;
        }
        
        const alertsHTML = alerts.map(alert => this.createAlertHTML(alert)).join('');
        this.alertsContainer.insertAdjacentHTML('beforeend', alertsHTML);
        
        this.currentOffset += alerts.length;
    }
    
    createAlertHTML(alert) {
        const priorityClass = this.getPriorityClass(alert.priority);
        const statusClass = this.getStatusClass(alert.status);
        const timeAgo = this.formatTimeAgo(alert.created_at);
        
        return `
            <div class="alert-item border rounded mb-3 p-3 ${alert.read ? '' : 'border-primary'}" data-alert-id="${alert._id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="d-flex align-items-center mb-2">
                            <span class="badge ${priorityClass} me-2">${alert.priority.toUpperCase()}</span>
                            <span class="badge ${statusClass} me-2">${alert.status.toUpperCase()}</span>
                            <small class="text-muted">${timeAgo}</small>
                        </div>
                        <h6 class="mb-1">${this.getAlertTypeIcon(alert.type)} ${alert.title}</h6>
                        <p class="mb-2 text-muted">${alert.description}</p>
                        
                        ${alert.transaction_id ? `
                            <div class="alert-details">
                                <small class="text-muted">
                                    <strong>Transaction:</strong> ${alert.transaction_id} | 
                                    <strong>Amount:</strong> ${this.formatCurrency(alert.amount, alert.currency)} |
                                    <strong>Risk Score:</strong> ${(alert.risk_score * 100).toFixed(1)}%
                                </small>
                            </div>
                        ` : ''}
                        
                        ${alert.account_id ? `
                            <div class="alert-details">
                                <small class="text-muted">
                                    <strong>Account:</strong> ${alert.account_id}
                                </small>
                            </div>
                        ` : ''}
                    </div>
                    
                    <div class="alert-actions">
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="alertsManager.viewAlert('${alert._id}')">
                                View
                            </button>
                            ${alert.status === 'active' ? `
                                <button class="btn btn-outline-success" onclick="alertsManager.resolveAlert('${alert._id}')">
                                    Resolve
                                </button>
                                <button class="btn btn-outline-warning" onclick="alertsManager.investigateAlert('${alert._id}')">
                                    Investigate
                                </button>
                            ` : ''}
                            <button class="btn btn-outline-secondary" onclick="alertsManager.dismissAlert('${alert._id}')">
                                Dismiss
                            </button>
                        </div>
                    </div>
                </div>
                
                ${alert.notes && Array.isArray(alert.notes) && alert.notes.length > 0 ? `
                    <div class="alert-notes mt-3 pt-3 border-top">
                        <h6>Notes:</h6>
                        ${alert.notes.map(note => `
                            <div class="note-item mb-2">
                                <small class="text-muted">${this.formatDateTime(note.created_at)} - ${note.user}</small>
                                <p class="mb-0">${note.content}</p>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    updateStatsDisplay(stats) {
        // Update stat cards using ID selectors
        const statElements = {
            'active-alerts': stats.active_alerts || 0,
            'high-priority-alerts': stats.high_priority || 0,
            'resolved-alerts': stats.resolved_today || 0,
            'avg-response-time': this.formatResponseTime(stats.avg_response_time || 0)
        };
        
        Object.entries(statElements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }
    
    updateLoadMoreButton(hasMore) {
        const loadMoreBtn = document.querySelector('#load-more');
        if (loadMoreBtn) {
            loadMoreBtn.style.display = hasMore ? 'block' : 'none';
        }
    }
    
    // Alert actions
    async viewAlert(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}`);
            const alert = await response.json();
            
            this.showAlertDetailsModal(alert);
            
            // Mark as read
            if (!alert.read) {
                await this.markAsRead(alertId);
            }
            
        } catch (error) {
            console.error('Error viewing alert:', error);
        }
    }
    
    async resolveAlert(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notes: 'Resolved via web interface' })
            });
            
            if (response.ok) {
                this.refreshAlerts();
                this.showNotification('Alert resolved successfully', 'success');
            } else {
                const errorData = await response.json();
                this.showNotification(errorData.message || 'Error resolving alert', 'error');
            }
            
        } catch (error) {
            console.error('Error resolving alert:', error);
            this.showNotification('Error resolving alert', 'error');
        }
    }
    
    async investigateAlert(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/investigate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notes: 'Investigation started via web interface' })
            });
            
            if (response.ok) {
                this.refreshAlerts();
                this.showNotification('Investigation started', 'info');
            } else {
                const errorData = await response.json();
                this.showNotification(errorData.message || 'Error starting investigation', 'error');
            }
            
        } catch (error) {
            console.error('Error starting investigation:', error);
            this.showNotification('Error starting investigation', 'error');
        }
    }
    
    async dismissAlert(alertId) {
        if (!confirm('Are you sure you want to dismiss this alert?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/alerts/${alertId}/dismiss`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notes: 'Dismissed via web interface' })
            });
            
            if (response.ok) {
                this.refreshAlerts();
                this.showNotification('Alert dismissed', 'info');
            } else {
                const errorData = await response.json();
                this.showNotification(errorData.message || 'Error dismissing alert', 'error');
            }
            
        } catch (error) {
            console.error('Error dismissing alert:', error);
            this.showNotification('Error dismissing alert', 'error');
        }
    }
    
    async markAsRead(alertId) {
        try {
            await fetch(`/api/alerts/${alertId}/read`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            
            // Update UI
            const alertElement = document.querySelector(`[data-alert-id="${alertId}"]`);
            if (alertElement) {
                alertElement.classList.remove('border-primary');
            }
            
        } catch (error) {
            console.error('Error marking alert as read:', error);
        }
    }
    
    async markAllRead() {
        try {
            const response = await fetch('/api/alerts/read-all', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.currentFilters)
            });
            
            if (response.ok) {
                this.refreshAlerts();
                this.showNotification('All alerts marked as read', 'success');
            }
            
        } catch (error) {
            console.error('Error marking all alerts as read:', error);
            this.showNotification('Error marking alerts as read', 'error');
        }
    }
    
    // Modal functions
    showAlertDetailsModal(alert) {
        const modal = document.getElementById('alert-modal');
        if (!modal) {
            console.error('Alert modal not found');
            return;
        }
        
        modal.querySelector('.modal-header h2').textContent = alert.title;
        modal.querySelector('#alert-details').innerHTML = `
            <div class="alert-detail-grid">
                <div class="alert-detail-label">Type:</div>
                <div class="alert-detail-value">${alert.type || 'Unknown'}</div>
                
                <div class="alert-detail-label">Priority:</div>
                <div class="alert-detail-value">
                    <span class="alert-priority ${alert.priority || 'medium'}">${(alert.priority || 'medium').toUpperCase()}</span>
                </div>
                
                <div class="alert-detail-label">Status:</div>
                <div class="alert-detail-value">
                    <span class="alert-status ${alert.status || 'active'}">${(alert.status || 'active').toUpperCase()}</span>
                </div>
                
                <div class="alert-detail-label">Created:</div>
                <div class="alert-detail-value">${this.formatDateTime(alert.created_at || alert.timestamp)}</div>
                
                <div class="alert-detail-label">Description:</div>
                <div class="alert-detail-value">${alert.description || alert.message || 'No description available'}</div>
                
                ${alert.transaction_id ? `
                    <div class="alert-detail-label">Transaction ID:</div>
                    <div class="alert-detail-value">
                        <a href="/network?transaction=${alert.transaction_id}" class="btn btn-sm btn-outline">
                            <i class="fas fa-external-link-alt"></i> ${alert.transaction_id}
                        </a>
                    </div>
                ` : ''}
                
                ${alert.account_id ? `
                    <div class="alert-detail-label">Account ID:</div>
                    <div class="alert-detail-value">${alert.account_id}</div>
                ` : ''}
                
                ${alert.risk_score ? `
                    <div class="alert-detail-label">Risk Score:</div>
                    <div class="alert-detail-value">
                        <span class="info-value ${alert.risk_score >= 0.7 ? 'risk-high' : alert.risk_score >= 0.4 ? 'risk-medium' : 'risk-low'}">
                            ${(alert.risk_score * 100).toFixed(1)}%
                        </span>
                    </div>
                ` : ''}
            </div>
            
            <div style="margin-top: var(--spacing-lg); padding-top: var(--spacing-md); border-top: 1px solid var(--border-color);">
                <h4 style="color: var(--primary-color); margin-bottom: var(--spacing-md);">
                    <i class="fas fa-sticky-note"></i> Add Note
                </h4>
                <div style="display: flex; gap: var(--spacing-sm);">
                    <input type="text" id="alert-note-input" placeholder="Add a note..." 
                           class="form-input" style="flex: 1;">
                    <button class="btn btn-primary" onclick="alertsManager.addNote('${alert._id || alert.id}')">
                        <i class="fas fa-plus"></i> Add
                    </button>
                </div>
            </div>
        `;
        
        // Show modal using our custom modal system
        modal.style.display = 'flex';
        modal.classList.add('show');
        
        // Add close functionality
        const closeButtons = modal.querySelectorAll('.modal-close');
        closeButtons.forEach(btn => {
            btn.onclick = () => {
                modal.style.display = 'none';
                modal.classList.remove('show');
            };
        });
        
        // Close on backdrop click
        modal.onclick = (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
                modal.classList.remove('show');
            }
        };
    }
    
    async addNote(alertId) {
        const noteInput = document.getElementById('alert-note-input');
        const noteContent = noteInput.value.trim();
        
        if (!noteContent) return;
        
        try {
            const response = await fetch(`/api/alerts/${alertId}/notes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: noteContent })
            });
            
            if (response.ok) {
                noteInput.value = '';
                this.showNotification('Note added successfully', 'success');
                // Refresh the modal or alert list
                this.viewAlert(alertId);
            }
            
        } catch (error) {
            console.error('Error adding note:', error);
            this.showNotification('Error adding note', 'error');
        }
    }
    
    // Utility functions
    applyFilters() {
        this.loadAlerts(true);
        this.loadAlertStats();
    }
    
    clearFilters() {
        this.currentFilters = {
            status: 'active',
            priority: 'all',
            type: 'all',
            search: ''
        };
        
        // Reset form inputs
        document.querySelectorAll('select[name], input[name]').forEach(input => {
            if (input.name === 'status') {
                input.value = 'active';
            } else if (input.name === 'search') {
                input.value = '';
            } else {
                input.value = 'all';
            }
        });
        
        this.applyFilters();
    }
    
    refreshAlerts() {
        this.loadAlerts(true);
        this.loadAlertStats();
    }
    
    loadMoreAlerts() {
        this.loadAlerts(false);
    }
    
    exportAlerts() {
        const params = new URLSearchParams(this.currentFilters);
        params.set('export', 'true');
        
        window.open(`/api/alerts/export?${params}`, '_blank');
    }
    
    startAutoRefresh() {
        // Refresh every 30 seconds
        setInterval(() => {
            this.loadAlertStats();
        }, 30000);
    }
    
    // Helper functions
    getPriorityClass(priority) {
        switch(priority) {
            case 'high': return 'bg-danger';
            case 'medium': return 'bg-warning text-dark';
            case 'low': return 'bg-info';
            default: return 'bg-secondary';
        }
    }
    
    getStatusClass(status) {
        switch(status) {
            case 'active': return 'bg-success';
            case 'investigating': return 'bg-warning text-dark';
            case 'resolved': return 'bg-primary';
            case 'dismissed': return 'bg-secondary';
            default: return 'bg-light text-dark';
        }
    }
    
    getAlertTypeIcon(type) {
        switch(type) {
            case 'suspicious_transaction': return '<i class="fas fa-exclamation-triangle text-warning"></i>';
            case 'high_amount': return '<i class="fas fa-dollar-sign text-danger"></i>';
            case 'unusual_pattern': return '<i class="fas fa-chart-line text-info"></i>';
            case 'structuring': return '<i class="fas fa-layer-group text-warning"></i>';
            default: return '<i class="fas fa-bell text-muted"></i>';
        }
    }
    
    formatTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return `${days}d ago`;
    }
    
    async applyFilters() {
        // Get current filter values
        this.currentFilters.status = document.getElementById('status-filter')?.value || 'all';
        this.currentFilters.priority = document.getElementById('priority-filter')?.value || 'all';
        this.currentFilters.type = document.getElementById('type-filter')?.value || 'all';
        this.currentFilters.date = document.getElementById('date-filter')?.value || '';
        this.currentFilters.search = document.getElementById('search-input')?.value || '';
        
        // Reset pagination and reload alerts
        this.currentOffset = 0;
        await this.loadAlerts(true);
        this.showNotification('Filters applied successfully', 'success');
    }
    
    async clearFilters() {
        // Reset all filters
        document.getElementById('status-filter').value = 'active';
        document.getElementById('priority-filter').value = 'all';
        document.getElementById('type-filter').value = 'all';
        document.getElementById('date-filter').value = '';
        document.getElementById('search-input').value = '';
        
        this.currentFilters = {
            status: 'active',
            priority: 'all',
            type: 'all',
            date: '',
            search: ''
        };
        
        // Reload alerts with cleared filters
        this.currentOffset = 0;
        await this.loadAlerts(true);
        this.showNotification('Filters cleared', 'info');
    }
    
    async performSearch() {
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            this.currentFilters.search = searchInput.value;
            this.currentOffset = 0;
            await this.loadAlerts(true);
            
            if (this.currentFilters.search) {
                this.showNotification(`Searching for: "${this.currentFilters.search}"`, 'info');
            }
        }
    }
    
    async refreshAlerts() {
        this.showNotification('Refreshing alerts...', 'info');
        this.currentOffset = 0;
        await this.loadAlerts(true);
        await this.loadAlertStats();
        this.showNotification('Alerts refreshed successfully', 'success');
    }
    
    async markAllRead() {
        try {
            const response = await fetch('/api/alerts/mark-all-read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            this.showNotification(`Marked ${result.count || 0} alerts as read`, 'success');
            
            // Refresh alerts to show updated read status
            await this.loadAlerts(true);
            await this.loadAlertStats();
            
        } catch (error) {
            console.error('Error marking all as read:', error);
            this.showNotification('Failed to mark alerts as read', 'error');
        }
    }
    
    async exportAlerts() {
        try {
            this.showNotification('Preparing export...', 'info');
            
            const params = new URLSearchParams({
                ...this.currentFilters,
                format: 'csv'
            });
            
            const response = await fetch(`/api/alerts/export?${params}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            // Handle file download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // Generate filename with current date
            const now = new Date();
            const dateStr = now.toISOString().split('T')[0];
            a.download = `alerts_export_${dateStr}.csv`;
            
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            this.showNotification('Export completed successfully', 'success');
            
        } catch (error) {
            console.error('Error exporting alerts:', error);
            this.showNotification('Failed to export alerts', 'error');
        }
    }
    
    async loadMoreAlerts() {
        this.currentOffset += this.loadLimit;
        await this.loadAlerts(false);
    }

    formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
    
    formatResponseTime(hours) {
        // Handle string values like "0h" from API
        if (typeof hours === 'string') {
            return hours;
        }
        
        // Handle numeric values
        if (hours < 1) return `${Math.round(hours * 60)}m`;
        return `${Math.round(hours)}h`;
    }
    
    formatCurrency(amount, currency) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency || 'USD'
        }).format(amount);
    }
    
    showError(message) {
        if (this.alertsContainer) {
            this.alertsContainer.innerHTML = `
                <div class="empty-state text-center py-5">
                    <div class="empty-state-icon">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <h5 style="color: var(--text-primary); margin: var(--spacing-lg) 0 var(--spacing-sm) 0;">Error Loading Alerts</h5>
                    <p style="color: var(--text-secondary); margin-bottom: var(--spacing-lg);">${message}</p>
                    <button class="btn btn-primary" onclick="alertsManager.refreshAlerts()">
                        <i class="fas fa-sync"></i> Retry
                    </button>
                </div>
            `;
        }
    }
    
    showNotification(message, type = 'info') {
        // Create or get notification container
        let notificationContainer = document.querySelector('#notification-container');
        if (!notificationContainer) {
            notificationContainer = document.createElement('div');
            notificationContainer.id = 'notification-container';
            notificationContainer.className = 'notification-container';
            document.body.appendChild(notificationContainer);
        }
        
        const notification = document.createElement('div');
        const notificationId = 'notification-' + Date.now();
        
        // Get appropriate icon and color
        let icon, bgClass;
        switch (type) {
            case 'success':
                icon = 'fas fa-check-circle';
                bgClass = 'notification-success';
                break;
            case 'error':
            case 'danger':
                icon = 'fas fa-exclamation-triangle';
                bgClass = 'notification-error';
                break;
            case 'warning':
                icon = 'fas fa-exclamation-circle';
                bgClass = 'notification-warning';
                break;
            default:
                icon = 'fas fa-info-circle';
                bgClass = 'notification-info';
        }
        
        notification.id = notificationId;
        notification.className = `notification ${bgClass}`;
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">
                    <i class="${icon}"></i>
                </div>
                <div class="notification-message">${message}</div>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        notificationContainer.appendChild(notification);
        
        // Trigger animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Auto-remove after 4 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 4000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.alertsManager = new AlertsManager();
});