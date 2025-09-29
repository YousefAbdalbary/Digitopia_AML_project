// Network Analysis JavaScript
class NetworkAnalysis {
    constructor() {
        this.svg = null;
        this.simulation = null;
        this.nodes = [];
        this.links = [];
        this.width = 800;
        this.height = 600;
        
        // World map properties
        this.worldMap = null;
        this.currentView = 'd3'; // 'd3' or 'map'
        this.mapMarkers = [];
        this.mapLines = [];
        this.animatedLayer = null;
        
        // Selection mode properties
        this.selectionMode = false;
        this.selectedFlows = [];
        this.multiSelectEnabled = false; // For ctrl/shift selection
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeVisualization();
        this.initializeWorldMap();
        this.loadNetworkData();
    }
    
    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-network');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadNetworkData());
        }
        
        // Filter changes
        document.querySelectorAll('#focus-account, #network-depth, #min-amount, #risk-filter').forEach(element => {
            element.addEventListener('change', () => this.loadNetworkData());
        });
        
        // Export button
        const exportBtn = document.getElementById('export-network');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportNetwork());
        }
        
        // Pattern analysis
        const analyzeBtn = document.getElementById('analyze-patterns');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => this.analyzePatterns());
        }
        
        // View toggle buttons
        const d3ViewBtn = document.getElementById('toggle-d3-view');
        const mapViewBtn = document.getElementById('toggle-map-view');
        
        if (d3ViewBtn) {
            d3ViewBtn.addEventListener('click', () => this.toggleView('d3'));
        }
        
        if (mapViewBtn) {
            mapViewBtn.addEventListener('click', () => this.toggleView('map'));
        }
        
        // Visualization controls
        const layoutSelect = document.getElementById('layout-type');
        const nodeSizeSelect = document.getElementById('node-size-metric');
        const edgeWidthSelect = document.getElementById('edge-width-metric');
        
        if (layoutSelect) {
            layoutSelect.addEventListener('change', () => this.updateLayout());
        }
        
        if (nodeSizeSelect) {
            nodeSizeSelect.addEventListener('change', () => this.updateNodeSizes());
        }
        
        if (edgeWidthSelect) {
            edgeWidthSelect.addEventListener('change', () => this.updateEdgeWidths());
        }
        
        // Close panel buttons
        const closeDetailsBtn = document.getElementById('close-details');
        const closeEdgeDetailsBtn = document.getElementById('close-edge-details');
        
        if (closeDetailsBtn) {
            closeDetailsBtn.addEventListener('click', () => {
                document.getElementById('node-details-panel').style.display = 'none';
            });
        }
        
        if (closeEdgeDetailsBtn) {
            closeEdgeDetailsBtn.addEventListener('click', () => {
                document.getElementById('edge-details-panel').style.display = 'none';
            });
        }
    }
    
    initializeVisualization() {
        const container = document.getElementById('network-graph');
        if (!container) {
            console.error('Network graph container not found!');
            return;
        }
        
        // Get container dimensions
        const rect = container.getBoundingClientRect();
        this.width = rect.width || 800;
        this.height = rect.height || 600;
        
        // Clear existing content
        container.innerHTML = '';
        
        // Create SVG with responsive dimensions
        this.svg = d3.select('#network-graph')
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .attr('viewBox', `0 0 ${this.width} ${this.height}`)
            .style('background-color', '#f8f9fa')
            .style('border-radius', '8px');
        
        // Add zoom behavior with improved settings
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                // Apply transform to both groups
                this.svg.select('.links').attr('transform', event.transform);
                this.svg.select('.nodes').attr('transform', event.transform);
            });
        
        this.svg.call(zoom);
        
        // Add double-click to reset zoom
        this.svg.on('dblclick.zoom', () => {
            this.svg.transition()
                .duration(750)
                .call(zoom.transform, d3.zoomIdentity);
        });
        
        // Create groups for links and nodes (order matters - links should be drawn first)
        this.svg.append('g').attr('class', 'links');
        this.svg.append('g').attr('class', 'nodes');
        
        // Add resize listener
        window.addEventListener('resize', this.handleResize.bind(this));
    }
    
    handleResize() {
        if (!this.svg) return;
        
        const container = document.getElementById('network-graph');
        if (!container) return;
        
        const rect = container.getBoundingClientRect();
        const newWidth = rect.width || 800;
        const newHeight = rect.height || 600;
        
        // Update dimensions
        this.width = newWidth;
        this.height = newHeight;
        
        // Update SVG size
        this.svg
            .attr('width', this.width)
            .attr('height', this.height)
            .attr('viewBox', `0 0 ${this.width} ${this.height}`);
        
        // Update simulation center if it exists
        if (this.simulation) {
            this.simulation
                .force('center', d3.forceCenter(this.width / 2, this.height / 2))
                .alpha(0.3)
                .restart();
        }
    }
    
    async loadNetworkData() {
        try {
            const filters = this.getFilters();
            const response = await fetch(`/api/network/data?${new URLSearchParams(filters)}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Server error:', errorText);
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Validate data structure
            if (!data || !Array.isArray(data.nodes) || !Array.isArray(data.edges)) {
                throw new Error('Invalid data format received from server');
            }
            
            this.updateVisualization(data);
            this.updateStats(data);
            
        } catch (error) {
            console.error('Error loading network data:', error);
            let errorMessage = 'Failed to load network data. ';
            
            if (error.message.includes('HTTP 500')) {
                errorMessage += 'Server error occurred. Check console for details.';
            } else if (error.message.includes('Invalid data format')) {
                errorMessage += 'Invalid data format received.';
            } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorMessage += 'Network connection error.';
            } else {
                errorMessage += 'Please try again.';
            }
            
            this.showError(errorMessage);
        }
    }
    
    getFilters() {
        return {
            focus_account: document.getElementById('focus-account')?.value || '',
            depth: document.getElementById('network-depth')?.value || '2',
            min_amount: document.getElementById('min-amount')?.value || '1000',
            risk_level: document.getElementById('risk-filter')?.value || 'all'
        };
    }
    
    updateVisualization(data) {
        this.nodes = data.nodes || [];
        this.links = data.edges || data.links || [];  // Handle both 'edges' and 'links'
        
        console.log('Network data:', { nodes: this.nodes.length, links: this.links.length });
        
        // Log bank country codes in links data to verify
        if (this.links.length > 0) {
            console.log('Sample link data:', this.links[0]);
            console.log('Bank codes present:', 
                        'from_bank' in this.links[0], 
                        'to_bank' in this.links[0]);
        }
        
        if (this.nodes.length === 0) {
            this.showEmptyState();
            return;
        }
        
        // Clear existing visualization to prevent overlapping
        this.svg.select('.links').selectAll('*').remove();
        this.svg.select('.nodes').selectAll('*').remove();
        
        // Initialize simulation with improved forces
        this.simulation = d3.forceSimulation(this.nodes)
            .force('link', d3.forceLink(this.links).id(d => d.id).distance(120).strength(0.6))
            .force('charge', d3.forceManyBody().strength(-400))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(d => this.getNodeRadius(d) + 10))
            .alpha(0.9)
            .alphaDecay(0.02)
            .velocityDecay(0.8); // Add velocity decay for smoother movement
        
        this.drawLinks();
        this.drawNodes();
        
        // Improved tick function with boundary constraints
        this.simulation.on('tick', () => {
            // Update links with null checks
            this.svg.selectAll('.link')
                .attr('x1', d => {
                    if (!d.source || typeof d.source.x === 'undefined') return 0;
                    return Math.max(0, Math.min(this.width, d.source.x));
                })
                .attr('y1', d => {
                    if (!d.source || typeof d.source.y === 'undefined') return 0;
                    return Math.max(0, Math.min(this.height, d.source.y));
                })
                .attr('x2', d => {
                    if (!d.target || typeof d.target.x === 'undefined') return 0;
                    return Math.max(0, Math.min(this.width, d.target.x));
                })
                .attr('y2', d => {
                    if (!d.target || typeof d.target.y === 'undefined') return 0;
                    return Math.max(0, Math.min(this.height, d.target.y));
                });
            
            // Update nodes with boundary constraints
            this.svg.selectAll('.node')
                .attr('transform', d => {
                    if (typeof d.x === 'undefined' || typeof d.y === 'undefined') {
                        d.x = this.width / 2;
                        d.y = this.height / 2;
                    }
                    
                    const radius = this.getNodeRadius(d);
                    // Keep nodes within canvas bounds
                    d.x = Math.max(radius, Math.min(this.width - radius, d.x));
                    d.y = Math.max(radius, Math.min(this.height - radius, d.y));
                    
                    return `translate(${d.x},${d.y})`;
                });
        });
        
        // Update world map view if currently visible
        if (this.currentView === 'map') {
            this.updateWorldMapView();
        }
    }
    
    drawLinks() {
        const links = this.svg.select('.links')
            .selectAll('.link')
            .data(this.links, d => `${d.source.id || d.source}-${d.target.id || d.target}`); // Use key function
        
        // Remove old links
        links.exit().remove();
        
        // Add new links
        const linkEnter = links.enter()
            .append('line')
            .attr('class', 'link')
            .style('stroke', d => this.getLinkColor(d.risk_score))
            .style('stroke-width', d => Math.max(2, Math.min(8, d.amount / 500000)))
            .style('opacity', 0.7)
            .style('cursor', 'pointer')
            .style('pointer-events', 'visibleStroke') // Ensure links are clickable
            .on('click', (event, d) => {
                event.stopPropagation();
                this.showEdgeDetails(d);
            })
            .on('mouseover', function(event, d) {
                // Highlight link on hover
                d3.select(this)
                    .transition()
                    .duration(200)
                    .style('stroke-width', d => Math.max(4, Math.min(10, d.amount / 400000)))
                    .style('opacity', 0.9);
            })
            .on('mouseout', function(event, d) {
                // Reset link on mouse out
                d3.select(this)
                    .transition()
                    .duration(200)
                    .style('stroke-width', d => Math.max(2, Math.min(8, d.amount / 500000)))
                    .style('opacity', 0.7);
            });
        
        // Merge enter and update selections
        const allLinks = linkEnter.merge(links);
        
        // Update existing links
        allLinks
            .style('stroke', d => this.getLinkColor(d.risk_score))
            .style('stroke-width', d => Math.max(2, Math.min(8, d.amount / 500000)));
        
        // Add tooltips to links
        allLinks.append('title')
            .text(d => {
                const sourceId = d.source.id || d.source;
                const targetId = d.target.id || d.target;
                return `${sourceId} → ${targetId}\nAmount: $${(d.amount || 0).toLocaleString()}\nRisk: ${((d.risk_score || 0) * 100).toFixed(1)}%`;
            });
        
        return allLinks;
    }
    
    drawNodes() {
        const nodes = this.svg.select('.nodes')
            .selectAll('.node')
            .data(this.nodes, d => d.id); // Use key function for proper data binding
        
        // Remove old nodes
        nodes.exit().remove();
        
        // Create new node groups
        const nodeEnter = nodes.enter()
            .append('g')
            .attr('class', 'node')
            .style('cursor', 'grab')
            .on('click', (event, d) => {
                event.stopPropagation();
                this.showNodeDetails(d);
            })
            .on('mouseover', function(event, d) {
                // Highlight on hover
                d3.select(this).select('circle')
                    .transition()
                    .duration(200)
                    .attr('r', d => this.getNodeRadius(d) * 1.2)
                    .style('stroke-width', 3);
            }.bind(this))
            .on('mouseout', function(event, d) {
                // Reset on mouse out
                d3.select(this).select('circle')
                    .transition()
                    .duration(200)
                    .attr('r', d => this.getNodeRadius(d))
                    .style('stroke-width', 2);
            }.bind(this))
            .call(d3.drag()
                .on('start', (event, d) => {
                    d3.select(event.sourceEvent.target).style('cursor', 'grabbing');
                    this.dragstarted(event, d);
                })
                .on('drag', (event, d) => {
                    this.dragged(event, d);
                })
                .on('end', (event, d) => {
                    d3.select(event.sourceEvent.target).style('cursor', 'grab');
                    this.dragended(event, d);
                }));
        
        // Add circle to new nodes
        nodeEnter.append('circle')
            .attr('r', d => this.getNodeRadius(d))
            .style('fill', d => this.getNodeColor(d.avg_risk_score || d.risk_score))
            .style('stroke', '#fff')
            .style('stroke-width', 2)
            .style('filter', 'drop-shadow(2px 2px 4px rgba(0,0,0,0.3))'); // Add shadow for better visibility
        
        // Add text labels to new nodes
        nodeEnter.append('text')
            .attr('dy', '.35em')
            .attr('text-anchor', 'middle')
            .style('font-size', '10px')
            .style('font-weight', 'bold')
            .style('fill', '#333')
            .style('pointer-events', 'none') // Prevent text from interfering with drag
            .text(d => d.id.substring(0, 6)); // Show first 6 characters of ID
        
        // Merge enter and update selections
        const allNodes = nodeEnter.merge(nodes);
        
        // Update existing nodes
        allNodes.select('circle')
            .attr('r', d => this.getNodeRadius(d))
            .style('fill', d => this.getNodeColor(d.avg_risk_score || d.risk_score));
        
        // Add tooltips
        allNodes.append('title')
            .text(d => `Account: ${d.id}\nTransactions: ${d.transaction_count || 0}\nRisk Score: ${((d.avg_risk_score || d.risk_score || 0) * 100).toFixed(1)}%`);
        
        return allNodes;
    }
    
    getNodeRadius(node) {
        const baseRadius = 15;
        const sizeBy = document.querySelector('[name="node_size"]')?.value || 'transaction_count';
        
        switch(sizeBy) {
            case 'total_amount':
                return baseRadius + (node.total_amount || 0) / 1000000;
            case 'risk_score':
                return baseRadius + (node.risk_score || 0) * 20;
            default:
                return baseRadius + (node.transaction_count || 0) * 2;
        }
    }
    
    getNodeColor(riskScore) {
        if (riskScore >= 0.7) return '#dc3545'; // High risk - red
        if (riskScore >= 0.3) return '#ffc107'; // Medium risk - yellow
        return '#28a745'; // Low risk - green
    }
    
    getLinkColor(riskScore) {
        if (riskScore >= 0.7) return '#dc3545';
        if (riskScore >= 0.3) return '#ffc107';
        return '#17a2b8';
    }
    
    dragstarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
        
        // Ensure the node stays visible during drag
        d3.select(event.sourceEvent.target).raise();
    }

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
        
        // Force update the simulation to prevent visual glitches
        this.simulation.alpha(0.1).restart();
    }

    dragended(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        
        // Only release position if not pinned (you can implement pinning later)
        // For now, keep the node where it was dropped
        // d.fx = null;
        // d.fy = null;
        
        // Keep the node at the dropped position
        d.fx = event.x;
        d.fy = event.y;
    }    updateStats(data) {
        const stats = data.stats || {};
        
        const nodeCount = document.getElementById('node-count');
        const edgeCount = document.getElementById('edge-count');
        const transactionCount = document.getElementById('transaction-count');
        const highRiskCount = document.getElementById('high-risk-count');
        
        if (nodeCount) nodeCount.textContent = stats.nodes || 0;
        if (edgeCount) edgeCount.textContent = stats.edges || 0;
        if (transactionCount) transactionCount.textContent = stats.transactions || 0;
        if (highRiskCount) highRiskCount.textContent = stats.high_risk || 0;
    }
    
    showNodeDetails(node) {
        const panel = document.getElementById('node-details-panel');
        const content = document.getElementById('node-details-content');
        
        if (!panel || !content) return;
        
        // Populate panel with node details
        content.innerHTML = `
            <div class="node-info">
                <h6>Account Information</h6>
                <p><strong>ID:</strong> ${node.id}</p>
                <p><strong>Type:</strong> ${node.type || 'Account'}</p>
                <p><strong>Risk Level:</strong> ${node.risk_level || 'N/A'}</p>
                <p><strong>Risk Score:</strong> ${((node.avg_risk_score || 0) * 100).toFixed(1)}%</p>
                
                <h6 class="mt-3">Transaction Summary</h6>
                <p><strong>Transaction Count:</strong> ${node.transaction_count || 0}</p>
                <p><strong>Total Sent:</strong> $${(node.total_sent || 0).toLocaleString()}</p>
                <p><strong>Total Received:</strong> $${(node.total_received || 0).toLocaleString()}</p>
                
                <div class="mt-3">
                    <button class="btn btn-sm btn-primary" onclick="networkAnalysis.focusOnAccount('${node.id}')">
                        Focus on Account
                    </button>
                </div>
            </div>
        `;
        
        // Show panel
        panel.style.display = 'block';
    }
    
    showEdgeDetails(edge) {
        const panel = document.getElementById('edge-details-panel');
        const content = document.getElementById('edge-details-content');
        
        if (!panel || !content) return;
        
        // Populate panel with edge details
        content.innerHTML = `
            <div class="edge-info">
                <h6>Transaction Flow</h6>
                <p><strong>From:</strong> ${edge.source.id || edge.source}</p>
                <p><strong>To:</strong> ${edge.target.id || edge.target}</p>
                <p><strong>Amount:</strong> ${edge.currency || '$'} ${(edge.amount || 0).toLocaleString()}</p>
                <p><strong>Risk Score:</strong> ${((edge.risk_score || 0) * 100).toFixed(1)}%</p>
                <p><strong>Timestamp:</strong> ${edge.timestamp ? new Date(edge.timestamp).toLocaleDateString() : 'N/A'}</p>
            </div>
        `;
        
        // Show panel
        panel.style.display = 'block';
    }
    
    focusOnAccount(accountId) {
        // Set focus account filter
        const focusInput = document.getElementById('focus-account');
        if (focusInput) {
            focusInput.value = accountId;
            this.loadNetworkData();
        }
    }
    
    showEmptyState() {
        const container = document.getElementById('network-visualization');
        container.innerHTML = `
            <div class="empty-state text-center py-5">
                <i class="fas fa-project-diagram fa-3x text-muted mb-3"></i>
                <h5>No Network Data Available</h5>
                <p class="text-muted">Try adjusting your filters or uploading transaction data.</p>
            </div>
        `;
    }
    
    showError(message) {
        const container = document.getElementById('network-visualization');
        container.innerHTML = `
            <div class="error-state text-center py-5">
                <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                <h5>Error Loading Network</h5>
                <p class="text-muted">${message}</p>
                <button class="btn btn-primary" onclick="networkAnalysis.loadNetworkData()">
                    <i class="fas fa-sync"></i> Retry
                </button>
            </div>
        `;
    }
    
    applyFilters() {
        this.loadNetworkData();
    }
    
    restartSimulation() {
        if (this.simulation) {
            // Reset all fixed positions
            this.nodes.forEach(node => {
                node.fx = null;
                node.fy = null;
            });
            
            // Restart with higher alpha for better repositioning
            this.simulation
                .alpha(0.8)
                .alphaTarget(0)
                .restart();
        }
    }
    
    freezeSimulation() {
        if (this.simulation) {
            this.simulation.stop();
        }
    }
    
    resumeSimulation() {
        if (this.simulation) {
            this.simulation.restart();
        }
    }
    
    createD3Controls() {
        let toolbar = document.getElementById('d3-controls-toolbar');
        
        if (!toolbar) {
            // Create the toolbar if it doesn't exist
            toolbar = document.createElement('div');
            toolbar.id = 'd3-controls-toolbar';
            toolbar.className = 'd3-toolbar';
            toolbar.style.cssText = `
                position: absolute;
                top: 20px;
                left: 20px;
                z-index: 1000;
                background-color: white;
                border-radius: 4px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                padding: 8px;
                display: flex;
                gap: 5px;
                flex-direction: column;
            `;
            
            toolbar.innerHTML = `
                <div class="btn-group" role="group">
                    <button id="restart-simulation" class="btn btn-sm btn-outline-primary" title="Restart Layout">
                        <i class="fas fa-redo"></i>
                    </button>
                    <button id="freeze-simulation" class="btn btn-sm btn-outline-warning" title="Freeze/Resume">
                        <i class="fas fa-pause"></i>
                    </button>
                    <button id="center-view" class="btn btn-sm btn-outline-info" title="Center View">
                        <i class="fas fa-crosshairs"></i>
                    </button>
                </div>
                <div class="form-check form-switch mt-2">
                    <input class="form-check-input" type="checkbox" id="show-labels" checked>
                    <label class="form-check-label" for="show-labels" style="font-size: 12px;">
                        Labels
                    </label>
                </div>
            `;
            
            // Add to the D3 container
            const d3Container = document.getElementById('network-graph');
            if (d3Container) {
                d3Container.style.position = 'relative';
                d3Container.appendChild(toolbar);
            }
            
            // Add event listeners
            document.getElementById('restart-simulation').addEventListener('click', () => this.restartSimulation());
            document.getElementById('freeze-simulation').addEventListener('click', () => this.toggleSimulation());
            document.getElementById('center-view').addEventListener('click', () => this.centerView());
            document.getElementById('show-labels').addEventListener('change', (e) => this.toggleLabels(e.target.checked));
        }
        
        // Show the toolbar
        toolbar.style.display = 'flex';
    }
    
    toggleSimulation() {
        const btn = document.getElementById('freeze-simulation');
        const icon = btn.querySelector('i');
        
        if (this.simulation && this.simulation.alpha() > 0) {
            // Currently running, so freeze it
            this.freezeSimulation();
            icon.className = 'fas fa-play';
            btn.title = 'Resume';
        } else {
            // Currently frozen, so resume it
            this.resumeSimulation();
            icon.className = 'fas fa-pause';
            btn.title = 'Freeze';
        }
    }
    
    centerView() {
        if (!this.svg) return;
        
        // Reset zoom to identity
        const zoom = d3.zoom().scaleExtent([0.1, 4]);
        this.svg.transition()
            .duration(750)
            .call(zoom.transform, d3.zoomIdentity);
    }
    
    toggleLabels(show) {
        if (!this.svg) return;
        
        this.svg.selectAll('.node text')
            .style('display', show ? 'block' : 'none');
    }
    
    async analyzePatterns() {
        try {
            const response = await fetch('/api/network/patterns', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.getFilters())
            });
            
            const patterns = await response.json();
            this.showPatternResults(patterns);
            
        } catch (error) {
            console.error('Error analyzing patterns:', error);
        }
    }
    
   showPatternResults(patterns) {
    const modal = document.getElementById('pattern-modal');
    if (!modal) return;
    
    const results = patterns.results || [];
    const resultsList = results.map(pattern => `
        <div class="alert alert-${pattern.severity === 'high' ? 'danger' : 'warning'}">
            <h6>${pattern.type}</h6>
            <p>${pattern.description}</p>
            <small>Confidence: ${(pattern.confidence * 100).toFixed(1)}%</small>
        </div>
    `).join('');
    
    modal.querySelector('.modal-body').innerHTML = resultsList || '<p>No suspicious patterns detected.</p>';
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

    highlightTransaction(transactionId) {
        console.log('Highlighting transaction in network:', transactionId);
        
        // Check if visualization is ready
        if (!this.svg || !this.links || !Array.isArray(this.links)) {
            console.warn('Network visualization not ready yet, scheduling retry...');
            setTimeout(() => this.highlightTransaction(transactionId), 1000);
            return;
        }
        
        // Find and highlight related accounts/nodes
        this.svg.selectAll('.node')
            .style('stroke', (d) => {
                // Check if this node is related to the transaction
                const isRelated = this.links.some(link => 
                    (link.source && link.target && 
                     (link.source.id === d.id || link.target.id === d.id) && 
                     link.transaction_id === transactionId)
                );
                return isRelated ? '#ff6b35' : '#ddd';
            })
            .style('stroke-width', (d) => {
                const isRelated = this.links.some(link => 
                    (link.source && link.target && 
                     (link.source.id === d.id || link.target.id === d.id) && 
                     link.transaction_id === transactionId)
                );
                return isRelated ? 4 : 1;
            });
        
        // Highlight related links/edges
        this.svg.selectAll('.link')
            .style('stroke', (d) => d.transaction_id === transactionId ? '#ff6b35' : '#999')
            .style('stroke-width', (d) => d.transaction_id === transactionId ? 3 : 1)
            .style('opacity', (d) => d.transaction_id === transactionId ? 1 : 0.6);
        
        // Show info panel if transaction found
        const relatedLinks = this.links.filter(link => link.transaction_id === transactionId);
        if (relatedLinks.length > 0) {
            this.showTransactionInfo(transactionId, relatedLinks[0]);
        } else {
            console.warn(`Transaction ${transactionId} not found in current network data`);
        }
    }
    
    showTransactionInfo(transactionId, linkData) {
        const infoPanel = document.querySelector('.network-info') || this.createInfoPanel();
        infoPanel.innerHTML = `
            <div class="transaction-highlight">
                <h5><i class="fas fa-exclamation-triangle text-warning"></i> Transaction Highlighted</h5>
                <p><strong>Transaction ID:</strong> ${transactionId}</p>
                <p><strong>Amount:</strong> ${linkData.amount || 'N/A'}</p>
                <p><strong>From:</strong> ${linkData.source.id}</p>
                <p><strong>To:</strong> ${linkData.target.id}</p>
                <button class="btn btn-sm btn-primary mt-2" onclick="window.location.href='/cash-flow'">
                    <i class="fas fa-arrow-left"></i> Back to Cash Flow
                </button>
            </div>
        `;
        infoPanel.style.display = 'block';
    }
    
    showFlowDetails(link, sourceCountry, targetCountry) {
        // Create or get the info panel
        const infoPanel = document.querySelector('.flow-info-panel') || this.createFlowInfoPanel();
        
        // Get source and target IDs
        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' ? link.target.id : link.target;
        
        // Format amount with commas
        const formattedAmount = link.amount?.toLocaleString() || 'N/A';
        
        // Calculate risk level text
        let riskLevel = "Low";
        let riskClass = "success";
        if (link.risk_score > 0.7) {
            riskLevel = "High";
            riskClass = "danger";
        } else if (link.risk_score > 0.4) {
            riskLevel = "Medium";
            riskClass = "warning";
        }
        
        // Set the content
        infoPanel.innerHTML = `
            <div class="card border-${riskClass}">
                <div class="card-header bg-${riskClass} text-white d-flex justify-content-between align-items-center">
                    <h5 class="mb-0"><i class="fas fa-exchange-alt"></i> Transaction Flow Details</h5>
                    <button type="button" class="btn-close btn-close-white" aria-label="Close" 
                            onclick="networkAnalysis.resetFlowHighlight()"></button>
                </div>
                <div class="card-body">
                    <div class="alert alert-${riskClass} mb-3">
                        <strong>${sourceId} → ${targetId}</strong>
                        <div class="mt-1">${link.currency || '$'} ${formattedAmount} | Risk: ${(link.risk_score * 100).toFixed(1)}%</div>
                    </div>
                    
                    <h6 class="border-bottom pb-2 mb-3">Basic Information</h6>
                    <p><strong>From Account:</strong> ${sourceId}</p>
                    <p><strong>To Account:</strong> ${targetId}</p>
                    <p><strong>Amount:</strong> ${link.currency || '$'} ${formattedAmount}</p>
                    <p><strong>Transaction ID:</strong> ${link.transaction_id || 'N/A'}</p>
                    <p><strong>Timestamp:</strong> ${link.timestamp ? new Date(link.timestamp).toLocaleString() : 'N/A'}</p>
                    
                    <h6 class="border-bottom pb-2 mb-3 mt-4">Geographic Information</h6>
                    <p><strong>Source Country:</strong> ${sourceCountry}</p>
                    <p><strong>Source Bank Code:</strong> ${link.from_bank || 'N/A'}</p>
                    <p><strong>Target Country:</strong> ${targetCountry}</p>
                    <p><strong>Target Bank Code:</strong> ${link.to_bank || 'N/A'}</p>
                    
                    <h6 class="border-bottom pb-2 mb-3 mt-4">Risk Assessment</h6>
                    <p><strong>Risk Score:</strong> <span class="badge bg-${riskClass}">${(link.risk_score * 100).toFixed(1)}%</span></p>
                    <p><strong>Risk Level:</strong> ${riskLevel}</p>
                    <p><strong>Flags:</strong> ${link.flags?.join(', ') || 'None'}</p>
                    
                    <div class="d-flex justify-content-between mt-4">
                        <button class="btn btn-secondary" onclick="networkAnalysis.resetFlowHighlight()">
                            <i class="fas fa-undo"></i> Reset View
                        </button>
                        <button class="btn btn-${riskClass}" onclick="networkAnalysis.focusOnFlow('${sourceId}', '${targetId}')">
                            <i class="fas fa-search"></i> Focus on This Flow
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Show the panel
        infoPanel.style.display = 'block';
    }
    
    createFlowInfoPanel() {
        const panel = document.createElement('div');
        panel.className = 'flow-info-panel';
        panel.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            width: 400px;
            background: transparent;
            border-radius: 8px;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: none;
        `;
        document.body.appendChild(panel);
        return panel;
    }
    
    resetFlowHighlight() {
        // Hide the info panel
        const infoPanel = document.querySelector('.flow-info-panel');
        if (infoPanel) {
            infoPanel.style.display = 'none';
        }
        
        // Reset all lines to their original state based on risk
        this.mapLines.forEach(line => {
            const lineData = line.options._flowData;
            if (lineData) {
                // Reset to original style
                line.setStyle({
                    color: this.getRiskColor(lineData.risk_score),
                    weight: Math.max(3, Math.sqrt(lineData.amount / 100000)), // Original width
                    opacity: 0.8,
                    dashArray: '5, 10' // Original dash pattern
                });
            }
        });
        
        console.log("Map view reset to normal");
    }
    
    toggleSelectionMode() {
        this.selectionMode = !this.selectionMode;
        const selectBtn = document.getElementById('select-mode-toggle');
        
        if (this.selectionMode) {
            // Enable selection mode
            selectBtn.classList.remove('btn-outline-primary');
            selectBtn.classList.add('btn-primary');
            
            // Show cursor as pointer for all polylines
            this.worldMap._container.style.cursor = 'crosshair';
            
            // Add a hint to the user
            this.showToast('Selection mode enabled. Click on flows to select them.');
        } else {
            // Disable selection mode
            selectBtn.classList.remove('btn-primary');
            selectBtn.classList.add('btn-outline-primary');
            
            // Reset cursor
            this.worldMap._container.style.cursor = '';
            
            // Clear selection if needed
            if (this.selectedFlows.length > 0) {
                this.clearSelection();
            }
        }
        
        console.log(`Selection mode: ${this.selectionMode ? 'Enabled' : 'Disabled'}`);
    }
    
    toggleMultiSelect() {
        this.multiSelectEnabled = !this.multiSelectEnabled;
        const multiSelectBtn = document.getElementById('multi-select-toggle');
        
        if (this.multiSelectEnabled) {
            // Enable multi-select
            multiSelectBtn.classList.remove('btn-outline-secondary');
            multiSelectBtn.classList.add('btn-secondary');
            this.showToast('Multi-select enabled. Select multiple flows without clearing previous selections.');
        } else {
            // Disable multi-select
            multiSelectBtn.classList.remove('btn-secondary');
            multiSelectBtn.classList.add('btn-outline-secondary');
        }
        
        console.log(`Multi-select: ${this.multiSelectEnabled ? 'Enabled' : 'Disabled'}`);
    }
    
    clearSelection() {
        // Reset all selected flows
        this.selectedFlows.forEach(flow => {
            const lineData = flow.options._flowData;
            // Reset to normal style based on risk
            flow.setStyle({
                color: this.getRiskColor(lineData.risk_score),
                weight: Math.max(3, Math.sqrt(lineData.amount / 100000)),
                opacity: 0.8,
                dashArray: '5, 10'
            });
        });
        
        // Clear the array
        this.selectedFlows = [];
        
        // Update the count display
        const countBadge = document.getElementById('selection-count');
        if (countBadge) {
            countBadge.textContent = '0';
            countBadge.style.display = 'none';
        }
        
        console.log('Selection cleared');
    }
    
    showToast(message) {
        // Create a toast notification
        const toast = document.createElement('div');
        toast.className = 'map-toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background-color: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px 20px;
            border-radius: 4px;
            z-index: 1500;
            font-size: 14px;
        `;
        
        // Add to the map container
        const mapContainer = document.getElementById('network-world-map');
        if (mapContainer) {
            mapContainer.appendChild(toast);
            
            // Remove after 3 seconds
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 3000);
        }
    }
    
    focusOnFlow(sourceId, targetId) {
        // Highlight this specific flow on the map
        this.mapLines.forEach(line => {
            const lineData = line.options._flowData;
            if (lineData && lineData.source === sourceId && lineData.target === targetId) {
                // Highlight this line
                line.setStyle({
                    weight: 6,
                    color: '#ff6b35',
                    opacity: 1,
                    dashArray: null
                });
                // Bring the highlighted line to front
                line.bringToFront();
                // Log that we've highlighted a line
                console.log(`Highlighted flow: ${sourceId} → ${targetId}`);
            } else {
                // Fade other lines
                line.setStyle({
                    opacity: 0.3
                });
            }
        });
    }
    
    createInfoPanel() {
        const panel = document.createElement('div');
        panel.className = 'network-info';
        panel.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            width: 300px;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
        `;
        document.body.appendChild(panel);
        return panel;
    }

    initializeWorldMap() {
        // Check if the map container exists
        const mapContainer = document.getElementById('network-world-map');
        if (!mapContainer) {
            console.error('Map container element not found! Make sure the HTML has an element with id "network-world-map"');
            return;
        }
        
        try {
            // Initialize Leaflet world map
            console.log('Initializing world map...');
            this.worldMap = L.map('network-world-map', { 
                attributionControl: false,
                zoomControl: true
            }).setView([20, 0], 2);
            
            // Add dark tile layer
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                subdomains: 'abcd',
                maxZoom: 19,
                attribution: ''
            }).addTo(this.worldMap);
            
            console.log('World map initialized successfully for Network Analysis');
        } catch (error) {
            console.error('Error initializing world map:', error);
        }
    }
    
    toggleView(viewType) {
        const d3Container = document.getElementById('network-graph');
        const mapContainer = document.getElementById('network-world-map');
        const d3Btn = document.getElementById('toggle-d3-view');
        const mapBtn = document.getElementById('toggle-map-view');
        
        if (viewType === 'd3') {
            // Show D3 network
            d3Container.style.display = 'block';
            mapContainer.style.display = 'none';
            d3Btn.classList.add('active');
            d3Btn.classList.remove('btn-outline-primary');
            d3Btn.classList.add('btn-primary');
            mapBtn.classList.remove('active', 'btn-primary');
            mapBtn.classList.add('btn-outline-primary');
            this.currentView = 'd3';
            
            // Hide selection toolbar if visible
            const selectionToolbar = document.getElementById('map-selection-toolbar');
            if (selectionToolbar) selectionToolbar.style.display = 'none';
            
            // Create or show D3 controls
            this.createD3Controls();
            
        } else if (viewType === 'map') {
            // Show world map
            d3Container.style.display = 'none';
            mapContainer.style.display = 'block';
            mapBtn.classList.add('active');
            mapBtn.classList.remove('btn-outline-primary');
            mapBtn.classList.add('btn-primary');
            d3Btn.classList.remove('active', 'btn-primary');
            d3Btn.classList.add('btn-outline-primary');
            this.currentView = 'map';
            
            // Create or show the selection toolbar
            this.createSelectionToolbar();
            
            // Invalidate map size after showing and force update
            setTimeout(() => {
                if (this.worldMap) {
                    try {
                        console.log('Resizing world map...');
                        this.worldMap.invalidateSize();
                        console.log('Updating world map view with flows');
                        this.updateWorldMapView();
                    } catch (error) {
                        console.error('Error updating world map:', error);
                    }
                } else {
                    console.error('World map is not initialized!');
                    // Try to re-initialize the map if it's not available
                    this.initializeWorldMap();
                }
            }, 100);
        }
    }
    
    createSelectionToolbar() {
        let toolbar = document.getElementById('map-selection-toolbar');
        
        if (!toolbar) {
            // Create the toolbar if it doesn't exist
            toolbar = document.createElement('div');
            toolbar.id = 'map-selection-toolbar';
            toolbar.className = 'map-toolbar';
            toolbar.style.cssText = `
                position: absolute;
                top: 20px;
                left: 60px;
                z-index: 1000;
                background-color: white;
                border-radius: 4px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                padding: 8px;
                display: flex;
                gap: 5px;
            `;
            
            toolbar.innerHTML = `
                <button id="select-mode-toggle" class="btn btn-sm btn-outline-primary" title="Toggle Selection Mode">
                    <i class="fas fa-mouse-pointer"></i>
                </button>
                <button id="multi-select-toggle" class="btn btn-sm btn-outline-secondary" title="Multi-Select Mode (like Ctrl+Click)">
                    <i class="fas fa-object-group"></i>
                </button>
                <button id="clear-selection" class="btn btn-sm btn-outline-danger" title="Clear Selection">
                    <i class="fas fa-times"></i>
                </button>
                <span id="selection-count" class="badge bg-primary ms-2" style="align-self: center; display: none;">0</span>
            `;
            
            // Add to the map container
            const mapContainer = document.getElementById('network-world-map');
            if (mapContainer) {
                mapContainer.appendChild(toolbar);
            }
            
            // Add event listeners
            document.getElementById('select-mode-toggle').addEventListener('click', () => this.toggleSelectionMode());
            document.getElementById('multi-select-toggle').addEventListener('click', () => this.toggleMultiSelect());
            document.getElementById('clear-selection').addEventListener('click', () => this.clearSelection());
        }
        
        // Show the toolbar
        toolbar.style.display = 'flex';
    }
    
    updateWorldMapView() {
        if (!this.worldMap) {
            console.error('Cannot update world map view - map is not initialized');
            return;
        }
        
        if (this.currentView !== 'map') {
            console.log('Not in map view, skipping map update');
            return;
        }
        
        try {
            console.log('Starting world map update...');
            
            // Clear existing markers and lines
            this.clearMapMarkers();
            
            // Add account markers
            this.addAccountMarkers();
            
            // Add transaction flows
            this.addTransactionFlows();
            
            console.log('World map update completed');
        } catch (error) {
            console.error('Error updating world map view:', error);
        }
    }
    
    clearMapMarkers() {
        // Stop all animations
        if (this.activeAnimations) {
            this.activeAnimations.clear();
        }
        
        // Remove existing markers
        this.mapMarkers.forEach(marker => {
            this.worldMap.removeLayer(marker);
        });
        this.mapMarkers = [];
        
        // Remove existing lines
        this.mapLines.forEach(line => {
            this.worldMap.removeLayer(line);
        });
        this.mapLines = [];
        
        // Clear animated layer
        if (this.animatedLayer) {
            this.worldMap.removeLayer(this.animatedLayer);
            this.animatedLayer = null;
        }
    }
    
    // Shared method to fetch country coordinates - available to all methods
    async fetchCountryCoordinates(code) {
        if (!code || typeof code !== 'string' || code.trim().length !== 2) {
            console.warn(`Invalid country code: ${code}`);
            return null;
        }

        try {
            console.log(`Fetching coordinates for country code: ${code}`);
            const response = await fetch(`https://restcountries.com/v3.1/alpha/${code}`);
            if (!response.ok) {
                console.warn(`API error for code ${code}: ${response.status}`);
                return null;
            }
            
            const data = await response.json();
            
            if (Array.isArray(data) && data.length > 0 && data[0].latlng) {
                console.log(`Got coordinates for ${code}: ${data[0].latlng[0]}, ${data[0].latlng[1]}`);
                return {
                    lat: data[0].latlng[0],
                    lng: data[0].latlng[1],
                    name: data[0].name.common
                };
            } else {
                console.warn(`Invalid data structure for ${code}:`, data);
            }
        } catch (error) {
            console.error(`Error fetching country coordinates for ${code}:`, error);
        }
        return null;
    }

    async generateAccountLocations(nodes) {
        // Always generate fresh locations (no caching)
        console.log('Generating new node locations - cache disabled');
        
        // No longer using fallback locations - only real data from API
        
        // Try to extract country codes from node data and fetch real coordinates
        const locations = [];
        
        // First create a mapping of node IDs to their bank codes from the links data
        const nodeBankCodes = {};
        
        // Check links for bank codes
        this.links.forEach(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;
            
            if (link.from_bank && typeof link.from_bank === 'string' && link.from_bank.length === 2) {
                if (!nodeBankCodes[sourceId]) {
                    nodeBankCodes[sourceId] = link.from_bank;
                    console.log(`Found bank code for node ${sourceId} from links: ${link.from_bank}`);
                }
            }
            
            if (link.to_bank && typeof link.to_bank === 'string' && link.to_bank.length === 2) {
                if (!nodeBankCodes[targetId]) {
                    nodeBankCodes[targetId] = link.to_bank;
                    console.log(`Found bank code for node ${targetId} from links: ${link.to_bank}`);
                }
            }
        });
        
        for (let i = 0; i < nodes.length; i++) {
            const node = nodes[i];
            let location = null;
            
            console.log("Processing node:", node.id);
            
            // Try to get bank code from node data or from the links mapping
            // Look for bank codes in various properties
            const bankCode = node.from_bank || node.to_bank || 
                           node.bank_code || node.country_code ||
                           nodeBankCodes[node.id];
            
            if (bankCode && typeof bankCode === 'string' && bankCode.length === 2) {
                console.log(`Node ${node.id} has bank code: ${bankCode}`);
                
                // Always fetch fresh coordinates from API
                location = await this.fetchCountryCoordinates(bankCode);
                
                console.log(`Location for ${node.id} (${bankCode}):`, location);
            } else {
                console.log(`No valid bank code found for node ${node.id}`);
            }
            
            // No fallback locations - if we can't get real coordinates, we skip this node
            if (!location) {
                console.log(`No valid location for node ${node.id}, skipping...`);
                // Push null to maintain index alignment with nodes array
                locations.push(null);
                continue;
            }
            
            // Add a very small offset to prevent exact overlap for nodes in the same country
            // This will make nodes from the same country visible and clickable instead of stacking
            const latOffset = (Math.random() - 0.5) * 0.1; // Very small offset (±0.05 degrees)
            const lngOffset = (Math.random() - 0.5) * 0.1; // Very small offset (±0.05 degrees)
            
            const finalLocation = {
                name: location.name,
                lat: location.lat + latOffset,
                lng: location.lng + lngOffset
            };
            
            // Store in locations array
            locations.push(finalLocation);
            console.log(`Generated location for node ${node.id}: ${JSON.stringify(finalLocation)}`);
        }
        
        return locations;
    }

    async addAccountMarkers() {
        if (!this.nodes || this.nodes.length === 0) {
            console.log('No nodes to display on map');
            return;
        }
        
        console.log(`Adding ${this.nodes.length} account markers to map`);
        
        // Generate account locations if not already generated
        const locations = await this.generateAccountLocations(this.nodes);
        
        // Count valid locations
        const validLocations = locations.filter(loc => loc !== null).length;
        console.log(`Generated ${validLocations} valid locations out of ${this.nodes.length} nodes`);
        
        this.nodes.forEach((node, index) => {
            const location = locations[index];
            // Only create markers for nodes with valid locations from real country data
            if (location) {
                console.log(`Creating marker for node ${node.id} with location: ${location.name}`);
                // Determine marker color based on risk level
                let markerColor = '#28a745'; // Low risk - green
                if (node.avg_risk_score > 0.7) {
                    markerColor = '#dc3545'; // High risk - red
                } else if (node.avg_risk_score > 0.4) {
                    markerColor = '#ffc107'; // Medium risk - yellow
                }
                
                // Create custom marker
                const marker = L.circleMarker([location.lat, location.lng], {
                    radius: Math.max(8, Math.min(20, (node.transaction_count || 1) * 3)),
                    fillColor: markerColor,
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8,
                    _nodeData: node // Store node data for reference
                });
                
                // Add popup with account details
                marker.bindPopup(`
                    <div class="account-popup">
                        <h6>${location.name}</h6>
                        <p><strong>Account:</strong> ${node.id}</p>
                        <p><strong>Risk Score:</strong> ${((node.avg_risk_score || 0) * 100).toFixed(1)}%</p>
                        <p><strong>Transactions:</strong> ${node.transaction_count || 0}</p>
                        <p><strong>Total Sent:</strong> $${node.total_sent?.toLocaleString() || 'N/A'}</p>
                        <p><strong>Total Received:</strong> $${node.total_received?.toLocaleString() || 'N/A'}</p>
                        <button class="btn btn-sm btn-primary mt-2" id="view-node-${node.id}">View Details</button>
                    </div>
                `);
                
                // Add click handler for the marker
                marker.on('click', (e) => {
                    // The popup will show automatically
                    // Add event listener for the detail button after popup is opened
                    setTimeout(() => {
                        const detailButton = document.getElementById(`view-node-${node.id}`);
                        if (detailButton) {
                            detailButton.addEventListener('click', () => {
                                this.showNodeDetails(node);
                            });
                        }
                    }, 100);
                });
                
                marker.addTo(this.worldMap);
                this.mapMarkers.push(marker);
                console.log(`Added marker for ${node.id} at ${location.lat}, ${location.lng}`);
            }
        });
        
        console.log(`Total markers added: ${this.mapMarkers.length}`);
    }
    
    async addTransactionFlows() {
        if (!this.links || this.links.length === 0) {
            console.log('No links to display on map');
            return;
        }
        
        console.log(`Adding ${this.links.length} transaction flows to map`);
        
        // Get fresh coordinates for all nodes
        console.log("Generating fresh node coordinates for flows");
        const locations = await this.generateAccountLocations(this.nodes);
        
        // Create a map of node ID to location
        const locationMap = {};
        this.nodes.forEach((node, index) => {
            if (locations[index]) {
                locationMap[node.id] = locations[index];
            }
        });
        
        // Create a cache for bank country code to coordinates
        
        // Create animated layer for moving dots
        if (!this.animatedLayer) {
            this.animatedLayer = L.layerGroup().addTo(this.worldMap);
        }
        
        // Helper function for risk color
        const riskColor = (risk) => {
            if (risk > 0.7) return '#dc3545'; // High risk - red
            if (risk > 0.4) return '#ffc107'; // Medium risk - yellow
            return '#28a745'; // Low risk - green
        };
        
        // Store the function for later use
        this.getRiskColor = riskColor;
        
        // Helper function for linear interpolation along straight path
        const interpolatePath = (latlngs, t) => {
            if (t <= 0) return latlngs[0];
            if (t >= 1) return latlngs[latlngs.length - 1];
            
            // Simple linear interpolation between start and end points
            const start = latlngs[0];
            const end = latlngs[1];
            
            return [
                start[0] + (end[0] - start[0]) * t,
                start[1] + (end[1] - start[1]) * t
            ];
        };
        
        // Process each transaction flow
        console.log(`Processing ${this.links.length} transaction flows`);
        
        // Process each link sequentially to avoid race conditions with fetch calls
        for (let index = 0; index < this.links.length; index++) {
            const link = this.links[index];
            
            // Handle both string IDs and node objects
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;
            
            // Get bank country codes from link data
            const fromBankCode = link.from_bank;
            const toBankCode = link.to_bank;
            
            console.log(`Flow ${index + 1}: ${sourceId} → ${targetId}, Banks: ${fromBankCode || 'Unknown'} → ${toBankCode || 'Unknown'}`);
            
            // Fetch coordinates for banks using country codes if available
            let src = null;
            let tgt = null;
            
            // Try bank country codes first
            if (fromBankCode && fromBankCode.length === 2) {
                const location = await this.fetchCountryCoordinates(fromBankCode);
                if (location) {
                    src = {
                        lat: location.lat,
                        lng: location.lng,
                        name: location.name
                    };
                }
            }
            
            if (toBankCode && toBankCode.length === 2) {
                const location = await this.fetchCountryCoordinates(toBankCode);
                if (location) {
                    tgt = {
                        lat: location.lat,
                        lng: location.lng,
                        name: location.name
                    };
                }
            }
            
            // Check if we have valid locations for source and target
            if (!src && locationMap[sourceId]) src = locationMap[sourceId];
            if (!tgt && locationMap[targetId]) tgt = locationMap[targetId];
            
            // Log the flow details
            console.log(`Flow ${index + 1}: ${sourceId} → ${targetId}`, 
                        { src, tgt, bankCodes: `${fromBankCode || 'N/A'} → ${toBankCode || 'N/A'}` });
            
            // Skip this flow if either source or target location is missing
            if (!src || !tgt) {
                console.log(`Missing coordinates for flow ${sourceId} → ${targetId}, skipping...`);
                continue;
            }
            
            if (src && tgt) {
                // Create a completely straight path between points
                const latlngs = [
                    [src.lat, src.lng],
                    [tgt.lat, tgt.lng]
                ];
                
                // Create static polyline for the flow path
                const polyline = L.polyline(latlngs, {
                    color: riskColor(link.risk_score),
                    weight: Math.max(3, Math.sqrt(link.amount / 100000)), // More visible
                    opacity: 0.8,
                    dashArray: '5, 10', // Dashed line pattern for better visibility
                    _flowData: {  // Store flow data for reference
                        source: sourceId,
                        target: targetId,
                        amount: link.amount,
                        risk_score: link.risk_score
                    }
                }).addTo(this.worldMap);
                
                // Add tooltip with flow details including country names and bank codes
                const sourceCountry = src?.name || 'Unknown';
                const targetCountry = tgt?.name || 'Unknown';
                const fromBankCode = link.from_bank || 'N/A';
                const toBankCode = link.to_bank || 'N/A';
                
                polyline.bindTooltip(`
                    <b>Flow:</b> ${sourceId} → ${targetId}<br>
                    <b>Countries:</b> ${sourceCountry} → ${targetCountry}<br>
                    <b>Bank Codes:</b> ${fromBankCode} → ${toBankCode}<br>
                    <b>Amount:</b> $${(link.amount / 1000000).toFixed(1)}M<br>
                    <b>Risk:</b> ${(link.risk_score * 100).toFixed(0)}%
                `);
                
                // Add click handler to show detailed flow information and highlight the line
                polyline.on('click', () => {
                    // First highlight this specific flow
                    const clickSourceId = typeof link.source === 'object' ? link.source.id : link.source;
                    const clickTargetId = typeof link.target === 'object' ? link.target.id : link.target;
                    
                    console.log(`Flow clicked: ${clickSourceId} → ${clickTargetId}`);
                    
                    // First reset all lines to original state
                    this.mapLines.forEach(l => {
                        const riskScore = l.options._flowData?.risk_score || 0;
                        l.setStyle({
                            color: this.getRiskColor(riskScore),
                            weight: l === polyline ? 6 : Math.max(3, Math.sqrt(l.options._flowData?.amount / 100000) || 3),
                            opacity: l === polyline ? 1 : 0.5,
                            dashArray: l === polyline ? null : '5, 10'
                        });
                    });
                    
                    // Now highlight this one with more visual emphasis
                    polyline.setStyle({
                        weight: 7,
                        color: '#ff6b35', // Bright orange
                        opacity: 1,
                        dashArray: null
                    });
                    
                    // Bring the highlighted line to front
                    polyline.bringToFront();
                    
                    // Then show the details
                    this.showFlowDetails(link, sourceCountry, targetCountry);
                });
                
                // Make sure we store the link data with the polyline object
                polyline.options._flowData = {
                    source: sourceId,
                    target: targetId,
                    amount: link.amount,
                    risk_score: link.risk_score,
                    transaction_id: link.transaction_id
                };
                
                this.mapLines.push(polyline);
                
                // Create animated dots along the path
                const flowId = `flow_${sourceId}_${targetId}`;
                const points = [];
                const count = 5; // More dots for better visibility
                
                for (let i = 0; i < count; i++) {
                    const t = i / count; // Use full path
                    const dot = L.circleMarker(interpolatePath(latlngs, t), {
                        radius: 5, // Larger radius
                        color: '#ffcc00', // More visible yellow
                        fillColor: '#ffcc00',
                        fillOpacity: 1,
                        weight: 1.5 // Thicker border
                    }).addTo(this.animatedLayer);
                    
                    points.push({ 
                        dot, 
                        offset: t,
                        speed: 0.005 // Consistent speed
                    });
                }
                
                console.log(`Added ${count} animated dots for flow ${sourceId} → ${targetId}`);
                
                // Store animation reference for cleanup
                if (!this.activeAnimations) {
                    this.activeAnimations = new Map();
                }
                
                // Animation function for this flow
                const animateDots = () => {
                    if (this.currentView !== 'map' || !this.worldMap || !this.activeAnimations.has(flowId)) {
                        return; // Stop animation if view changed or flow removed
                    }
                    
                    points.forEach(p => {
                        p.offset += p.speed;
                        if (p.offset > 1) {
                            p.offset = 0; // Reset to start
                        }
                        
                        try {
                            const newPos = interpolatePath(latlngs, p.offset);
                            p.dot.setLatLng(newPos);
                        } catch (e) {
                            console.warn('Animation error:', e);
                        }
                    });
                    
                    requestAnimationFrame(animateDots);
                };
                
                // Store animation reference
                this.activeAnimations.set(flowId, { animateDots, points });
                
                // Start animation with a small delay to stagger flows
                setTimeout(() => {
                    if (this.currentView === 'map' && this.worldMap) {
                        animateDots();
                    }
                }, Math.random() * 1000);
            }
        }
    }

    updateLayout() {
        const layoutType = document.getElementById('layout-type')?.value || 'force';
        
        if (!this.simulation) return;
        
        this.simulation.stop();
        
        switch (layoutType) {
            case 'circular':
                this.applyCircularLayout();
                break;
            case 'hierarchical':
                this.applyHierarchicalLayout();
                break;
            default:
                this.applyForceLayout();
                break;
        }
        
        this.simulation.restart();
    }
    
    applyForceLayout() {
        this.simulation
            .force('link', d3.forceLink(this.links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(30));
    }
    
    applyCircularLayout() {
        const radius = Math.min(this.width, this.height) / 2 - 100;
        const angleStep = (2 * Math.PI) / this.nodes.length;
        
        this.nodes.forEach((node, i) => {
            node.fx = this.width / 2 + radius * Math.cos(i * angleStep);
            node.fy = this.height / 2 + radius * Math.sin(i * angleStep);
        });
        
        this.simulation
            .force('link', d3.forceLink(this.links).id(d => d.id).distance(50))
            .force('charge', null)
            .force('center', null)
            .force('collision', d3.forceCollide().radius(30));
    }
    
    applyHierarchicalLayout() {
        // Group nodes by risk level
        const highRisk = this.nodes.filter(n => n.avg_risk_score > 0.7);
        const mediumRisk = this.nodes.filter(n => n.avg_risk_score > 0.4 && n.avg_risk_score <= 0.7);
        const lowRisk = this.nodes.filter(n => n.avg_risk_score <= 0.4);
        
        const levels = [highRisk, mediumRisk, lowRisk];
        const levelHeight = this.height / 4;
        
        levels.forEach((level, levelIndex) => {
            const y = levelHeight * (levelIndex + 1);
            const xStep = this.width / (level.length + 1);
            
            level.forEach((node, nodeIndex) => {
                node.fx = xStep * (nodeIndex + 1);
                node.fy = y;
            });
        });
        
        this.simulation
            .force('link', d3.forceLink(this.links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-100))
            .force('center', null)
            .force('collision', d3.forceCollide().radius(30));
    }
    
    updateNodeSizes() {
        const metric = document.getElementById('node-size-metric')?.value || 'transaction_count';
        
        this.svg.selectAll('.node circle')
            .transition()
            .duration(500)
            .attr('r', d => this.getNodeRadius(d, metric));
    }
    
    getNodeRadius(node, metric) {
        let value;
        switch (metric) {
            case 'total_amount':
                value = (node.total_sent || 0) + (node.total_received || 0);
                return Math.max(8, Math.min(25, Math.sqrt(value / 10000)));
            case 'risk_score':
                value = node.avg_risk_score || 0;
                return Math.max(8, Math.min(25, value * 30));
            default: // transaction_count
                value = node.transaction_count || 1;
                return Math.max(8, Math.min(25, value * 3));
        }
    }
    
    updateEdgeWidths() {
        const metric = document.getElementById('edge-width-metric')?.value || 'total_amount';
        
        this.svg.selectAll('.link')
            .transition()
            .duration(500)
            .style('stroke-width', d => this.getEdgeWidth(d, metric));
    }
    
    getEdgeWidth(link, metric) {
        let value;
        switch (metric) {
            case 'transaction_count':
                value = 1; // Assume 1 transaction per link for now
                return Math.max(1, Math.min(8, value * 2));
            case 'risk_score':
                value = link.risk_score || 0;
                return Math.max(1, Math.min(8, value * 10));
            default: // total_amount
                value = link.amount || 0;
                return Math.max(1, Math.min(8, Math.sqrt(value / 50000)));
        }
    }

    exportNetwork() {
        const data = {
            nodes: this.nodes,
            links: this.links,
            filters: this.getFilters(),
            timestamp: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `network_analysis_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.networkAnalysis = new NetworkAnalysis();
});