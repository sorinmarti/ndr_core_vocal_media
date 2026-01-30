/**
 * Simple Test Module
 * Demonstrates the JavaScript Module UI Element system
 */
(function() {
    'use strict';

    window.SimpleTestModule = function(selector, options) {
        this.container = document.querySelector(selector);
        this.options = options;
        this.init();
    };

    window.SimpleTestModule.prototype.init = function() {
        // Create a simple card
        const card = document.createElement('div');
        card.style.cssText = `
            border: 3px solid ${this.options.color};
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-family: Arial, sans-serif;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        `;

        const title = document.createElement('h3');
        title.textContent = this.options.message;
        title.style.margin = '0 0 10px 0';

        const info = document.createElement('p');
        info.innerHTML = `
            <strong>✅ JS Module System Working!</strong><br>
            Module initialized successfully.<br>
            Container: <code>${this.container.id}</code><br>
            Media Path: <code>${this.options.mediaBasePath || 'N/A (CDN mode)'}</code>
        `;
        info.style.fontSize = '14px';
        info.style.margin = '0';

        const button = document.createElement('button');
        button.textContent = 'Test Interaction';
        button.style.cssText = `
            margin-top: 15px;
            padding: 8px 16px;
            background: white;
            color: #667eea;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        `;
        button.onclick = () => {
            alert('JS Module is interactive! 🎉');
        };

        card.appendChild(title);
        card.appendChild(info);
        card.appendChild(button);

        this.container.appendChild(card);

        console.log('[SimpleTestModule] Initialized with options:', this.options);
    };
})();
