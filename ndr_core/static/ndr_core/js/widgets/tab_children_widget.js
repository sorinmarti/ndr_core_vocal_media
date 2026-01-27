/**
 * JavaScript for TabChildrenWidget
 * Handles add/remove rows and serialization to JSON
 */

(function() {
    'use strict';

    function initTabChildrenWidget() {
        const widgets = document.querySelectorAll('.tab-children-widget');

        widgets.forEach(widget => {
            const inputId = widget.getAttribute('data-input-id');
            const hiddenInput = document.getElementById(inputId);
            const tbody = widget.querySelector('.tab-rows');
            const addButton = widget.querySelector('.add-tab-row');

            // Function to update row numbers
            function updateRowNumbers() {
                const rows = tbody.querySelectorAll('.tab-row');
                rows.forEach((row, idx) => {
                    row.querySelector('td:first-child').textContent = idx + 1;
                });
            }

            // Function to serialize current state to JSON
            function serializeToJSON() {
                const rows = tbody.querySelectorAll('.tab-row');
                const tabs = [];

                rows.forEach(row => {
                    const tabLabel = row.querySelector('.tab-label').value.trim();
                    const resultFieldId = row.querySelector('.result-field-select').value;
                    const tabOrder = parseInt(row.querySelector('.tab-order').value) || 1;

                    // Only add if both label and field are set
                    if (tabLabel && resultFieldId) {
                        tabs.push({
                            tab_label: tabLabel,
                            result_field_id: parseInt(resultFieldId),
                            tab_order: tabOrder
                        });
                    }
                });

                hiddenInput.value = JSON.stringify(tabs);
            }

            // Function to create a new row
            function createNewRow() {
                const rowCount = tbody.querySelectorAll('.tab-row').length;
                const newRow = document.createElement('tr');
                newRow.className = 'tab-row';
                newRow.innerHTML = `
                    <td class="text-center">${rowCount + 1}</td>
                    <td><input type="text" class="form-control form-control-sm tab-label" placeholder="Tab Label"></td>
                    <td><select class="form-control form-control-sm result-field-select">
                        ${getResultFieldOptions()}
                    </select></td>
                    <td><input type="number" class="form-control form-control-sm tab-order" value="${rowCount + 1}" min="1"></td>
                    <td class="text-center">
                        <button type="button" class="btn btn-sm btn-danger remove-tab-row">
                            <i class="fa-regular fa-trash"></i>
                        </button>
                    </td>
                `;

                // Attach event listeners to new row
                attachRowEventListeners(newRow);
                return newRow;
            }

            // Function to get result field options from existing select
            function getResultFieldOptions() {
                const firstSelect = tbody.querySelector('.result-field-select');
                if (firstSelect) {
                    return firstSelect.innerHTML;
                }
                return '<option value="">-- Select Result Field --</option>';
            }

            // Attach event listeners to a row
            function attachRowEventListeners(row) {
                // Remove button
                const removeBtn = row.querySelector('.remove-tab-row');
                removeBtn.addEventListener('click', function() {
                    row.remove();
                    updateRowNumbers();
                    serializeToJSON();
                });

                // Input changes
                const inputs = row.querySelectorAll('input, select');
                inputs.forEach(input => {
                    input.addEventListener('change', serializeToJSON);
                    input.addEventListener('input', serializeToJSON);
                });
            }

            // Add button click
            addButton.addEventListener('click', function() {
                const newRow = createNewRow();
                tbody.appendChild(newRow);
                updateRowNumbers();
                serializeToJSON();
            });

            // Attach listeners to existing rows
            const existingRows = tbody.querySelectorAll('.tab-row');
            existingRows.forEach(attachRowEventListeners);

            // Serialize on form submit to ensure data is saved
            const form = widget.closest('form');
            if (form) {
                form.addEventListener('submit', function() {
                    serializeToJSON();
                });
            }
        });
    }

    // Initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTabChildrenWidget);
    } else {
        initTabChildrenWidget();
    }
})();
