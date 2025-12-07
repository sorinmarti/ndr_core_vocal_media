
function getUrlParameter(sParam, default_value) {
    // https://stackoverflow.com/questions/19491336/get-url-parameter-jquery-or-how-to-get-query-string-values-in-js
    let sPageURL = window.location.search.substring(1),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
        }
    }
    return default_value;
}

/**
 * Manages collapsible block state persistence using localStorage.
 * Saves and restores the expanded/collapsed state of blocks across page reloads.
 */
(function() {
    'use strict';

    const STORAGE_KEY_PREFIX = 'ndr_collapse_state_';

    /**
     * Save collapse state to localStorage
     */
    function saveCollapseState(collapseId, isExpanded) {
        try {
            localStorage.setItem(STORAGE_KEY_PREFIX + collapseId, isExpanded ? 'true' : 'false');
        } catch (e) {
            console.warn('Could not save collapse state:', e);
        }
    }

    /**
     * Get collapse state from localStorage
     */
    function getCollapseState(collapseId) {
        try {
            return localStorage.getItem(STORAGE_KEY_PREFIX + collapseId);
        } catch (e) {
            console.warn('Could not get collapse state:', e);
            return null;
        }
    }

    /**
     * Initialize collapsible blocks state management
     */
    function initCollapsibleBlocks() {
        // Find all collapsible elements
        const collapsibles = document.querySelectorAll('.collapse');

        collapsibles.forEach(function(collapse) {
            const collapseId = collapse.id;
            if (!collapseId) return;

            // Restore saved state on page load
            const savedState = getCollapseState(collapseId);
            if (savedState !== null) {
                if (savedState === 'true') {
                    // Should be expanded
                    collapse.classList.add('show');
                } else {
                    // Should be collapsed
                    collapse.classList.remove('show');
                }
            }

            // Listen for state changes and save them
            collapse.addEventListener('shown.bs.collapse', function() {
                saveCollapseState(collapseId, true);
            });

            collapse.addEventListener('hidden.bs.collapse', function() {
                saveCollapseState(collapseId, false);
            });
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCollapsibleBlocks);
    } else {
        // DOM already loaded
        initCollapsibleBlocks();
    }
})();