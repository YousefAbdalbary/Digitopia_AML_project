// Dashboard JavaScript - AML Detection Platform

class Dashboard {
    constructor() {
        this.map = null;
        this.refreshInterval = null;
        this.charts = {};
        
        this.init();
    }
    
    init() {
        this.initializeMap();
        this.loadDashboardData();
        this.setupEventListeners();
        this.startAutoRefresh();
    }
    
    setupEventListeners() {
        // Map controls - Enhanced filtering
        document.getElementById('map-currency')?.addEventListener('change', () => {
            this.applyMapFilters();
        });
        
        document.getElementById('map-period')?.addEventListener('change', () => {
            this.applyMapFilters();
        });
        
        document.getElementById('map-min-amount')?.addEventListener('change', () => {
            this.applyMapFilters();
        });
        
        document.getElementById('map-risk-level')?.addEventListener('change', () => {
            this.applyMapFilters();
        });
        
        document.getElementById('apply-map-filters')?.addEventListener('click', () => {
            this.applyMapFilters();
        });
        
        document.getElementById('reset-map-filters')?.addEventListener('click', () => {
            this.resetMapFilters();
        });
        
        document.getElementById('refresh-map')?.addEventListener('click', () => {
            this.loadMapData();
        });
        
        // Volume chart period
        document.getElementById('volume-period')?.addEventListener('change', () => {
            this.loadVolumeChart();
        });
        
        // Quick actions
        document.getElementById('run-ai-analysis')?.addEventListener('click', () => {
            this.runAIAnalysis();
        });
        
        document.getElementById('export-report')?.addEventListener('click', () => {
            this.exportDashboardReport();
        });
        
        document.getElementById('create-alert')?.addEventListener('click', () => {
            this.showCreateAlertModal();
        });
    }
    
