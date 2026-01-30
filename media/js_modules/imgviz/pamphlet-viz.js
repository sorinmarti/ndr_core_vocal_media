/**
 * Pamphlet Image Visualization Module
 * Interactive force-directed visualization of 17th-18th century song pamphlet images
 */
(function() {
    'use strict';

    window.PamphletViz = function(selector, options) {
        this.container = document.querySelector(selector);
        this.options = options;

        // Build full paths using mediaBasePath
        this.dataUrl = options.mediaBasePath + options.dataFile;
        this.imagePath = options.mediaBasePath + options.imagesFolder;
        this.databaseUrl = options.databaseUrl;

        // State
        this.data = [];
        this.filteredData = [];
        this.simulation = null;
        this.svg = null;
        this.g = null;
        this.currentViewMode = 'all';

        // Category definitions
        this.narrativeCategories = new Set(['scene_wide', 'scene_close']);
        this.decorativeCategories = new Set(['line_simple', 'line_ornamental',
                                             'ornament_geometric', 'ornament_figural', 'heraldry']);

        this.categoryInfo = {
            'line_simple': {name: 'Simple Lines', color: '#8B7355', group: 'decorative'},
            'line_ornamental': {name: 'Ornamental Lines', color: '#A0826D', group: 'decorative'},
            'ornament_geometric': {name: 'Geometric Patterns', color: '#6B8E23', group: 'decorative'},
            'ornament_figural': {name: 'Figural Ornaments', color: '#CD853F', group: 'decorative'},
            'heraldry': {name: 'Heraldry', color: '#8B4513', group: 'decorative'},
            'scene_wide': {name: 'Wide Scenes', color: '#4682B4', group: 'narrative'},
            'scene_close': {name: 'Close Scenes', color: '#5F9EA0', group: 'narrative'}
        };

        this.init();
    };

    window.PamphletViz.prototype.init = function() {
        console.log('[PamphletViz] Initializing with options:', this.options);

        // Create UI
        this.createUI();

        // Load data
        fetch(this.dataUrl)
            .then(response => response.json())
            .then(data => {
                this.data = data.filter(d => d.category === 'image' && d.visual_category);
                console.log('[PamphletViz] Loaded', this.data.length, 'images');
                this.initializeFilters();
                this.applyFilters();
            })
            .catch(error => {
                console.error('[PamphletViz] Failed to load data:', error);
                this.container.innerHTML = '<div class="alert alert-danger">Failed to load visualization data. Check console for details.</div>';
            });
    };

    window.PamphletViz.prototype.createUI = function() {
        this.container.innerHTML = `
            <div class="pamphlet-viz-wrapper">
                <div class="pv-controls">
                    <div class="pv-stats" id="pv-stats">Loading...</div>
                    <h3>Filters</h3>

                    <div class="pv-filter-group">
                        <label>View Mode</label>
                        <div class="pv-view-controls">
                            <button class="pv-view-btn active" data-mode="all">All</button>
                            <button class="pv-view-btn" data-mode="narrative">Narrative</button>
                            <button class="pv-view-btn" data-mode="decorative">Decorative</button>
                        </div>
                    </div>

                    <div class="pv-filter-group">
                        <label>Category</label>
                        <select id="pv-category-filter">
                            <option value="all">All Categories</option>
                            <optgroup label="Decorative">
                                <option value="line_simple">Simple Lines</option>
                                <option value="line_ornamental">Ornamental Lines</option>
                                <option value="ornament_geometric">Geometric Patterns</option>
                                <option value="ornament_figural">Figural Ornaments</option>
                                <option value="heraldry">Heraldry</option>
                            </optgroup>
                            <optgroup label="Narrative">
                                <option value="scene_wide">Wide Scenes</option>
                                <option value="scene_close">Close Scenes</option>
                            </optgroup>
                        </select>
                    </div>

                    <div class="pv-filter-group pv-year-filter">
                        <label>Year Range: <span id="pv-year-range-label">1500 - 1800</span></label>
                        <input type="range" id="pv-year-min" min="1500" max="1800" value="1500">
                        <input type="range" id="pv-year-max" min="1500" max="1800" value="1800">
                    </div>

                    <div class="pv-view-controls">
                        <button class="pv-view-btn" id="pv-reset-view">Reset View</button>
                    </div>
                </div>

                <div class="pv-legend">
                    <h3>Categories</h3>
                    <div id="pv-legend-items"></div>
                </div>

                <div class="pv-info-panel" id="pv-info-panel">
                    <button class="pv-info-close" id="pv-info-close">&times;</button>
                    <div class="pv-info-content" id="pv-info-content"></div>
                </div>

                <svg id="pv-visualization"></svg>
            </div>
        `;

        this.attachEventListeners();
        this.setupSVG();
    };

    window.PamphletViz.prototype.setupSVG = function() {
        const width = this.container.clientWidth || 1200;
        const height = Math.max(600, window.innerHeight - 100);

        this.svg = d3.select(this.container).select('#pv-visualization');
        this.svg.attr('width', width).attr('height', height);

        this.g = this.svg.append('g');

        const zoom = d3.zoom()
            .scaleExtent([0.3, 4])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });

        this.svg.call(zoom);
        this.zoomBehavior = zoom;
    };

    window.PamphletViz.prototype.attachEventListeners = function() {
        const self = this;

        // View mode buttons
        this.container.querySelectorAll('.pv-view-btn[data-mode]').forEach(btn => {
            btn.addEventListener('click', function() {
                self.setViewMode(this.dataset.mode);
                self.container.querySelectorAll('.pv-view-btn[data-mode]').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
            });
        });

        // Category filter
        this.container.querySelector('#pv-category-filter').addEventListener('change', () => this.applyFilters());

        // Year filters
        this.container.querySelector('#pv-year-min').addEventListener('change', () => this.applyFilters());
        this.container.querySelector('#pv-year-max').addEventListener('change', () => this.applyFilters());

        // Reset view
        this.container.querySelector('#pv-reset-view').addEventListener('click', () => this.resetView());

        // Info panel close
        this.container.querySelector('#pv-info-close').addEventListener('click', () => this.closeInfo());
    };

    window.PamphletViz.prototype.initializeFilters = function() {
        this.updateYearLabel();
        this.generateLegend();
    };

    window.PamphletViz.prototype.updateYearLabel = function() {
        const minYear = this.container.querySelector('#pv-year-min').value;
        const maxYear = this.container.querySelector('#pv-year-max').value;
        this.container.querySelector('#pv-year-range-label').textContent = `${minYear} - ${maxYear}`;
    };

    window.PamphletViz.prototype.generateLegend = function() {
        const legendItems = this.container.querySelector('#pv-legend-items');
        legendItems.innerHTML = '';

        const counts = {};
        this.data.forEach(d => {
            const cat = d.visual_category;
            counts[cat] = (counts[cat] || 0) + 1;
        });

        const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);

        sorted.forEach(([cat, count]) => {
            const info = this.categoryInfo[cat];
            if (!info) return;

            const item = document.createElement('div');
            item.className = 'pv-legend-item';
            item.innerHTML = `
                <div class="pv-legend-color" style="background: ${info.color}"></div>
                <span>${info.name}</span>
                <span class="pv-legend-count">${count}</span>
            `;
            legendItems.appendChild(item);
        });
    };

    window.PamphletViz.prototype.setViewMode = function(mode) {
        this.currentViewMode = mode;
        this.applyFilters();
    };

    window.PamphletViz.prototype.applyFilters = function() {
        this.updateYearLabel();

        const categoryFilter = this.container.querySelector('#pv-category-filter').value;
        const minYear = parseInt(this.container.querySelector('#pv-year-min').value);
        const maxYear = parseInt(this.container.querySelector('#pv-year-max').value);

        this.filteredData = this.data.filter(d => {
            if (this.currentViewMode === 'narrative' && !this.narrativeCategories.has(d.visual_category)) {
                return false;
            }
            if (this.currentViewMode === 'decorative' && !this.decorativeCategories.has(d.visual_category)) {
                return false;
            }

            if (categoryFilter !== 'all' && d.visual_category !== categoryFilter) {
                return false;
            }

            const year = parseInt(d.year);
            if (year && (year < minYear || year > maxYear)) {
                return false;
            }

            return true;
        });

        this.updateVisualization();
        this.updateStats();
    };

    window.PamphletViz.prototype.updateStats = function() {
        const narrative = this.filteredData.filter(d => this.narrativeCategories.has(d.visual_category)).length;
        const decorative = this.filteredData.filter(d => this.decorativeCategories.has(d.visual_category)).length;
        this.container.querySelector('#pv-stats').textContent =
            `Showing ${this.filteredData.length} images | Narrative: ${narrative} | Decorative: ${decorative}`;
    };

    window.PamphletViz.prototype.updateVisualization = function() {
        const self = this;

        this.g.selectAll('*').remove();

        const width = parseInt(this.svg.attr('width'));
        const height = parseInt(this.svg.attr('height'));

        const nodes = this.filteredData.map(d => {
            const isNarrative = this.narrativeCategories.has(d.visual_category);
            return {
                ...d,
                id: d.filename,
                isNarrative: isNarrative,
                size: isNarrative ? 40 : 25,
                previewPath: this.imagePath + d.filename.replace(/\.(tif|tiff)$/i, '.jpg')
            };
        });

        const categoryGroups = {};
        Object.keys(this.categoryInfo).forEach((cat, i) => {
            const angle = (i / Object.keys(this.categoryInfo).length) * 2 * Math.PI;
            const radius = 300;
            categoryGroups[cat] = {
                x: width / 2 + Math.cos(angle) * radius,
                y: height / 2 + Math.sin(angle) * radius
            };
        });

        this.simulation = d3.forceSimulation(nodes)
            .force('charge', d3.forceManyBody().strength(-30))
            .force('collision', d3.forceCollide().radius(d => d.size + 2))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('category', d3.forceX(d => categoryGroups[d.visual_category]?.x || width / 2).strength(0.1))
            .force('category-y', d3.forceY(d => categoryGroups[d.visual_category]?.y || height / 2).strength(0.1))
            .on('tick', ticked);

        const nodeElements = this.g.selectAll('.pv-image-node')
            .data(nodes, d => d.id)
            .join('g')
            .attr('class', d => `pv-image-node ${d.isNarrative ? 'pv-narrative' : 'pv-decorative'}`)
            .on('click', function(event, d) { self.showInfo(d); })
            .call(d3.drag()
                .on('start', dragStarted)
                .on('drag', dragged)
                .on('end', dragEnded));

        nodeElements.append('circle')
            .attr('r', d => d.size)
            .attr('fill', d => self.categoryInfo[d.visual_category]?.color || '#999')
            .attr('opacity', 0.9);

        const defs = this.svg.append('defs');
        nodeElements.each(function(d) {
            const clipId = `clip-${d.id.replace(/[^a-zA-Z0-9]/g, '_')}`;
            defs.append('clipPath')
                .attr('id', clipId)
                .append('circle')
                .attr('r', d.size - 2);

            d3.select(this).append('image')
                .attr('xlink:href', d.previewPath)
                .attr('x', -d.size + 2)
                .attr('y', -d.size + 2)
                .attr('width', (d.size - 2) * 2)
                .attr('height', (d.size - 2) * 2)
                .attr('clip-path', `url(#${clipId})`)
                .attr('preserveAspectRatio', 'xMidYMid slice');
        });

        function ticked() {
            nodeElements.attr('transform', d => `translate(${d.x},${d.y})`);
        }

        function dragStarted(event, d) {
            if (!event.active) self.simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragEnded(event, d) {
            if (!event.active) self.simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
    };

    window.PamphletViz.prototype.showInfo = function(d) {
        const panel = this.container.querySelector('#pv-info-panel');
        const content = this.container.querySelector('#pv-info-content');

        const catInfo = this.categoryInfo[d.visual_category];
        const categoryBadge = `<span class="pv-category-badge" style="background: ${catInfo.color}">${catInfo.name}</span>`;
        const sourceUrl = `${this.databaseUrl}?id=tk_${d.doc_id}`;

        content.innerHTML = `
            <div class="pv-info-image">
                <img src="${d.previewPath}" alt="${d.filename}">
            </div>

            <div class="pv-info-title">
                ${d.title || 'No title available'}
            </div>

            <a href="${sourceUrl}" target="_blank" class="pv-source-link-btn">
                View Source Document →
            </a>

            <div class="pv-info-metadata">
                <h3>Metadata</h3>
                <div class="pv-info-row">
                    <span class="pv-info-label">Category:</span>
                    <span class="pv-info-value">${categoryBadge}</span>
                </div>
                <div class="pv-info-row">
                    <span class="pv-info-label">Year:</span>
                    <span class="pv-info-value">${d.year || 'Unknown'}</span>
                </div>
                <div class="pv-info-row">
                    <span class="pv-info-label">Location:</span>
                    <span class="pv-info-value">${d.location || 'Unknown'}</span>
                </div>
                <div class="pv-info-row">
                    <span class="pv-info-label">Institution:</span>
                    <span class="pv-info-value">${d.institution || 'Unknown'}</span>
                </div>
                <div class="pv-info-row">
                    <span class="pv-info-label">Document ID:</span>
                    <span class="pv-info-value">${d.doc_id}</span>
                </div>
                <div class="pv-info-row">
                    <span class="pv-info-label">Page:</span>
                    <span class="pv-info-value">${d.page_number}</span>
                </div>
            </div>
        `;

        panel.classList.add('active');
    };

    window.PamphletViz.prototype.closeInfo = function() {
        this.container.querySelector('#pv-info-panel').classList.remove('active');
    };

    window.PamphletViz.prototype.resetView = function() {
        this.svg.transition().duration(750).call(
            this.zoomBehavior.transform,
            d3.zoomIdentity
        );
    };
})();
