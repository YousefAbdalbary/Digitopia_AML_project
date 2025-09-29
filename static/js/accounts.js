// Account Analysis JavaScript
class AccountAnalysis {
    constructor() {
        this.currentResults = [];
        this.selectedAccounts = [];
        this.searchFilters = {
            query: '',
            type: 'all',
            risk_level: 'all',
            country: 'all',
            limit: '10'
        };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadInitialData();
    }
    
    attachAccountCardListeners() {
        // Handle View Account buttons
        document.querySelectorAll('.view-account-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                // Get account ID from the button itself or closest button element
                const button = e.target.closest('.view-account-btn');
                const accountId = button ? button.getAttribute('data-id') : null;
                
                if (accountId) {
                    console.log('View account clicked:', accountId);
                    await this.viewAccount(accountId);
                } else {
                    console.error('Account ID not found for view button');
                }
            });
        });
        
        // Handle Analyze Account buttons
        document.querySelectorAll('.analyze-account-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                // Get account ID from the button itself or closest button element
                const button = e.target.closest('.analyze-account-btn');
                const accountId = button ? button.getAttribute('data-id') : null;
                
                if (accountId) {
                    console.log('Analyze account clicked:', accountId);
                    await this.analyzeAccount(accountId);
                } else {
                    console.error('Account ID not found for analyze button');
                }
            });
        });
    }
    
    setupEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('account-search');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.searchFilters.query = e.target.value;
                    this.performSearch();
                }, 300);
            });
        }
        
        // Search button
        const searchBtn = document.getElementById('search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.performSearch());
        }
        
        // Filter dropdowns
        const typeFilter = document.getElementById('account-type-filter');
        const riskFilter = document.getElementById('risk-level-filter');
        const countryFilter = document.getElementById('country-filter');
        
        if (typeFilter) {
            typeFilter.addEventListener('change', (e) => {
                this.searchFilters.type = e.target.value;
                this.performSearch();
            });
        }
        
        if (riskFilter) {
            riskFilter.addEventListener('change', (e) => {
                this.searchFilters.risk_level = e.target.value;
                this.performSearch();
            });
        }
        
        if (countryFilter) {
            countryFilter.addEventListener('change', (e) => {
                this.searchFilters.country = e.target.value;
                this.performSearch();
            });
        }
        
        // Limit filter
        const limitFilter = document.getElementById('limit-filter');
        if (limitFilter) {
            limitFilter.addEventListener('change', (e) => {
                this.searchFilters.limit = e.target.value;
                this.loadInitialData(); // Reload with new limit
            });
        }
        
        // Enter key in search
        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.target.id === 'account-search') {
                e.preventDefault();
                this.performSearch();
            }
        });
    }
    
    async loadInitialData() {
        try {
            // Load some sample accounts or recent high-risk accounts
            const limit = this.searchFilters.limit || '10';
            const response = await fetch(`/api/accounts/recent-high-risk?limit=${limit}`);
            
            if (response.ok) {
                const accounts = await response.json();
                if (accounts.length > 0) {
                    this.displaySearchResults(accounts);
                    this.attachAccountCardListeners();
                }
            } else {
                // If the high-risk endpoint doesn't exist, try loading all accounts
                const allAccountsResponse = await fetch('/api/accounts/search');
                if (allAccountsResponse.ok) {
                    const allAccounts = await allAccountsResponse.json();
                    this.displaySearchResults(allAccounts.slice(0, 10)); // Show first 10
                    this.attachAccountCardListeners();
                }
            }
            
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }
    
    async performSearch() {
        try {
            const params = new URLSearchParams(this.searchFilters);
            const response = await fetch(`/api/accounts/search?${params}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const results = await response.json();
            this.currentResults = results;
            this.displaySearchResults(results);
            
        } catch (error) {
            console.error('Error performing search:', error);
            this.showSearchError('Failed to search accounts. Please try again.');
        }
    }
    
    displaySearchResults(accounts) {
        const resultsContainer = document.querySelector('#accounts-grid');
        const countElement = document.querySelector('#results-count');
        
        if (!resultsContainer) return;
        
        // Update count
        if (countElement) {
            countElement.textContent = `${accounts.length} accounts found`;
        }
        
        if (accounts.length === 0) {
            resultsContainer.innerHTML = `
                <div class="empty-results text-center py-5">
                    <i class="fas fa-search fa-3x text-muted mb-3"></i>
                    <h5>No Accounts Found</h5>
                    <p class="text-muted">Try different search terms or adjust your filters.</p>
                </div>
            `;
            return;
        }
        
        resultsContainer.innerHTML = accounts.map(account => this.createAccountCard(account)).join('');
        
        // Add event listeners to newly created buttons
        this.attachAccountCardListeners();
    }
    
    createAccountCard(account) {
        const riskClass = this.getRiskClass(account.risk_score);
        const riskLabel = this.getRiskLabel(account.risk_score);
        
        return `
            <div class="account-card border rounded p-3 mb-3" data-account-id="${account.account_id}">
                <div class="row align-items-center">
                    <div class="col-md-1">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" value="${account.account_id}" 
                                   onchange="accountAnalysis.toggleAccountSelection('${account.account_id}')">
                        </div>
                    </div>
                    
                    <div class="col-md-3">
                        <div class="account-info">
                            <h6 class="mb-1">${account.account_id}</h6>
                            <small class="text-muted">
                                ${account.account_type || 'Unknown Type'} • ${account.country || 'Unknown'}
                            </small>
                        </div>
                    </div>
                    
                    <div class="col-md-2">
                        <div class="risk-indicator">
                            <span class="badge ${riskClass} fs-6">${(account.risk_score * 100).toFixed(1)}%</span>
                            <div class="small text-muted">${riskLabel}</div>
                        </div>
                    </div>
                    
                    <div class="col-md-2">
                        <div class="transaction-stats">
                            <div class="fw-bold">${account.transaction_count || 0}</div>
                            <div class="small text-muted">Transactions</div>
                        </div>
                    </div>
                    
                    <div class="col-md-2">
                        <div class="volume-stats">
                            <div class="fw-bold">${this.formatCurrency(account.total_amount || account.total_sent || 0)}</div>
                            <div class="small text-muted">Total Volume</div>
                        </div>
                    </div>
                    
                    <div class="col-md-2">
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary view-account-btn" data-id="${account.account_id}">
                                <i class="fas fa-eye"></i> View
                            </button>
                            <button class="btn btn-outline-info analyze-account-btn" data-id="${account.account_id}">
                                <i class="fas fa-chart-line"></i> Analyze
                            </button>
                            ${account.risk_score >= 0.7 ? `
                                <button class="btn btn-outline-warning flag-account-btn" data-id="${account.account_id}">
                                    <i class="fas fa-flag"></i>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
                
                ${account.recent_activity ? `
                    <div class="row mt-3">
                        <div class="col-12">
                            <div class="recent-activity">
                                <h6 class="mb-2">Recent Activity</h6>
                                <div class="activity-timeline">
                                    ${account.recent_activity.slice(0, 3).map(activity => `
                                        <div class="activity-item d-flex justify-content-between align-items-center py-1">
                                            <span class="small">
                                                ${activity.type}: ${this.formatCurrency(activity.amount, activity.currency)}
                                            </span>
                                            <span class="small text-muted">${this.formatDateTime(activity.timestamp)}</span>
                                        </div>
                                    `).join('')}
                                    ${account.recent_activity.length > 3 ? `
                                        <div class="text-center">
                                            <small><a href="#" onclick="accountAnalysis.viewAccountDetails('${account.account_id}')">View all ${account.recent_activity.length} activities</a></small>
                                        </div>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    async viewAccountDetails(accountId) {
        try {
            const response = await fetch(`/api/accounts/${accountId}/details`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const accountDetails = await response.json();
            this.showAccountDetailsModal(accountDetails);
            
        } catch (error) {
            console.error('Error loading account details:', error);
            this.showNotification('Error loading account details', 'error');
        }
    }
    
    showAccountDetailsModal(account) {
        const modal = document.getElementById('account-details-modal');
        if (!modal) return;
        
        modal.querySelector('.modal-title').textContent = `Account: ${account.account_id}`;
        
        const modalBody = modal.querySelector('.modal-body');
        modalBody.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Account Information</h6>
                    <p><strong>Account ID:</strong> ${account.account_id}</p>
                    <p><strong>Type:</strong> ${account.account_type || 'N/A'}</p>
                    <p><strong>Country:</strong> ${account.country || 'N/A'}</p>
                    <p><strong>Created:</strong> ${this.formatDateTime(account.created_at)}</p>
                    <p><strong>Last Activity:</strong> ${this.formatDateTime(account.last_activity)}</p>
                </div>
                <div class="col-md-6">
                    <h6>Risk Assessment</h6>
                    <p><strong>Risk Score:</strong> 
                        <span class="badge ${this.getRiskClass(account.risk_score)} fs-6">
                            ${(account.risk_score * 100).toFixed(1)}%
                        </span>
                    </p>
                    <p><strong>Risk Factors:</strong></p>
                    <ul class="list-unstyled">
                        ${(account.risk_factors || []).map(factor => `
                            <li><i class="fas fa-exclamation-triangle text-warning"></i> ${factor}</li>
                        `).join('')}
                    </ul>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-4">
                    <div class="stat-box text-center p-3 border rounded">
                        <h5>${account.transaction_count || 0}</h5>
                        <small class="text-muted">Total Transactions</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-box text-center p-3 border rounded">
                        <h5>${this.formatCurrency(account.total_volume || 0)}</h5>
                        <small class="text-muted">Total Volume</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-box text-center p-3 border rounded">
                        <h5>${this.formatCurrency(account.avg_transaction || 0)}</h5>
                        <small class="text-muted">Avg Transaction</small>
                    </div>
                </div>
            </div>
            
            ${account.transaction_history && account.transaction_history.length > 0 ? `
                <div class="mt-4">
                    <h6>Recent Transactions</h6>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Type</th>
                                    <th>Amount</th>
                                    <th>Risk</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${account.transaction_history.slice(0, 10).map(tx => `
                                    <tr>
                                        <td>${this.formatDate(tx.timestamp)}</td>
                                        <td>${tx.type}</td>
                                        <td>${this.formatCurrency(tx.amount, tx.currency)}</td>
                                        <td>
                                            <span class="badge ${this.getRiskClass(tx.risk_score)} badge-sm">
                                                ${(tx.risk_score * 100).toFixed(1)}%
                                            </span>
                                        </td>
                                        <td>
                                            <span class="badge ${this.getStatusClass(tx.status)} badge-sm">
                                                ${tx.status}
                                            </span>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            ` : ''}
        `;
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
    
    async analyzeAccount(accountId) {
        try {
            const response = await fetch(`/api/accounts/${accountId}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const analysisResult = await response.json();
            this.showAnalysisResults(accountId, analysisResult);
            
        } catch (error) {
            console.error('Error analyzing account:', error);
            this.showNotification('Error analyzing account', 'error');
        }
    }
    
    showAnalysisResults(accountId, analysis) {
        const modal = document.getElementById('analysis-modal');
        if (!modal) return;
        
        modal.querySelector('.modal-title').textContent = `Analysis: ${accountId}`;
        
        const modalBody = modal.querySelector('.modal-body');
        modalBody.innerHTML = `
            <div class="analysis-results">
                <div class="row">
                    <div class="col-md-6">
                        <h6>Risk Assessment</h6>
                        <div class="risk-score-display text-center p-3 border rounded mb-3">
                            <div class="display-6 ${this.getRiskClass(analysis.overall_risk_score)}">${(analysis.overall_risk_score * 100).toFixed(1)}%</div>
                            <div class="text-muted">Overall Risk Score</div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h6>Key Findings</h6>
                        <ul class="list-group list-group-flush">
                            ${(analysis.findings || []).map(finding => `
                                <li class="list-group-item px-0">
                                    <i class="fas fa-${finding.severity === 'high' ? 'exclamation-triangle text-danger' : 
                                                      finding.severity === 'medium' ? 'exclamation-circle text-warning' : 
                                                      'info-circle text-info'}"></i>
                                    ${finding.description}
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-12">
                        <h6>Transaction Patterns</h6>
                        <div class="patterns-grid">
                            ${(analysis.patterns || []).map(pattern => `
                                <div class="pattern-card border rounded p-3 mb-2">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <div>
                                            <strong>${pattern.type}</strong>
                                            <p class="mb-0 text-muted small">${pattern.description}</p>
                                        </div>
                                        <div class="confidence-score">
                                            <span class="badge ${pattern.confidence > 0.8 ? 'bg-danger' : 
                                                                pattern.confidence > 0.6 ? 'bg-warning text-dark' : 'bg-info'}">
                                                ${(pattern.confidence * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
                
                ${analysis.recommendations && analysis.recommendations.length > 0 ? `
                    <div class="row mt-4">
                        <div class="col-12">
                            <h6>Recommendations</h6>
                            <div class="alert alert-info">
                                <ul class="mb-0">
                                    ${analysis.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
    
    async flagAccount(accountId) {
        if (!confirm(`Are you sure you want to flag account ${accountId} for investigation?`)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/accounts/${accountId}/flag`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (response.ok) {
                this.showNotification('Account flagged successfully', 'success');
                this.performSearch(); // Refresh results
            }
            
        } catch (error) {
            console.error('Error flagging account:', error);
            this.showNotification('Error flagging account', 'error');
        }
    }
    
    toggleAccountSelection(accountId) {
        const index = this.selectedAccounts.indexOf(accountId);
        if (index === -1) {
            this.selectedAccounts.push(accountId);
        } else {
            this.selectedAccounts.splice(index, 1);
        }
        
        this.updateComparisonButton();
    }
    
    updateComparisonButton() {
        const compareBtn = document.querySelector('[data-action="compare"]');
        if (compareBtn) {
            compareBtn.disabled = this.selectedAccounts.length < 2;
            compareBtn.textContent = `Compare (${this.selectedAccounts.length})`;
        }
    }
    
    async compareAccounts() {
        if (this.selectedAccounts.length < 2) {
            this.showNotification('Please select at least 2 accounts to compare', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/accounts/compare', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ accounts: this.selectedAccounts })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const comparison = await response.json();
            this.showComparisonModal(comparison);
            
        } catch (error) {
            console.error('Error comparing accounts:', error);
            this.showNotification('Error comparing accounts', 'error');
        }
    }
    
    showComparisonModal(comparison) {
        const modal = document.getElementById('comparison-modal');
        if (!modal) return;
        
        modal.querySelector('.modal-title').textContent = `Account Comparison (${comparison.accounts.length} accounts)`;
        
        const modalBody = modal.querySelector('.modal-body');
        modalBody.innerHTML = `
            <div class="comparison-table">
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>Metric</th>
                            ${comparison.accounts.map(acc => `<th>${acc.account_id}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Risk Score</strong></td>
                            ${comparison.accounts.map(acc => `
                                <td>
                                    <span class="badge ${this.getRiskClass(acc.risk_score)} fs-6">
                                        ${(acc.risk_score * 100).toFixed(1)}%
                                    </span>
                                </td>
                            `).join('')}
                        </tr>
                        <tr>
                            <td><strong>Transaction Count</strong></td>
                            ${comparison.accounts.map(acc => `<td>${acc.transaction_count || 0}</td>`).join('')}
                        </tr>
                        <tr>
                            <td><strong>Total Volume</strong></td>
                            ${comparison.accounts.map(acc => `<td>${this.formatCurrency(acc.total_volume || 0)}</td>`).join('')}
                        </tr>
                        <tr>
                            <td><strong>Avg Transaction</strong></td>
                            ${comparison.accounts.map(acc => `<td>${this.formatCurrency(acc.avg_transaction || 0)}</td>`).join('')}
                        </tr>
                        <tr>
                            <td><strong>Country</strong></td>
                            ${comparison.accounts.map(acc => `<td>${acc.country || 'N/A'}</td>`).join('')}
                        </tr>
                    </tbody>
                </table>
            </div>
            
            ${comparison.insights && comparison.insights.length > 0 ? `
                <div class="mt-4">
                    <h6>Comparison Insights</h6>
                    <div class="alert alert-info">
                        <ul class="mb-0">
                            ${comparison.insights.map(insight => `<li>${insight}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            ` : ''}
        `;
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
    
    // Helper functions
    getRiskClass(riskScore) {
        if (riskScore >= 0.7) return 'bg-danger';
        if (riskScore >= 0.3) return 'bg-warning text-dark';
        return 'bg-success';
    }
    
    getRiskLabel(riskScore) {
        if (riskScore >= 0.7) return 'High Risk';
        if (riskScore >= 0.3) return 'Medium Risk';
        return 'Low Risk';
    }
    
    getStatusClass(status) {
        switch(status) {
            case 'active': return 'bg-success';
            case 'flagged': return 'bg-warning text-dark';
            case 'suspended': return 'bg-danger';
            case 'closed': return 'bg-secondary';
            default: return 'bg-primary';
        }
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
    
    showSearchError(message) {
        const resultsContainer = document.querySelector('#search-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="error-state text-center py-5">
                    <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                    <h5>Search Error</h5>
                    <p class="text-muted">${message}</p>
                    <button class="btn btn-primary" onclick="accountAnalysis.performSearch()">
                        <i class="fas fa-sync"></i> Retry
                    </button>
                </div>
            `;
        }
    }
    
    async viewAccount(accountId) {
        try {
            const response = await fetch(`/api/accounts/${accountId}/details`);
            if (!response.ok) throw new Error('Failed to fetch account details');
            
            const account = await response.json();
            
            // Show account details in a modal or redirect to detail page
            this.showAccountDetailsModal(account);
            
        } catch (error) {
            console.error('Error viewing account:', error);
            this.showNotification('Failed to load account details', 'error');
        }
    }
    
    async analyzeAccount(accountId) {
        try {
            const response = await fetch(`/api/accounts/${accountId}/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) throw new Error('Failed to analyze account');
            
            const analysis = await response.json();
            
            // Show analysis results in a modal
            this.showAnalysisModal(analysis);
            
        } catch (error) {
            console.error('Error analyzing account:', error);
            this.showNotification('Failed to analyze account', 'error');
        }
    }
    
    showAccountDetailsModal(account) {
        const modalHTML = `
            <div class="modal fade" id="accountDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Account Details: ${account.account_id}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <p><strong>Account ID:</strong> ${account.account_id}</p>
                                    <p><strong>Account Type:</strong> ${account.account_type || 'N/A'}</p>
                                    <p><strong>Country:</strong> ${account.country || 'N/A'}</p>
                                    <p><strong>Risk Score:</strong> <span class="badge bg-${account.risk_score > 0.7 ? 'danger' : account.risk_score > 0.4 ? 'warning' : 'success'}">${(account.risk_score * 100).toFixed(1)}%</span></p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>Total Transactions:</strong> ${account.transaction_count || 0}</p>
                                    <p><strong>Total Amount:</strong> $${account.total_amount ? account.total_amount.toLocaleString() : '0'}</p>
                                    <p><strong>Average Transaction:</strong> $${account.avg_amount ? account.avg_amount.toLocaleString() : '0'}</p>
                                    <p><strong>Status:</strong> <span class="badge bg-primary">${account.status || 'Active'}</span></p>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="window.accountAnalysis.analyzeAccount('${account.account_id}')">Analyze Account</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('accountDetailsModal');
        if (existingModal) existingModal.remove();
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Show modal
        const modal = document.getElementById('accountDetailsModal');
        if (typeof bootstrap !== 'undefined') {
            new bootstrap.Modal(modal).show();
        } else {
            // Fallback: show modal manually
            modal.style.display = 'block';
            modal.classList.add('show');
            document.body.classList.add('modal-open');
            
            // Add backdrop
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            document.body.appendChild(backdrop);
        }
    }
    
    showAnalysisModal(analysis) {
        const modalHTML = `
            <div class="modal fade" id="analysisModal" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Account Analysis: ${analysis.account_id}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-4">
                                    <div class="card mb-3">
                                        <div class="card-header"><h6>Risk Assessment</h6></div>
                                        <div class="card-body">
                                            <p><strong>Risk Score:</strong> <span class="badge bg-${analysis.risk_score > 0.7 ? 'danger' : analysis.risk_score > 0.4 ? 'warning' : 'success'}">${(analysis.risk_score * 100).toFixed(1)}%</span></p>
                                            <p><strong>Risk Level:</strong> <span class="badge bg-${analysis.risk_score > 0.7 ? 'danger' : analysis.risk_score > 0.4 ? 'warning' : 'success'}">${analysis.risk_score > 0.7 ? 'High' : analysis.risk_score > 0.4 ? 'Medium' : 'Low'}</span></p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-8">
                                    <div class="card mb-3">
                                        <div class="card-header"><h6>Pattern Analysis</h6></div>
                                        <div class="card-body">
                                            <div class="row">
                                                ${analysis.patterns.map(pattern => `
                                                    <div class="col-md-6 mb-2">
                                                        <div class="alert alert-${pattern.severity === 'high' ? 'danger' : pattern.severity === 'medium' ? 'warning' : 'info'} py-2">
                                                            <strong>${pattern.type}:</strong> ${pattern.description}
                                                        </div>
                                                    </div>
                                                `).join('')}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-12">
                                    <div class="card">
                                        <div class="card-header"><h6>Analysis Summary</h6></div>
                                        <div class="card-body">
                                            <div class="row">
                                                <div class="col-md-4"><p><strong>Analysis Date:</strong> ${new Date(analysis.analysis_date).toLocaleString()}</p></div>
                                                <div class="col-md-4"><p><strong>Risk Level:</strong> <span class="badge bg-${analysis.risk_score > 0.7 ? 'danger' : analysis.risk_score > 0.4 ? 'warning' : 'success'}">${analysis.risk_score > 0.7 ? 'High' : analysis.risk_score > 0.4 ? 'Medium' : 'Low'}</span></p></div>
                                                <div class="col-md-4"><p><strong>Patterns Found:</strong> ${analysis.patterns ? analysis.patterns.length : 0}</p></div>
                                            </div>
                                            ${analysis.recommendations && analysis.recommendations.length > 0 ? `
                                                <div class="row mt-3">
                                                    <div class="col-12">
                                                        <h6>Recommendations:</h6>
                                                        <ul>
                                                            ${analysis.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                                                        </ul>
                                                    </div>
                                                </div>
                                            ` : ''}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="accountAnalysis.generateReport('${accountId}')">Generate Report</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('analysisModal');
        if (existingModal) existingModal.remove();
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Show modal
        const modal = document.getElementById('analysisModal');
        if (typeof bootstrap !== 'undefined') {
            new bootstrap.Modal(modal).show();
        } else {
            // Fallback: show modal manually
            modal.style.display = 'block';
            modal.classList.add('show');
            document.body.classList.add('modal-open');
            
            // Add backdrop
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            document.body.appendChild(backdrop);
        }
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
    
    async generateReport(accountId) {
        try {
            this.showNotification('Generating report...', 'info');
            
            const response = await fetch(`/api/accounts/${accountId}/report`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const report = await response.json();
            
            if (report.error) {
                throw new Error(report.error);
            }
            
            // Create and download the report
            this.downloadReport(report);
            this.showNotification('Report generated successfully!', 'success');
            
        } catch (error) {
            console.error('Error generating report:', error);
            this.showNotification(`Failed to generate report: ${error.message}`, 'error');
        }
    }
    
    downloadReport(report) {
        // Create a formatted report content
        const reportContent = this.formatReportForDownload(report);
        
        // Create and trigger download
        const blob = new Blob([reportContent], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `account_report_${report.account_id}_${new Date().toISOString().slice(0, 10)}.txt`;
        
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
    
    formatReportForDownload(report) {
        const formatCurrency = (amount) => {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(amount);
        };
        
        let content = `AML ACCOUNT ANALYSIS REPORT\n`;
        content += `===============================\n\n`;
        content += `Account ID: ${report.account_id}\n`;
        content += `Generated: ${new Date(report.generated_at).toLocaleString()}\n\n`;
        
        // Account Details
        if (report.account_details) {
            content += `ACCOUNT DETAILS\n`;
            content += `---------------\n`;
            content += `Type: ${report.account_details.account_type || 'Unknown'}\n`;
            content += `Country: ${report.account_details.country || 'Unknown'}\n`;
            content += `Risk Score: ${(report.account_details.risk_score * 100).toFixed(1)}%\n`;
            content += `Status: ${report.account_details.status || 'Active'}\n\n`;
        }
        
        // Transaction Summary
        if (report.transaction_summary) {
            const ts = report.transaction_summary;
            content += `TRANSACTION SUMMARY\n`;
            content += `-------------------\n`;
            content += `Total Transactions: ${ts.total_transactions}\n`;
            content += `Total Incoming: ${formatCurrency(ts.total_incoming)}\n`;
            content += `Total Outgoing: ${formatCurrency(ts.total_outgoing)}\n`;
            content += `Net Flow: ${formatCurrency(ts.net_flow)}\n`;
            content += `Unique Counterparties: ${ts.unique_counterparties}\n`;
            if (ts.date_range && ts.date_range.from) {
                content += `Period: ${new Date(ts.date_range.from).toLocaleDateString()} - ${new Date(ts.date_range.to).toLocaleDateString()}\n`;
            }
            content += `\n`;
        }
        
        // Risk Analysis
        if (report.risk_analysis) {
            const ra = report.risk_analysis;
            content += `RISK ANALYSIS\n`;
            content += `-------------\n`;
            content += `Risk Score: ${(ra.risk_score * 100).toFixed(1)}%\n`;
            content += `Risk Level: ${ra.risk_score > 0.7 ? 'High' : ra.risk_score > 0.4 ? 'Medium' : 'Low'}\n`;
            
            if (ra.patterns && ra.patterns.length > 0) {
                content += `Patterns Detected:\n`;
                ra.patterns.forEach(pattern => {
                    content += `  - ${pattern.type}: ${pattern.description}\n`;
                });
            }
            content += `\n`;
        }
        
        // Risk Indicators
        if (report.risk_indicators) {
            const ri = report.risk_indicators;
            content += `RISK INDICATORS\n`;
            content += `---------------\n`;
            content += `High Risk Transactions: ${ri.high_risk_transactions}\n`;
            content += `Large Transactions (>$100K): ${ri.large_transactions}\n`;
            if (ri.suspicious_patterns && ri.suspicious_patterns.length > 0) {
                content += `Suspicious Patterns: ${ri.suspicious_patterns.length}\n`;
            }
            content += `\n`;
        }
        
        // Recommendations
        if (report.recommendations && report.recommendations.length > 0) {
            content += `RECOMMENDATIONS\n`;
            content += `---------------\n`;
            report.recommendations.forEach((rec, index) => {
                content += `${index + 1}. ${rec}\n`;
            });
            content += `\n`;
        }
        
        content += `\nReport generated by AML Detection Platform\n`;
        content += `© ${new Date().getFullYear()} - Confidential\n`;
        
        return content;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.accountAnalysis = new AccountAnalysis();
});