// Cash Flow Analysis JavaScript
class CashFlowAnalysis {
    constructor() {
        this.currentPage = 1;
        this.itemsPerPage = 50;
        this.currentFilters = {};
        this.charts = {};
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.loadTransactions();
        this.loadCurrencyOverview();
    }
    
    setupEventListeners() {
        // Filter controls
        const applyFiltersBtn = document.querySelector('[data-action="apply-filters"]');
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', () => this.applyFilters());
        }
        
        // Export button
        const exportBtn = document.querySelector('[data-action="export"]');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportData());
        }
        
        // Pagination
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-page]')) {
                e.preventDefault();
                this.currentPage = parseInt(e.target.dataset.page);
                this.loadTransactions();
            }
        });
        
        // Search
        const searchInput = document.querySelector('[data-search="transactions"]');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.currentFilters.search = e.target.value;
                    this.currentPage = 1;
                    this.loadTransactions();
                }, 300);
            });
        }
        
        // Items per page
        const itemsSelect = document.querySelector('[data-items-per-page]');
        if (itemsSelect) {
            itemsSelect.addEventListener('change', (e) => {
                this.itemsPerPage = parseInt(e.target.value);
                this.currentPage = 1;
                this.loadTransactions();
            });
        }
        
        // Chart type selector
        const chartTypeSelect = document.querySelector('[data-chart="trends"]');
        if (chartTypeSelect) {
            chartTypeSelect.addEventListener('change', () => this.updateTrendsChart());
        }
        
        // Toggle currencies in network view
        const toggleCurrenciesBtn = document.getElementById('toggle-currency-edges');
        if (toggleCurrenciesBtn) {
            toggleCurrenciesBtn.addEventListener('click', () => this.toggleCurrencyView());
        }
    }
    
    initializeCharts() {
        this.initializeCurrencyChart();
        this.initializeTrendsChart();
        this.initializeRiskChart();
        this.initializeNetworkView();
    }
    
    initializeCurrencyChart() {
        const ctx = document.getElementById('currency-pie-chart');
        if (!ctx) {
            console.log('Currency chart canvas not found');
            return;
        }
        
        this.charts.currency = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#007bff', '#28a745', '#ffc107', '#dc3545', '#17a2b8',
                        '#6f42c1', '#e83e8c', '#fd7e14', '#20c997', '#6c757d'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: $${value.toLocaleString()} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    initializeTrendsChart() {
        const ctx = document.getElementById('flow-trends-chart');
        if (!ctx) {
            console.log('Trends chart canvas not found');
            return;
        }
        
        this.charts.trends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Volume',
                    data: [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }
    
    initializeRiskChart() {
        const ctx = document.getElementById('risk-analysis-chart');
        if (!ctx) {
            console.log('Risk analysis chart canvas not found');
            return;
        }
        
        this.charts.risk = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Low Risk', 'Medium Risk', 'High Risk'],
                datasets: [{
                    label: 'Transactions',
                    data: [],
                    backgroundColor: ['#28a745', '#ffc107', '#dc3545']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    initializeNetworkView() {
        const container = document.getElementById('multi-currency-network');
        if (!container) {
            console.log('Multi-currency network container not found');
            return;
        }
        
        try {
            // Clear any existing content
            container.innerHTML = '';
            
            // Set dimensions
            const height = 400;
            container.style.height = height + 'px';
            
            // Initialize Leaflet map
            this.networkMap = L.map('multi-currency-network', { 
                attributionControl: false,
                zoomControl: true,
                scrollWheelZoom: true
            });
            
            // Add dark tile layer
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                subdomains: 'abcd',
                maxZoom: 19,
                attribution: ''
            }).addTo(this.networkMap);
            
            this.bankMarkers = [];
            this.flowLines = [];
            
            console.log('World map initialized for Multi-Currency Network');
        } catch (error) {
            console.error('Error initializing network map:', error);
            container.innerHTML = '<div class="alert alert-warning">Failed to load map visualization. Please try refreshing the page.</div>';
        }
    }
    
    getFilters() {
        return {
            account_filter: document.getElementById('account-filter')?.value || '',
            currency: document.getElementById('currency-filter')?.value || 'all',
            date_range: document.getElementById('date-range')?.value || '30d',
            search: this.currentFilters.search || '',
            page: this.currentPage,
            per_page: this.itemsPerPage
        };
    }
    
    async loadTransactions() {
        try {
            const filters = this.getFilters();
            const response = await fetch(`/api/cash-flow/transactions?${new URLSearchParams(filters)}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.updateTransactionTable(data);
            this.updatePagination(data);
            
        } catch (error) {
            console.error('Error loading transactions:', error);
            this.showTransactionError('Failed to load transactions. Please try again.');
        }
    }
    
    async loadCurrencyOverview() {
        try {
            const filters = { 
                currency: this.getFilters().currency || 'all',
                date_range: this.getFilters().date_range || '30d'
            };
            
            console.log('Loading currency overview with filters:', filters);
            
            const response = await fetch(`/api/cash-flow/overview?${new URLSearchParams(filters)}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Full API response:', data);
            
            this.updateCurrencyChart(data.currency_breakdown || []);
            this.updateTrendsChart(data.trends || []);
            this.updateRiskAnalysis(data.risk_analysis || {});
            this.updateTopFlows(data.top_flows || []);
            
            // Call the async updateNetworkView function with await
            await this.updateNetworkView(data.top_flows || []);
            
        } catch (error) {
            console.error('Error loading currency overview:', error);
        }
    }
    
    updateTransactionTable(data) {
        const tbody = document.querySelector('#transactions-table tbody');
        if (!tbody) return;
        
        const transactions = data.transactions || [];
        
        if (transactions.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-4">
                        <i class="fas fa-search fa-2x text-muted mb-2"></i>
                        <p class="text-muted mb-0">No transactions found</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = transactions.map(tx => `
            <tr class="${this.getTransactionRowClass(tx.risk_score)}">
                <td>${this.formatDateTime(tx.timestamp)}</td>
                <td>
                    <span class="font-monospace">${tx.from_account}</span>
                </td>
                <td>
                    <span class="font-monospace">${tx.to_account}</span>
                </td>
                <td class="text-end">
                    <strong>${this.formatCurrency(tx.amount_received, tx.receiving_currency)}</strong>
                </td>
                <td>
                    <span class="badge bg-secondary">${tx.receiving_currency}</span>
                </td>
                <td>
                    <span class="badge ${this.getRiskBadgeClass(tx.risk_score)}">
                        ${(tx.risk_score * 100).toFixed(1)}%
                    </span>
                </td>
                <td>
                    <span class="badge ${this.getStatusBadgeClass(tx.status)}">
                        ${tx.status || 'Processed'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="window.cashFlowAnalysis.showTransactionDetails('${tx._id || tx.id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                    ${tx.risk_score >= 0.7 ? `
                        <button class="btn btn-sm btn-outline-warning" onclick="window.cashFlowAnalysis.flagTransaction('${tx._id || tx.id}')">
                            <i class="fas fa-flag"></i>
                        </button>
                    ` : ''}
                </td>
            </tr>
        `).join('');
    }
    
    updatePagination(data) {
        const pagination = document.querySelector('.pagination-info');
        if (pagination) {
            const start = ((this.currentPage - 1) * this.itemsPerPage) + 1;
            const end = Math.min(start + this.itemsPerPage - 1, data.total || 0);
            pagination.textContent = `Showing ${start}-${end} of ${data.total || 0} transactions`;
        }
        
        // Update pagination buttons
        const paginationContainer = document.querySelector('.pagination-controls');
        if (paginationContainer && data.total > this.itemsPerPage) {
            const totalPages = Math.ceil(data.total / this.itemsPerPage);
            const buttons = [];
            
            // Previous button
            buttons.push(`
                <button class="btn btn-outline-primary ${this.currentPage === 1 ? 'disabled' : ''}" 
                        data-page="${this.currentPage - 1}" ${this.currentPage === 1 ? 'disabled' : ''}>
                    <i class="fas fa-chevron-left"></i> Previous
                </button>
            `);
            
            // Page numbers (simplified)
            for (let i = Math.max(1, this.currentPage - 2); i <= Math.min(totalPages, this.currentPage + 2); i++) {
                buttons.push(`
                    <button class="btn ${i === this.currentPage ? 'btn-primary' : 'btn-outline-primary'}" 
                            data-page="${i}">${i}</button>
                `);
            }
            
            // Next button
            buttons.push(`
                <button class="btn btn-outline-primary ${this.currentPage === totalPages ? 'disabled' : ''}" 
                        data-page="${this.currentPage + 1}" ${this.currentPage === totalPages ? 'disabled' : ''}>
                    Next <i class="fas fa-chevron-right"></i>
                </button>
            `);
            
            paginationContainer.innerHTML = buttons.join('');
        }
    }
    
    updateCurrencyChart(currencyData) {
        if (!this.charts.currency) return;
        
        console.log('Currency data received:', currencyData);
        
        const labels = currencyData.map(item => item.currency || 'Unknown');
        const data = currencyData.map(item => item.amount || 0);
        
        this.charts.currency.data.labels = labels;
        this.charts.currency.data.datasets[0].data = data;
        this.charts.currency.update();
    }
    
    updateTrendsChart(trendsData) {
        if (!this.charts.trends) return;
        
        console.log('Trends data received:', trendsData);
        
        const chartType = document.querySelector('[data-chart="trends"]')?.value || 'volume';
        
        let labels, data, label;
        switch(chartType) {
            case 'transaction_count':
                labels = trendsData.map(item => item.date);
                data = trendsData.map(item => item.count || 0);
                label = 'Transaction Count';
                break;
            case 'average_risk':
                labels = trendsData.map(item => item.date);
                data = trendsData.map(item => (item.average_risk || 0) * 100);
                label = 'Average Risk (%)';
                break;
            default:
                labels = trendsData.map(item => item.date);
                data = trendsData.map(item => item.amount || 0);
                label = 'Volume';
        }
        
        this.charts.trends.data.labels = labels;
        this.charts.trends.data.datasets[0].data = data;
        this.charts.trends.data.datasets[0].label = label;
        this.charts.trends.update();
    }
    
    updateRiskAnalysis(riskData) {
        if (!this.charts.risk) return;
        
        console.log('Risk data received:', riskData);
        
        const data = [
            (riskData.low && riskData.low.count) || 0,
            (riskData.medium && riskData.medium.count) || 0,
            (riskData.high && riskData.high.count) || 0
        ];
        
        this.charts.risk.data.datasets[0].data = data;
        this.charts.risk.update();
    }
    
    updateTopFlows(topFlows) {
        const container = document.querySelector('#top-flows-list');
        if (!container) return;
        
        console.log('Top flows data received:', topFlows);
        
        if (!topFlows || topFlows.length === 0) {
            container.innerHTML = '<p class="text-muted">No cash flows found</p>';
            return;
        }
        
        container.innerHTML = topFlows.map((flow, index) => {
            // Handle self-transactions (same bank) with special formatting
            const isSelfTransaction = flow.from_bank === flow.to_bank;
            const flowDescription = isSelfTransaction ? 
                `<div class="fw-bold">${flow.from_bank || 'Unknown'} <span class="text-info">(Internal)</span></div>` : 
                `<div class="fw-bold">${flow.from_bank || 'Unknown'} → ${flow.to_bank || 'Unknown'}</div>`;
            
            return `
                <div class="d-flex justify-content-between align-items-center py-2 ${index < topFlows.length - 1 ? 'border-bottom' : ''}">
                    <div>
                        ${flowDescription}
                        <small class="text-muted">${flow.count || 0} transaction${flow.count !== 1 ? 's' : ''}</small>
                    </div>
                    <div class="text-end">
                        <div class="fw-bold">$${this.formatNumber(flow.amount || 0)}</div>
                        <span class="badge ${this.getRiskBadgeClass(flow.avg_risk || 0)}">
                            ${((flow.avg_risk || 0) * 100).toFixed(1)}%
                        </span>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    async updateNetworkView(topFlows) {
        try {
            if (!this.networkMap || !topFlows || topFlows.length === 0) {
                console.log('No map or flow data available for network view');
                return;
            }
            
            console.log('Updating world map network view with flows:', topFlows);
            
            // Make sure the map is properly sized
            this.networkMap.invalidateSize();
            
            // Clear existing markers and lines
            this.bankMarkers.forEach(marker => {
                if (marker && this.networkMap) {
                    try { this.networkMap.removeLayer(marker); } catch(e) {}
                }
            });
            this.flowLines.forEach(line => {
                if (line && this.networkMap) {
                    try { this.networkMap.removeLayer(line); } catch(e) {}
                }
            });
            this.bankMarkers = [];
            this.flowLines = [];
            
            // Pre-generate coordinates for banks
            const bankCoordinates = {};
            const banksData = new Map();
            
            // Initialize cache if it doesn't exist
            if (!this.bankCoordinatesCache) {
                this.bankCoordinatesCache = new Map();
            }
            
            // Process all banks to get coordinates
            for (const flow of topFlows) {
                // Process from_bank
                if (!bankCoordinates[flow.from_bank]) {
                    // Check cache first
                    if (this.bankCoordinatesCache.has(flow.from_bank)) {
                        const coords = this.bankCoordinatesCache.get(flow.from_bank);
                        // Add small random offset to prevent exact overlaps
                        bankCoordinates[flow.from_bank] = {
                            lat: coords.lat + (Math.random() - 0.5) * 1,
                            lng: coords.lng + (Math.random() - 0.5) * 1
                        };
                    } else {
                        // Try to fetch real coordinates using bank location as country code
                        try {
                            const coords = await this.fetchCountryCoordinates(flow.from_bank);
                            if (coords) {
                                console.log(`Got real coordinates for ${flow.from_bank}: ${coords.lat}, ${coords.lng}`);
                                // Add small random offset for multiple banks in same country
                                bankCoordinates[flow.from_bank] = {
                                    lat: coords.lat + (Math.random() - 0.5) * 0.5,
                                    lng: coords.lng + (Math.random() - 0.5) * 0.5
                                };
                                this.bankCoordinatesCache.set(flow.from_bank, coords);
                            } else {
                                // Use fallback with random global position if fetch fails
                                const fallbackCoords = { 
                                    lat: (Math.random() * 50) - 25, // Between -25° and 25°
                                    lng: (Math.random() * 180) - 90  // Between -90° and 90°
                                };
                                console.log(`Using fallback coordinates for ${flow.from_bank}`);
                                this.bankCoordinatesCache.set(flow.from_bank, fallbackCoords);
                                bankCoordinates[flow.from_bank] = fallbackCoords;
                            }
                        } catch (error) {
                            // Use fallback with random global position if fetch fails
                            const fallbackCoords = { 
                                lat: (Math.random() * 50) - 25, // Between -25° and 25°
                                lng: (Math.random() * 180) - 90  // Between -90° and 90°
                            };
                            console.log(`Error fetching coordinates for ${flow.from_bank}, using fallback`, error);
                            this.bankCoordinatesCache.set(flow.from_bank, fallbackCoords);
                            bankCoordinates[flow.from_bank] = fallbackCoords;
                        }
                    }
                }
                
                // Process to_bank
                if (!bankCoordinates[flow.to_bank]) {
                    // Check cache first
                    if (this.bankCoordinatesCache.has(flow.to_bank)) {
                        const coords = this.bankCoordinatesCache.get(flow.to_bank);
                        // Add small random offset to prevent exact overlaps
                        bankCoordinates[flow.to_bank] = {
                            lat: coords.lat + (Math.random() - 0.5) * 1,
                            lng: coords.lng + (Math.random() - 0.5) * 1
                        };
                    } else {
                        // Try to fetch real coordinates using bank location as country code
                        try {
                            const coords = await this.fetchCountryCoordinates(flow.to_bank);
                            if (coords) {
                                console.log(`Got real coordinates for ${flow.to_bank}: ${coords.lat}, ${coords.lng}`);
                                // Add small random offset for multiple banks in same country
                                bankCoordinates[flow.to_bank] = {
                                    lat: coords.lat + (Math.random() - 0.5) * 0.5,
                                    lng: coords.lng + (Math.random() - 0.5) * 0.5
                                };
                                this.bankCoordinatesCache.set(flow.to_bank, coords);
                            } else {
                                // Use fallback with random global position if fetch fails
                                const fallbackCoords = { 
                                    lat: (Math.random() * 50) - 25, // Between -25° and 25°
                                    lng: (Math.random() * 180) - 90  // Between -90° and 90°
                                };
                                console.log(`Using fallback coordinates for ${flow.to_bank}`);
                                this.bankCoordinatesCache.set(flow.to_bank, fallbackCoords);
                                bankCoordinates[flow.to_bank] = fallbackCoords;
                            }
                        } catch (error) {
                            // Use fallback with random global position if fetch fails
                            const fallbackCoords = { 
                                lat: (Math.random() * 50) - 25, // Between -25° and 25°
                                lng: (Math.random() * 180) - 90  // Between -90° and 90°
                            };
                            console.log(`Error fetching coordinates for ${flow.to_bank}, using fallback`, error);
                            this.bankCoordinatesCache.set(flow.to_bank, fallbackCoords);
                            bankCoordinates[flow.to_bank] = fallbackCoords;
                        }
                    }
                }
            }
            
            // Second pass - create bank data
            for (const flow of topFlows) {
                if (!banksData.has(flow.from_bank)) {
                    banksData.set(flow.from_bank, {
                        name: flow.from_bank,
                        group: 'Bank',
                        coordinates: bankCoordinates[flow.from_bank],
                        totalOut: 0,
                        totalIn: 0
                    });
                }
                if (!banksData.has(flow.to_bank)) {
                    banksData.set(flow.to_bank, {
                        name: flow.to_bank,
                        group: 'Bank',
                        coordinates: bankCoordinates[flow.to_bank],
                        totalOut: 0,
                        totalIn: 0
                    });
                }
                
                // Update totals
                banksData.get(flow.from_bank).totalOut += flow.amount;
                banksData.get(flow.to_bank).totalIn += flow.amount;
            }
            
            // Add bank markers
            banksData.forEach((bank, bankName) => {
                const coords = bank.coordinates;
                const color = this.getNodeColor(bank.group);
                
                // Create custom marker
                const marker = L.circleMarker([coords.lat, coords.lng], {
                    radius: Math.min(Math.max((bank.totalOut + bank.totalIn) / 50000, 8), 20),
                    fillColor: color,
                    color: '#fff',
                    weight: 3,
                    opacity: 1,
                    fillOpacity: 0.8
                }).addTo(this.networkMap);
                
                // Add popup
                marker.bindPopup(`
                    <div class="bank-popup">
                        <h6>${bank.name}</h6>
                        <p><strong>Region:</strong> ${bank.group}</p>
                        <p><strong>Outflows:</strong> $${this.formatNumber(bank.totalOut)}</p>
                        <p><strong>Inflows:</strong> $${this.formatNumber(bank.totalIn)}</p>
                    </div>
                `);
                
                this.bankMarkers.push(marker);
            });
            
            // Add flow lines
            topFlows.forEach(flow => {
                const fromBank = banksData.get(flow.from_bank);
                const toBank = banksData.get(flow.to_bank);
                
                if (fromBank && toBank) {
                    const fromCoords = fromBank.coordinates;
                    const toCoords = toBank.coordinates;
                    let flowLine;
                    
                    // Check if it's a self-flow (same bank sending to itself)
                    if (flow.from_bank === flow.to_bank) {
                        // Create a circular arc for self-flows
                        // We'll use a circle marker with a customized radius
                        const radius = Math.min(Math.max(flow.amount / 100000, 5), 15);
                        flowLine = L.circle([fromCoords.lat, fromCoords.lng], {
                            radius: radius * 1000, // Convert to meters
                            color: this.getLinkColor(flow.avg_risk),
                            weight: Math.min(Math.max(flow.amount / 100000, 2), 8),
                            fill: false,
                            opacity: 0.7,
                            dashArray: this.getFlowDashArray(flow.avg_risk)
                        }).addTo(this.networkMap);
                    } else {
                        // Normal flow between different banks
                        flowLine = L.polyline([
                            [fromCoords.lat, fromCoords.lng],
                            [toCoords.lat, toCoords.lng]
                        ], {
                            color: this.getLinkColor(flow.avg_risk),
                            weight: Math.min(Math.max(flow.amount / 100000, 2), 8),
                            opacity: 0.7,
                            dashArray: this.getFlowDashArray(flow.avg_risk)
                        }).addTo(this.networkMap);
                    }
                    
                    // Add popup to flow line
                    flowLine.bindPopup(`
                        <div class="flow-popup">
                            <h6>${flow.from_bank} ${flow.from_bank === flow.to_bank ? '(Internal)' : '→ ' + flow.to_bank}</h6>
                            <p><strong>Amount:</strong> $${this.formatNumber(flow.amount)}</p>
                            <p><strong>Transactions:</strong> ${flow.count}</p>
                            <p><strong>Risk Level:</strong> ${(flow.avg_risk * 100).toFixed(1)}%</p>
                        </div>
                    `);
                    
                    this.flowLines.push(flowLine);
                }
            });
            
            // Center the map to fit all markers
            if (this.bankMarkers.length > 0) {
                const group = new L.featureGroup(this.bankMarkers);
                this.networkMap.fitBounds(group.getBounds(), { padding: [30, 30] });
            }
        } catch (error) {
            console.error('Error updating network view:', error);
            const container = document.getElementById('multi-currency-network');
            if (container) {
                container.innerHTML += '<div class="alert alert-warning position-absolute" style="bottom:10px;left:10px;right:10px;z-index:1000">Error displaying network data. Try refreshing.</div>';
            }
        }
    }
    
    // getBankGroup was removed - using a generic 'Bank' group instead
    
    // Helper function to fetch country coordinates
    async fetchCountryCoordinates(countrycode) {
        try {
            // Map bank location codes to proper ISO codes if needed
        
            
            // Standardize the country code - use mapping if available
            const standardizedCode = countrycode;
            console.log(`Fetching coordinates for ${countrycode} (mapped to ${standardizedCode})`);
            
            const response = await fetch(`https://restcountries.com/v3.1/alpha/${standardizedCode}`);
            
            // Check if response is ok before processing
            if (!response.ok) {
                console.error(`Error fetching country data: ${response.status} ${response.statusText}`);
                return null;
            }
            
            const data = await response.json();
            if (data && data.length > 0 && data[0].latlng) {
                return {
                    lat: data[0].latlng[0],
                    lng: data[0].latlng[1],
					                name: data[0].name.common, // ✅ add country name

                };
            } else {
                console.error('No location data found in response', data);
            }
        } catch (error) {
            console.error(`Error fetching coordinates for ${countrycode}:`, error);
        }
        return null; // Return null if there's an error or no data
    }
    
    // The getBankCoordinates function has been removed and functionality is now handled directly in updateNetworkView
    
    // Simple hash function kept for compatibility with node color generation
    simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return Math.abs(hash);
    }
    
    getNodeColor(group) {
        // Generate consistent colors based on group name
        if (!this.colorCache) {
            this.colorCache = new Map();
        }
        
        if (this.colorCache.has(group)) {
            return this.colorCache.get(group);
        }
        
        // Generate color based on group name hash
        const hash = this.simpleHash(group);
        const hue = (hash % 360);
        const saturation = 70 + (hash % 30); // 70-100%
        const lightness = 45 + (hash % 20);  // 45-65%
        
        const color = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
        this.colorCache.set(group, color);
        return color;
    }
    
    getLinkColor(risk) {
        if (risk >= 0.7) return '#dc3545'; // Red for high risk
        if (risk >= 0.4) return '#ffc107'; // Yellow for medium risk
        return '#28a745'; // Green for low risk
    }
    
    getFlowDashArray(risk) {
        if (risk >= 0.7) return '10, 5'; // Dashed for high risk
        if (risk >= 0.4) return '5, 5'; // Small dashes for medium risk
        return null; // Solid line for low risk
    }
    
    toggleCurrencyView() {
        console.log('Toggling flow visibility');
        
        if (!this.networkMap) {
            console.log('Map not initialized');
            return;
        }
        
        const button = document.getElementById('toggle-currency-edges');
        const isHidden = button.classList.contains('flows-hidden');
        
        if (isHidden) {
            // Show flows
            this.flowLines.forEach(line => {
                this.networkMap.addLayer(line);
            });
            button.classList.remove('flows-hidden');
            button.innerHTML = '<i class="fas fa-eye-slash"></i> Hide Flows';
        } else {
            // Hide flows
            this.flowLines.forEach(line => {
                this.networkMap.removeLayer(line);
            });
            button.classList.add('flows-hidden');
            button.innerHTML = '<i class="fas fa-eye"></i> Show Flows';
        }
    }
    
    // Helper methods
    getTransactionRowClass(riskScore) {
        if (riskScore >= 0.7) return 'table-danger';
        if (riskScore >= 0.3) return 'table-warning';
        return '';
    }
    
    getRiskBadgeClass(riskScore) {
        if (riskScore >= 0.7) return 'bg-danger';
        if (riskScore >= 0.3) return 'bg-warning text-dark';
        return 'bg-success';
    }
    
    getStatusBadgeClass(status) {
        switch(status) {
            case 'suspicious': return 'bg-danger';
            case 'flagged': return 'bg-warning text-dark';
            case 'reviewed': return 'bg-info';
            default: return 'bg-success';
        }
    }
    
    formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
    
    formatCurrency(amount, currency) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency || 'USD'
        }).format(amount);
    }
    
    formatNumber(amount) {
        return new Intl.NumberFormat('en-US').format(amount);
    }
    
    // Modal functions
    async showTransactionDetails(transactionId) {
        try {
            const response = await fetch(`/api/transactions/${transactionId}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const transaction = await response.json();
            
            const modal = document.getElementById('transaction-details-modal');
            if (!modal) {
                console.error('Modal not found!');
                return;
            }
            
            // Populate modal
            const modalBody = modal.querySelector('.modal-body');
            if (modalBody) {
                modalBody.innerHTML = `
                    <div class="transaction-details-content">
                        <div class="details-section">
                            <h6><i class="fas fa-info-circle"></i> Transaction Details</h6>
                            <div class="detail-item">
                                <strong>Transaction ID:</strong> ${transaction._id || transactionId}
                            </div>
                            <div class="detail-item">
                                <strong>Timestamp:</strong> ${transaction.timestamp ? this.formatDateTime(transaction.timestamp) : 'N/A'}
                            </div>
                            <div class="detail-item">
                                <strong>Amount:</strong> ${transaction.amount_received ? this.formatCurrency(transaction.amount_received, transaction.receiving_currency) : 'N/A'}
                            </div>
                            <div class="detail-item">
                                <strong>Risk Score:</strong> 
                                <span class="risk-score ${this.getRiskClass(transaction.risk_score || 0)}">
                                    ${((transaction.risk_score || 0) * 100).toFixed(1)}%
                                </span>
                            </div>
                        </div>
                        
                        <div class="details-section">
                            <h6><i class="fas fa-university"></i> Account Information</h6>
                            <div class="detail-item">
                                <strong>From Account:</strong> ${transaction.from_account || 'N/A'}
                            </div>
                            <div class="detail-item">
                                <strong>To Account:</strong> ${transaction.to_account || 'N/A'}
                            </div>
                            <div class="detail-item">
                                <strong>Payment Format:</strong> ${transaction.payment_format || 'N/A'}
                            </div>
                            <div class="detail-item">
                                <strong>Currency:</strong> 
                                <span class="currency-badge">${transaction.receiving_currency || 'N/A'}</span>
                            </div>
                        </div>
                        
                        <div class="details-actions">
                            <button class="btn btn-primary btn-sm" onclick="cashFlowAnalysis.viewNetworkAnalysis('${transactionId}')">
                                <i class="fas fa-network-wired"></i> View Network Analysis
                            </button>
                            <button class="btn btn-info btn-sm" onclick="cashFlowAnalysis.viewAccountHistory('${transaction.from_account || ''}')">
                                <i class="fas fa-history"></i> Account History
                            </button>
                        </div>
                    </div>
                `;
            }
            
            // Show modal
            modal.style.display = 'block';
            modal.classList.add('show');
            document.body.classList.add('modal-open');
            
            // Add close event listeners
            const closeButtons = modal.querySelectorAll('.modal-close');
            closeButtons.forEach(btn => {
                btn.onclick = () => this.closeModal(modal);
            });
            
            // Close on backdrop click
            modal.onclick = (e) => {
                if (e.target === modal) {
                    this.closeModal(modal);
                }
            };
            
        } catch (error) {
            console.error('Error loading transaction details:', error);
            this.showAlert('Error loading transaction details: ' + error.message, 'danger');
        }
    }
    
    getRiskClass(riskScore) {
        if (riskScore >= 0.7) return 'high';
        if (riskScore >= 0.4) return 'medium';
        return 'low';
    }
    
    closeModal(modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
        document.body.classList.remove('modal-open');
    }

    viewNetworkAnalysis(transactionId) {
        // Redirect to network page with transaction context
        window.location.href = `/network?transaction=${transactionId}`;
    }

    viewAccountHistory(accountId) {
        try {
            // Store account filter and redirect to transactions with filter
            this.currentFilters.account = accountId;
            
            // Update the account filter input
            const accountFilter = document.getElementById('account-filter');
            if (accountFilter) {
                accountFilter.value = accountId;
            }
            
            // Reload transactions with the new filter
            this.loadTransactions();
            
            // Close modal using our custom modal system
            const modal = document.getElementById('transaction-details-modal');
            if (modal) {
                this.closeModal(modal);
            }
            
            // Show success message
            this.showAlert(`Showing transaction history for account: ${accountId}`, 'info');
            
        } catch (error) {
            console.error('Error viewing account history:', error);
            this.showAlert('Error loading account history', 'danger');
        }
    }
    
    async flagTransaction(transactionId) {
        try {
            const response = await fetch(`/api/transactions/${transactionId}/flag`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (response.ok) {
                this.loadTransactions(); // Refresh the table
                this.showAlert('Transaction flagged successfully', 'success');
            }
            
        } catch (error) {
            console.error('Error flagging transaction:', error);
            this.showAlert('Error flagging transaction', 'danger');
        }
    }
    
    applyFilters() {
        this.currentPage = 1;
        this.loadTransactions();
        this.loadCurrencyOverview();
    }
    
    exportData() {
        const filters = this.getFilters();
        const params = new URLSearchParams(filters);
        params.set('export', 'true');
        
        window.open(`/api/cash-flow/export?${params}`, '_blank');
    }
    
    showTransactionError(message) {
        const tbody = document.querySelector('#transactions-table tbody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-4">
                        <i class="fas fa-exclamation-triangle fa-2x text-danger mb-2"></i>
                        <p class="text-danger mb-2">${message}</p>
                        <button class="btn btn-primary btn-sm" onclick="cashFlowAnalysis.loadTransactions()">
                            <i class="fas fa-sync"></i> Retry
                        </button>
                    </td>
                </tr>
            `;
        }
    }
    
    showAlert(message, type = 'info') {
        const alertContainer = document.querySelector('#alerts-container') || document.body;
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.cashFlowAnalysis = new CashFlowAnalysis();
});