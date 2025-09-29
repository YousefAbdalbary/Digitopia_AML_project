// AML Detection Platform - Main JavaScript

class AMLPlatform {
    constructor() {
        this.apiEndpoints = {
            dashboardStats: '/api/dashboard/stats',
            volumeTrends: '/api/dashboard/volume-trends',
            transactions: '/api/transactions',
            networkGraph: '/api/network/graph',
            cashFlowMap: '/api/cash-flow/map',
            multiCurrencyFlow: '/api/cash-flow/multi-currency',
            alerts: '/api/alerts',
            account: '/api/account',
            upload: '/api/upload',
            analyze: '/api/analyze',
            riskCalculate: '/api/risk/calculate'
        };
        
        this.charts = {};
        this.maps = {};
        this.currentTheme = localStorage.getItem('theme') || 'light';
        
        this.init();
    }
    
    init() {
        this.setupTheme();
        this.setupEventListeners();
        this.setupLoading();
    }
    
    setupTheme() {
        document.documentElement.setAttribute('data-theme', this.currentTheme);
        
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            const icon = themeToggle.querySelector('i');
            icon.className = this.currentTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
            
            themeToggle.addEventListener('click', () => {
                this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
                document.documentElement.setAttribute('data-theme', this.currentTheme);
                localStorage.setItem('theme', this.currentTheme);
                
                icon.className = this.currentTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
            });
        }
    }
    
    setupEventListeners() {
        // Global error handling
        window.addEventListener('error', (e) => {
            console.error('Global error:', e);
            // Only show generic error for actual JS errors, not network issues
            if (e.error && e.error.name !== 'NetworkError') {
                this.showNotification('An error occurred. Please try again.', 'error');
            }
        });
        
        // Navigation active state
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }
    
    setupLoading() {
        this.loadingOverlay = document.getElementById('loading-overlay');
    }
    
    showLoading(message = 'Loading...') {
        if (this.loadingOverlay) {
            const loadingText = this.loadingOverlay.querySelector('p');
            if (loadingText) loadingText.textContent = message;
            this.loadingOverlay.classList.add('show');
        }
    }
    
    hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.remove('show');
        }
    }
    
    async apiCall(endpoint, options = {}) {
        try {
            this.showLoading();
            
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                },
            };
            
            const response = await fetch(endpoint, { ...defaultOptions, ...options });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API call failed:', error);
            this.showNotification(`API Error: ${error.message}`, 'error');
            throw error;
        } finally {
            this.hideLoading();
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
        
        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
        
        // Animate in
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
    }
    
    getNotificationIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    }
    
    formatCurrency(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    }
    
    formatNumber(number) {
        return new Intl.NumberFormat('en-US').format(number);
    }
    
    formatDate(date) {
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    }
    
    getRiskColor(riskScore) {
        if (riskScore >= 0.7) return 'var(--risk-high)';
        if (riskScore >= 0.4) return 'var(--risk-medium)';
        return 'var(--risk-low)';
    }
    
    getRiskLevel(riskScore) {
        if (riskScore >= 0.7) return 'High';
        if (riskScore >= 0.4) return 'Medium';
        return 'Low';
    }
    
    createChart(canvasId, config) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.warn(`Canvas with id '${canvasId}' not found`);
            return null;
        }
        
        // Destroy existing chart if it exists
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        // Create new chart
        this.charts[canvasId] = new Chart(canvas, config);
        return this.charts[canvasId];
    }
    
    updateChartData(chartId, newData) {
        if (this.charts[chartId]) {
            this.charts[chartId].data = newData;
            this.charts[chartId].update();
        }
    }
    
    // Utility function to get URL parameters
    getUrlParameter(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    }
    
    // Utility function to update URL parameters without page reload
    updateUrlParameter(key, value) {
        const url = new URL(window.location);
        if (value) {
            url.searchParams.set(key, value);
        } else {
            url.searchParams.delete(key);
        }
        window.history.replaceState({}, '', url);
    }
    
    // Debounce function for search inputs
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Export data as CSV
    exportToCSV(data, filename) {
        if (!data || data.length === 0) {
            this.showNotification('No data to export', 'warning');
            return;
        }
        
        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => 
                headers.map(header => {
                    const value = row[header];
                    return typeof value === 'string' && value.includes(',') 
                        ? `"${value}"` 
                        : value;
                }).join(',')
            )
        ].join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        window.URL.revokeObjectURL(url);
        
        this.showNotification('Data exported successfully', 'success');
    }
    
    // Show/hide elements with animation
    showElement(element, animation = 'fade-in') {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.style.display = 'block';
            element.classList.add(animation);
        }
    }
    
    hideElement(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.style.display = 'none';
            element.classList.remove('fade-in', 'slide-up');
        }
    }
}

// Initialize the platform
const amlPlatform = new AMLPlatform();

// Export for use in other modules
window.AMLPlatform = AMLPlatform;
window.amlPlatform = amlPlatform;