    async loadDashboardData() {
        try {
            const data = await amlPlatform.apiCall(amlPlatform.apiEndpoints.dashboardStats);
            this.updateKPIs(data);
            this.loadRiskDistributionChart(data.risk_distribution);
            this.loadCurrencyBreakdown(data.currency_breakdown);
            this.loadRecentAlerts();
            this.loadRiskyAccounts();
            this.loadVolumeChart();
            this.loadMapData();
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }
    
    updateKPIs(data) {
        // Update KPI values
        document.getElementById('suspicious-transactions').textContent = 
            amlPlatform.formatNumber(data.suspicious_transactions || 0);
        
        document.getElementById('monitored-accounts').textContent = 
            amlPlatform.formatNumber(data.monitored_accounts || 0);
        
        document.getElementById('daily-risk-rate').textContent = 
            `${data.daily_risk_rate || 0}%`;
        
        document.getElementById('cash-flow-volume').textContent = 
            amlPlatform.formatCurrency(data.cash_flow_volume || 0);
        
        // Update change indicators (would typically compare with previous period)
        // For now, using placeholder values
        document.getElementById('suspicious-change').textContent = '+12%';
        document.getElementById('accounts-change').textContent = '+5%';
        document.getElementById('risk-change').textContent = '-3%';
        document.getElementById('volume-change').textContent = '+18%';
    }
    
    loadRiskDistributionChart(riskData) {
        const config = {
            type: 'doughnut',
            data: {
                labels: ['Low Risk', 'Medium Risk', 'High Risk'],
                datasets: [{
                    data: [
                        riskData?.low || 0,
                        riskData?.medium || 0,
                        riskData?.high || 0
                    ],
                    backgroundColor: [
                        '#4caf50',
                        '#ff9800',
                        '#f44336'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed * 100) / total).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        };
        
        amlPlatform.createChart('risk-distribution-chart', config);
    }
    
    loadCurrencyBreakdown(currencyData) {
        const container = document.getElementById('currency-breakdown');
        if (!container || !currencyData) return;
        
        container.innerHTML = '';
        
        currencyData.forEach(currency => {
            const item = document.createElement('div');
            item.className = 'currency-item';
            
            const percentage = ((currency.total_volume / currencyData.reduce((sum, c) => sum + c.total_volume, 0)) * 100).toFixed(1);
            
            item.innerHTML = `
                <div class="currency-info">
                    <div class="currency-code">${currency._id}</div>
                    <div class="currency-amount">${amlPlatform.formatCurrency(currency.total_volume, currency._id)}</div>
                </div>
                <div class="currency-percentage">
                    <div class="percentage-bar">
                        <div class="percentage-fill" style="width: ${percentage}%"></div>
                    </div>
                    <span class="percentage-text">${percentage}%</span>
                </div>
            `;
            
            container.appendChild(item);
        });
    }
    
   async loadRecentAlerts() {
    try {
        console.log('Loading recent alerts...');
        
        const result = await amlPlatform.apiCall(`${amlPlatform.apiEndpoints.alerts}?status=active&limit=5`);
        
        console.log('Alerts API response:', result);
        
        // استخراج الـ alerts من الـ response
        const alerts = result.alerts || result.data?.alerts || result;
        
        const container = document.getElementById('recent-alerts');
        
        if (!container) {
            console.error('Alerts container not found!');
            return;
        }
        
        container.innerHTML = '';
        
        // تحقق أن alerts هو array
        if (!Array.isArray(alerts) || alerts.length === 0) {
            container.innerHTML = '<div class="no-data">No recent alerts</div>';
            console.log('No alerts found or alerts is not an array');
            return;
        }
        
        console.log(`Displaying ${alerts.length} alerts`);
        
        alerts.forEach(alert => {
            const alertItem = document.createElement('div');
            alertItem.className = 'alert-item';
            
            const title = alert.title || alert.type || 'Alert';
            const description = alert.description || 'No description available';
            const priority = alert.priority || 'medium';
            const createdAt = alert.created_at || alert.createdAt;
            
            alertItem.innerHTML = `
                <div class="alert-icon ${priority}">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <div class="alert-content">
                    <div class="alert-title">${title}</div>
                    <div class="alert-description">${description}</div>
                </div>
                <div class="alert-time">${amlPlatform.formatDate(createdAt)}</div>
            `;
            
            alertItem.addEventListener('click', () => {
                window.location.href = `/alerts?id=${alert._id || alert.id}`;
            });
            
            container.appendChild(alertItem);
        });
        
    } catch (error) {
        console.error('Error loading recent alerts:', error);
        const container = document.getElementById('recent-alerts');
        if (container) {
            container.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Error loading alerts: ${error.message}</p>
                </div>
            `;
        }
    }
}
    
    async loadRiskyAccounts() {
        try {
            // Get high-risk transactions and extract unique accounts
            const transactions = await amlPlatform.apiCall(`${amlPlatform.apiEndpoints.transactions}?risk_level=high&limit=20`);
            const container = document.getElementById('risky-accounts');
            
            if (!container) return;
            
            container.innerHTML = '';
            
            if (!transactions || transactions.length === 0) {
                container.innerHTML = '<div class="no-data">No high-risk accounts</div>';
                return;
            }
            
            // Group by account and calculate risk metrics
            const accountRisks = {};
            transactions.forEach(t => {
                const account = t.from_account;
                if (!accountRisks[account]) {
                    accountRisks[account] = {
                        account_id: account,
                        risk_scores: [],
                        transaction_count: 0,
                        total_amount: 0
                    };
                }
                accountRisks[account].risk_scores.push(t.risk_score);
                accountRisks[account].transaction_count++;
                accountRisks[account].total_amount += t.amount_received || 0;
            });
            
            // Sort by average risk score
            const sortedAccounts = Object.values(accountRisks)
                .map(acc => ({
                    ...acc,
                    avg_risk_score: acc.risk_scores.reduce((sum, score) => sum + score, 0) / acc.risk_scores.length
                }))
                .sort((a, b) => b.avg_risk_score - a.avg_risk_score)
                .slice(0, 5);
            
            sortedAccounts.forEach(account => {
                const accountItem = document.createElement('div');
                accountItem.className = 'account-item';
                accountItem.innerHTML = `
                    <div class="account-id">${account.account_id.substring(0, 8)}...</div>
                    <div class="account-risk">
                        <div class="risk-score" style="color: ${amlPlatform.getRiskColor(account.avg_risk_score)}">
                            ${(account.avg_risk_score * 100).toFixed(1)}%
                        </div>
                        <div class="risk-level">${amlPlatform.getRiskLevel(account.avg_risk_score)} Risk</div>
                    </div>
                    <div class="account-stats">
                        <div>${account.transaction_count} transactions</div>
                        <div>${amlPlatform.formatCurrency(account.total_amount)}</div>
                    </div>
                `;
                
                accountItem.addEventListener('click', () => {
                    window.location.href = `/accounts?id=${account.account_id}`;
                });
                
                container.appendChild(accountItem);
            });
        } catch (error) {
            console.error('Error loading risky accounts:', error);
        }
    }
    
    async loadVolumeChart() {
        const period = document.getElementById('volume-period')?.value || '7d';
        
        try {
            // Fetch real transaction volume data from API
            const response = await fetch(`/api/dashboard/volume-trends?period=${period}`);
            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || 'Failed to load volume data');
            }
            
            const volumeData = result.data;
            const labels = volumeData.map(item => item.label);
            const values = volumeData.map(item => item.volume);
            const counts = volumeData.map(item => item.count);
            
            const config = {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Transaction Volume',
                        data: values,
                        borderColor: 'var(--accent-color)',
                        backgroundColor: 'rgba(255, 122, 69, 0.1)',
                        fill: true,
                        tension: 0.4,
                        yAxisID: 'y'
                    }, {
                        label: 'Transaction Count',
                        data: counts,
                        borderColor: 'var(--secondary-color)',
                        backgroundColor: 'rgba(102, 153, 255, 0.1)',
                        fill: false,
                        tension: 0.4,
                        yAxisID: 'y1',
                        hidden: true  // Hidden by default, can be toggled
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    aspectRatio: 2,
                    layout: {
                        padding: {
                            top: 10,
                            bottom: 10,
                            left: 5,
                            right: 5
                        }
                    },
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return amlPlatform.formatCurrency(value);
                                }
                            },
                            title: {
                                display: true,
                                text: 'Volume (USD)'
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            beginAtZero: true,
                            grid: {
                                drawOnChartArea: false,
                            },
                            title: {
                                display: true,
                                text: 'Transaction Count'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                padding: 20
                            }
                        },
                        tooltip: {
                            callbacks: {
                                title: function(context) {
                                    const dataIndex = context[0].dataIndex;
                                    const dataPoint = volumeData[dataIndex];
                                    return `${dataPoint.label} (${dataPoint.date})`;
                                },
                                label: function(context) {
                                    const dataIndex = context.dataIndex;
                                    const dataPoint = volumeData[dataIndex];
                                    
                                    if (context.datasetIndex === 0) {
                                        return [
                                            `Volume: ${amlPlatform.formatCurrency(context.parsed.y)}`,
                                            `Transactions: ${dataPoint.count}`,
                                            `Avg Amount: ${amlPlatform.formatCurrency(dataPoint.avg_amount)}`,
                                            `Max Amount: ${amlPlatform.formatCurrency(dataPoint.max_amount)}`
                                        ];
                                    } else {
                                        return `Transaction Count: ${context.parsed.y}`;
                                    }
                                }
                            }
                        },
                        title: {
                            display: true,
                            text: `Transaction Volume Trends - ${period.toUpperCase()}`,
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        }
                    }
                }
            };
            
            amlPlatform.createChart('volume-trend-chart', config);
            
            // Update summary statistics
            this.updateVolumeSummary(result);
            
        } catch (error) {
            console.error('Error loading volume chart:', error);
            
            // Show error message to user
            const chartContainer = document.getElementById('volume-trend-chart');
            if (chartContainer) {
                chartContainer.innerHTML = `
                    <div class="chart-error">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>Error loading volume data: ${error.message}</p>
                        <button onclick="dashboard.loadVolumeChart()" class="btn btn-sm btn-primary">
                            <i class="fas fa-sync"></i> Retry
                        </button>
                    </div>
                `;
            }
        }
    }
    
    updateVolumeSummary(volumeResult) {
        try {
            // Update volume summary cards or statistics
            const summaryContainer = document.getElementById('volume-summary');
            if (summaryContainer) {
                summaryContainer.innerHTML = `
                    <div class="volume-stat">
                        <span class="stat-label">Total Volume</span>
                        <span class="stat-value">${amlPlatform.formatCurrency(volumeResult.total_volume)}</span>
                    </div>
                    <div class="volume-stat">
                        <span class="stat-label">Total Transactions</span>
                        <span class="stat-value">${amlPlatform.formatNumber(volumeResult.total_transactions)}</span>
                    </div>
                    <div class="volume-stat">
                        <span class="stat-label">Avg Volume/Period</span>
                        <span class="stat-value">${amlPlatform.formatCurrency(volumeResult.avg_volume_per_period)}</span>
                    </div>
                    <div class="volume-stat">
                        <span class="stat-label">Period</span>
                        <span class="stat-value">${volumeResult.period.toUpperCase()}</span>
                    </div>
                `;
            }
            
            // Update any other volume-related UI elements
            const periodLabel = document.getElementById('volume-period-label');
            if (periodLabel) {
                periodLabel.textContent = `Last ${volumeResult.period.toUpperCase()}`;
            }
            
        } catch (error) {
            console.error('Error updating volume summary:', error);
        }
    }
    
    initializeMap() {
        const mapContainer = document.getElementById('world-map');
        if (!mapContainer) return;
        
        // Initialize enhanced Leaflet map
        this.map = L.map('world-map', { attributionControl: false }).setView([20, 0], 2);
        
        // Add dark tile layer
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            subdomains: 'abcd',
            maxZoom: 19,
            attribution: ''
        }).addTo(this.map);
        
        // Initialize animated layer and pulse intervals
        this.animatedLayer = L.layerGroup().addTo(this.map);
        this.pulseIntervals = [];
        
        // Initialize with sample data
        this.loadMapData();
    }
    
    // Get current filter values
    getMapFilters() {
        return {
            currency: document.getElementById('map-currency')?.value || 'ALL',
            period: document.getElementById('map-period')?.value || '30d',
            minAmount: document.getElementById('map-min-amount')?.value || '0',
            riskLevel: document.getElementById('map-risk-level')?.value || 'all'
        };
    }
    
    // Apply filters and reload map
    async applyMapFilters() {
        const filters = this.getMapFilters();
        
        // Show loading indicator
        this.showMapLoading();
        
        try {
            const params = new URLSearchParams({
                currency: filters.currency,
                time_period: filters.period,
                min_amount: filters.minAmount,
                risk_level: filters.riskLevel
            });
            
            const data = await amlPlatform.apiCall(
                `${amlPlatform.apiEndpoints.cashFlowMap}?${params.toString()}`
            );
            
            // Apply client-side filtering for better user experience
            const filteredData = this.applyClientSideFilters(data, filters);
            this.updateEnhancedMap(filteredData);
            
            // Update filter stats
            this.updateFilterStats(filteredData);
            
        } catch (error) {
            console.error('Error applying map filters:', error);
            this.showMapError('Failed to apply filters. Please try again.');
        } finally {
            this.hideMapLoading();
        }
    }
    
    // Apply additional client-side filtering
    applyClientSideFilters(data, filters) {
        if (!data.nodes || !data.flows) return data;
        
        let filteredNodes = [...data.nodes];
        let filteredFlows = [...data.flows];
        
        // Filter by minimum amount
        if (filters.minAmount > 0) {
            const minAmount = parseFloat(filters.minAmount) / 1000000; // Convert to millions
            filteredNodes = filteredNodes.filter(node => node.volume >= minAmount);
            filteredFlows = filteredFlows.filter(flow => flow.amount >= parseFloat(filters.minAmount));
        }
        
        // Filter by risk level
        if (filters.riskLevel !== 'all') {
            const riskFilter = (risk) => {
                switch (filters.riskLevel) {
                    case 'high': return risk >= 0.7;
                    case 'medium': return risk >= 0.4 && risk < 0.7;
                    case 'low': return risk < 0.4;
                    default: return true;
                }
            };
            
            filteredNodes = filteredNodes.filter(node => riskFilter(node.risk));
            filteredFlows = filteredFlows.filter(flow => riskFilter(flow.risk));
        }
        
        return {
            ...data,
            nodes: filteredNodes,
            flows: filteredFlows,
            total_volume: filteredNodes.reduce((sum, node) => sum + node.volume, 0),
            total_flows: filteredFlows.length
        };
    }
    
    // Reset filters to default values
    resetMapFilters() {
        document.getElementById('map-currency').value = 'ALL';
        document.getElementById('map-period').value = '30d';
        document.getElementById('map-min-amount').value = '0';
        document.getElementById('map-risk-level').value = 'all';
        
        this.applyMapFilters();
    }
    
    // Show loading indicator
    showMapLoading() {
        const mapContainer = document.getElementById('world-map');
        if (mapContainer) {
            mapContainer.style.opacity = '0.5';
            mapContainer.style.pointerEvents = 'none';
        }
        
        // Show loading spinner on apply button
        const applyButton = document.getElementById('apply-map-filters');
        if (applyButton) {
            applyButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Applying...';
            applyButton.disabled = true;
        }
    }
    
    // Hide loading indicator
    hideMapLoading() {
        const mapContainer = document.getElementById('world-map');
        if (mapContainer) {
            mapContainer.style.opacity = '1';
            mapContainer.style.pointerEvents = 'auto';
        }
        
        // Reset apply button
        const applyButton = document.getElementById('apply-map-filters');
        if (applyButton) {
            applyButton.innerHTML = '<i class="fas fa-filter"></i> Apply Filters';
            applyButton.disabled = false;
        }
    }
    
    // Show map error
    showMapError(message) {
        const mapContainer = document.getElementById('world-map');
        if (mapContainer) {
            mapContainer.innerHTML = `
                <div class="map-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>${message}</p>
                    <button onclick="dashboard.applyMapFilters()" class="btn btn-primary">
                        <i class="fas fa-retry"></i> Retry
                    </button>
                </div>
            `;
        }
    }
    
    // Update filter statistics
    updateFilterStats(data) {
        console.log('Updating filter stats with data:', data);
        const statsContainer = document.querySelector('.map-filter-stats');
        if (statsContainer) {
            const nodes = data.nodes?.length || 0;
            const flows = data.flows?.length || 0;
            const volume = data.total_volume || 0;
            
            console.log(`Stats: ${nodes} locations, ${flows} flows, $${volume.toFixed(1)}M volume`);
            
            statsContainer.innerHTML = `
                <div class="filter-stat">
                    <span class="stat-value">${nodes}</span>
                    <span class="stat-label">Locations</span>
                </div>
                <div class="filter-stat">
                    <span class="stat-value">${flows}</span>
                    <span class="stat-label">Flows</span>
                </div>
                <div class="filter-stat">
                    <span class="stat-value">$${volume.toFixed(1)}M</span>
                    <span class="stat-label">Total Volume</span>
                </div>
            `;
        } else {
            console.error('Stats container not found!');
        }
    }
    
    async loadMapData() {
        const currency = document.getElementById('map-currency')?.value || 'USD';
        const period = document.getElementById('map-period')?.value || '30d';
        
        try {
            const data = await amlPlatform.apiCall(
                `${amlPlatform.apiEndpoints.cashFlowMap}?currency=${currency}&time_period=${period}`
            );
            
            console.log('Map data received:', data);
            this.updateEnhancedMap(data);
            this.updateFilterStats(data);  // Update stats after loading data
        } catch (error) {
            console.error('Error loading map data:', error);
            // Load sample data for demo
            this.loadEnhancedSampleMapData();
        }
    }
    
    async loadEnhancedSampleMapData() {
        // Generate dynamic sample data instead of hardcoded values
        const sampleData = await this.generateDynamicSampleData();
        this.updateEnhancedMap(sampleData);
        this.updateFilterStats(sampleData);  // Update stats with sample data
    }
    
    async generateDynamicSampleData() {
        // Helper function to fetch country coordinates
        const fetchCountryCoordinates = async (code) => {
            try {
                const response = await fetch(`https://restcountries.com/v3.1/alpha/${code}`);
                const data = await response.json();
                if (data.length > 0) {
                    return {
                        lat: data[0].latlng[0],
                        lng: data[0].latlng[1],
                        name: data[0].name.common
                    };
                }
            } catch (error) {
                console.error('Error fetching country coordinates:', error);
            }
            return null;
        };
        
        // Sample country codes for demonstration
        const countryCodes = ['US', 'GB', 'JP', 'SG', 'HK', 'CH', 'KY', 'AE', 'DE', 'FR'];
        const amlNodes = [];
        
        // Generate nodes with real coordinates
        for (const code of countryCodes) {
            const coords = await fetchCountryCoordinates(code);
            if (coords) {
                amlNodes.push({
                    id: coords.name.replace(/\s+/g, ''),
                    lat: coords.lat,
                    lng: coords.lng,
                    volume: Math.floor(Math.random() * 400) + 200, // 200-600M
                    risk: Math.random() * 0.8 + 0.1 // 0.1-0.9
                });
            }
        }
        
        // Generate flows between nodes
        const amlFlows = [];
        const flowCount = Math.min(8, amlNodes.length - 1);
        
        for (let i = 0; i < flowCount; i++) {
            const source = amlNodes[i % amlNodes.length];
            const target = amlNodes[(i + 1) % amlNodes.length];
            
            if (source && target && source.id !== target.id) {
                amlFlows.push({
                    source: source.id,
                    target: target.id,
                    amount: Math.floor(Math.random() * 200000000) + 100000000, // 100M-300M
                    risk: Math.random() * 0.8 + 0.1
                });
            }
        }
        
        return {
            nodes: amlNodes,
            flows: amlFlows,
            total_volume: amlNodes.reduce((sum, node) => sum + node.volume, 0),
            total_flows: amlFlows.length
        };
    }
    
    updateEnhancedMap(data) {
        if (!this.map) return;
        
        const amlNodes = data.nodes || [];
        const amlFlows = data.flows || [];
        
        // Initialize animated layer if not exists
        if (!this.animatedLayer) {
            this.animatedLayer = L.layerGroup().addTo(this.map);
            this.pulseIntervals = [];
        }
        
        // Clear existing layers and intervals
        this.animatedLayer.clearLayers();
        if (this.pulseIntervals) {
            this.pulseIntervals.forEach(id => clearInterval(id));
            this.pulseIntervals = [];
        }
        
        // Helper functions
        const riskColor = (risk) => {
            return risk > 0.7 ? 'red' : risk > 0.4 ? 'orange' : 'green';
        };
        
        const getTooltip = (node) => {
            return `<b>${node.id}</b><br>
                    Liquidity: $${(node.volume * 1.2).toFixed(1)}M / €${(node.volume * 1.1).toFixed(1)}M / £${(node.volume * 0.9).toFixed(1)}M<br>
                    Risk Score: ${(node.risk * 100).toFixed(0)}%<br>
                    Transaction Volume: ${node.volume}M`;
        };
        
        // رسم النقاط مع حركة pulse فقط للنقاط المفلترة
        const drawNodes = (nodes) => {
            this.animatedLayer.clearLayers();
            this.pulseIntervals.forEach(id => clearInterval(id));
            this.pulseIntervals = [];
            
            nodes.forEach(node => {
                const marker = L.circleMarker([node.lat, node.lng], {
                    radius: Math.sqrt(node.volume) * 2,
                    color: riskColor(node.risk),
                    fillColor: riskColor(node.risk),
                    fillOpacity: 0.5,
                    weight: 2
                }).addTo(this.animatedLayer)
                  .bindTooltip(getTooltip(node));
                
                marker.on('click', () => { 
                    window.location.href = `/network?country=${node.id}`; 
                });
                
                const pulse = L.circle([node.lat, node.lng], {
                    radius: Math.sqrt(node.volume) * 5,
                    color: riskColor(node.risk),
                    fillColor: riskColor(node.risk),
                    fillOpacity: 0.2,
                    weight: 0
                }).addTo(this.animatedLayer);
                
                let growing = true, r = Math.sqrt(node.volume) * 5;
                const intervalID = setInterval(() => {
                    r += growing ? 0.3 : -0.3;
                    if (r > Math.sqrt(node.volume) * 8) growing = false;
                    if (r < Math.sqrt(node.volume) * 5) growing = true;
                    pulse.setRadius(r);
                }, 50);
                this.pulseIntervals.push(intervalID);
            });
        };
        
        // Interpolation helper for flows
        const interpolatePath = (latlngs, t) => {
            const n = latlngs.length - 1;
            let idx = Math.floor(t * n);
            const frac = t * n - idx;
            const p0 = latlngs[idx], p1 = latlngs[Math.min(idx + 1, n)];
            return [p0[0] + (p1[0] - p0[0]) * frac, p0[1] + (p1[1] - p0[1]) * frac];
        };
        
        // Draw nodes
        drawNodes(amlNodes);
        
        // Draw animated flows
        amlFlows.forEach(flow => {
            const src = amlNodes.find(n => n.id === flow.source);
            const tgt = amlNodes.find(n => n.id === flow.target);
            
            if (!src || !tgt) return; // Skip if source or target node not found
            
            const latlngs = [
                [src.lat, src.lng],
                [(src.lat + tgt.lat) / 2 + 5, (src.lng + tgt.lng) / 2],
                [tgt.lat, tgt.lng]
            ];
            
            L.polyline(latlngs, {
                color: riskColor(flow.risk),
                weight: Math.sqrt(flow.amount / 1000000),
                opacity: 0.7
            }).addTo(this.map)
              .bindTooltip(`<b>Flow:</b> ${flow.source} → ${flow.target}<br>
                           Amount: $${(flow.amount / 1000000).toFixed(1)}M<br>
                           Risk: ${(flow.risk * 100).toFixed(0)}%`);
            
            const points = [];
            const count = 5;
            for (let i = 0; i < count; i++) {
                const t = i / count;
                const dot = L.circleMarker(interpolatePath(latlngs, t), {
                    radius: 4,
                    color: 'yellow',
                    fillColor: 'yellow',
                    fillOpacity: 1
                }).addTo(this.animatedLayer);
                points.push({ dot, offset: t });
            }
            
            const animateDots = () => {
                points.forEach(p => {
                    p.offset += 0.005;
                    if (p.offset > 1) p.offset = 0;
                    p.dot.setLatLng(interpolatePath(latlngs, p.offset));
                });
                requestAnimationFrame(animateDots);
            };
            animateDots();
        });
        
        // Update map legend
        this.updateMapLegend();
    }
    
    // Additional method to handle map cleanup
    cleanupMapAnimations() {
        if (this.pulseIntervals) {
            this.pulseIntervals.forEach(id => clearInterval(id));
            this.pulseIntervals = [];
        }
        if (this.animatedLayer) {
            this.animatedLayer.clearLayers();
        }
    }
    
    updateMapLegend() {
        const legendContainer = document.querySelector('.map-legend');
        if (legendContainer) {
            legendContainer.innerHTML = `
                <div class="legend-item">
                    <div class="legend-color" style="background-color: red;"></div>
                    <span>High Risk</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: orange;"></div>
                    <span>Medium Risk</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: green;"></div>
                    <span>Low Risk</span>
                </div>
            `;
        }
    }
    
    // Legacy method for compatibility
    updateMap(data) {
        if (!this.map) return;
        
        // Clear existing layers
        this.map.eachLayer((layer) => {
            if (layer instanceof L.CircleMarker || layer instanceof L.Polyline) {
                this.map.removeLayer(layer);
            }
        });
        
        // Add nodes
        if (data.nodes) {
            data.nodes.forEach(node => {
                const radius = Math.max(5, Math.min(node.volume / 200000, 30));
                const color = amlPlatform.getRiskColor(node.risk_score);
                
                const marker = L.circleMarker([node.lat, node.lng], {
                    radius: radius,
                    fillColor: color,
                    color: 'white',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }).addTo(this.map);
                
                marker.bindPopup(`
                    <div class="map-popup">
                        <h4>${node.name}</h4>
                        <p><strong>Volume:</strong> ${amlPlatform.formatCurrency(node.volume)}</p>
                        <p><strong>Risk Score:</strong> ${(node.risk_score * 100).toFixed(1)}%</p>
                        <p><strong>Risk Level:</strong> ${amlPlatform.getRiskLevel(node.risk_score)}</p>
                    </div>
                `);
                
                marker.on('click', () => {
                    // Navigate to account details or network graph
                    window.location.href = `/network?focus=${node.id}`;
                });
            });
        }
        
        // Add edges (flows)
        if (data.edges) {
            data.edges.forEach(edge => {
                const color = amlPlatform.getRiskColor(edge.risk_score);
                const weight = Math.max(2, Math.min(edge.amount / 100000, 8));
                
                const line = L.polyline([
                    [edge.from.lat, edge.from.lng],
                    [edge.to.lat, edge.to.lng]
                ], {
                    color: color,
                    weight: weight,
                    opacity: 0.7
                }).addTo(this.map);
                
                line.bindPopup(`
                    <div class="map-popup">
                        <h4>Transaction Flow</h4>
                        <p><strong>Amount:</strong> ${amlPlatform.formatCurrency(edge.amount)}</p>
                        <p><strong>Risk Score:</strong> ${(edge.risk_score * 100).toFixed(1)}%</p>
                    </div>
                `);
            });
        }
    }
    
    async runAIAnalysis() {
        try {
            amlPlatform.showLoading('Running AI analysis...');
            
            const result = await amlPlatform.apiCall(amlPlatform.apiEndpoints.analyze, {
                method: 'POST',
                body: JSON.stringify({})
            });
            
            amlPlatform.showNotification(
                `AI Analysis completed: ${result.analyzed_transactions} transactions analyzed, ${result.suspicious_count} suspicious patterns found`,
                'success'
            );
            
            // Refresh dashboard data
            this.loadDashboardData();
        } catch (error) {
            console.error('Error running AI analysis:', error);
            amlPlatform.showNotification('AI analysis failed', 'error');
        }
    }
    
    exportDashboardReport() {
        // Generate dashboard report data
        const reportData = {
            generated_at: new Date().toISOString(),
            suspicious_transactions: document.getElementById('suspicious-transactions').textContent,
            monitored_accounts: document.getElementById('monitored-accounts').textContent,
            daily_risk_rate: document.getElementById('daily-risk-rate').textContent,
            cash_flow_volume: document.getElementById('cash-flow-volume').textContent
        };
        
        // Export as JSON for now (could be enhanced to PDF)
        const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `aml-dashboard-report-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        URL.revokeObjectURL(url);
        
        amlPlatform.showNotification('Dashboard report exported', 'success');
    }
    
    showCreateAlertModal() {
        // This would typically show a modal for creating custom alerts
        amlPlatform.showNotification('Alert creation feature coming soon', 'info');
    }
    
    startAutoRefresh() {
        // Refresh dashboard data every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.loadDashboardData();
        }, 5 * 60 * 1000);
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
});