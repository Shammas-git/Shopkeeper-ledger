/**
 * Initialize Bootstrap popovers
 * 
 * Interacts with:
 * - Elements with [data-bs-toggle="popover"] attribute (e.g., balance button in base.html line 136)
 * - Used for the balance details popover and potentially other popovers throughout the site
 */
function setupPopovers() {
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    if (popoverTriggerList.length > 0) {
        popoverTriggerList.forEach(function(popoverTriggerEl) {
            new bootstrap.Popover(popoverTriggerEl, {
                trigger: 'click',
                container: 'body',
                html: true
            });
        });
        
        // Close popovers when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('[data-bs-toggle="popover"]') && 
                !e.target.closest('.popover')) {
                popoverTriggerList.forEach(function(popoverEl) {
                    const popover = bootstrap.Popover.getInstance(popoverEl);
                    if (popover) {
                        popover.hide();
                    }
                });
            }
        });
    }
}

/**
 * Setup scrollable tables with dynamic height
 * 
 * Interacts with:
 * - Elements with .table-responsive-scroll class (used in customers.html line 54, customer_detail.html line 135)
 * - Affects all table containers that need vertical scrolling when content overflows
 * - Calculates appropriate height based on viewport size for optimal mobile and desktop viewing
 */
function setupScrollableTables() {
    // Find all scrollable tables
    const scrollableTables = document.querySelectorAll('.table-responsive-scroll');
    
    if (scrollableTables.length === 0) return;
    
    // Function to adjust table heights
    function adjustTableHeights() {
        scrollableTables.forEach(tableContainer => {
            // Get the available viewport height
            const viewportHeight = window.innerHeight;
            // Calculate appropriate max height for tables based on viewport
            // Smaller screens get a higher percentage to use more available space
            const percentage = window.innerWidth < 768 ? 0.5 : 0.6;
            const maxHeight = Math.min(viewportHeight * percentage, 500);
            tableContainer.style.maxHeight = `${maxHeight}px`;
        });
    }
    
    // Set initial heights
    adjustTableHeights();
    
    // Add window resize event listener
    window.addEventListener('resize', function() {
        adjustTableHeights();
    });
}

/**
 * Main document ready event handler
 * Initializes all interactive components when the page loads
 */
document.addEventListener('DOMContentLoaded', function() {
    /**
     * Apply number input validation for transaction amount
     * 
     * Interacts with:
     * - input[name="amount"] fields in add_transaction.html and add_transaction_global.html forms
     * - Ensures only valid decimal numbers can be entered for transaction amounts
     */
    const amountInput = document.querySelector('input[name="amount"]');
    if (amountInput) {
        amountInput.addEventListener('input', function(e) {
            // Allow only numbers and decimal point
            this.value = this.value.replace(/[^0-9.]/g, '');
            
            // Ensure only one decimal point
            const parts = this.value.split('.');
            if (parts.length > 2) {
                this.value = parts[0] + '.' + parts.slice(1).join('');
            }
        });
    }

    // Initialize Bootstrap popovers
    setupPopovers();
    
    // Initialize scrollable tables
    setupScrollableTables();

    /**
     * Auto-hide alerts after 5 seconds
     * 
     * Interacts with:
     * - .alert elements (Flash messages in base.html line 187)
     * - Automatically dismisses notification alerts after they've been shown for 5 seconds
     */
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert.parentNode) { // Check if the alert is still in the DOM
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });

    /**
     * Setup auto-save for customer forms if present
     * 
     * Interacts with:
     * - Form with .customer-autosave-form class in customer_detail.html (line 27)
     * - Only initializes the auto-save functionality when a customer edit form is present
     */
    const customerForm = document.querySelector('.customer-autosave-form');
    if (customerForm) {
        setupCustomerAutoSave();
    }
    
    /**
     * Enhanced dropdown behavior with manual positioning
     * 
     * Interacts with:
     * - .dropdown elements throughout the site (e.g., Account dropdown in base.html line 34)
     * - Improves dropdown behavior for better mobile UX by overriding default Bootstrap positioning
     */
    document.querySelectorAll('.dropdown').forEach(dropdownElement => {
        const button = dropdownElement.querySelector('.dropdown-toggle');
        const menu = dropdownElement.querySelector('.dropdown-menu');
        
        if (!button || !menu) return;
        
        // Create a proper Bootstrap dropdown
        const dropdown = new bootstrap.Dropdown(button, {
            // Bootstrap's options
            reference: 'toggle',
            offset: [0, 2],
            autoClose: true,
            popperConfig: {
                strategy: 'fixed',
                placement: 'bottom-start',
                modifiers: [
                    {
                        name: 'preventOverflow',
                        options: {
                            boundary: 'viewport'
                        }
                    }
                ]
            }
        });
        
        // Override Bootstrap positioning when dropdown is shown
        button.addEventListener('shown.bs.dropdown', () => {
            // Get button position
            const buttonRect = button.getBoundingClientRect();
            
            // Position menu directly below button
            if (menu.classList.contains('dropdown-menu-end')) {
                // Right-aligned for account dropdown
                menu.style.left = 'auto';
                menu.style.right = '0';
            } else {
                // Left-aligned for normal dropdowns
                menu.style.left = '0';
                menu.style.right = 'auto';
            }
            
            // Set top position just below the button
            menu.style.top = '100%';
            
            // Remove any transform that might displace the menu
            menu.style.transform = 'none !important';
        });
    });
    
    /**
     * Prevent dropdowns from closing when clicking form elements
     * 
     * Interacts with:
     * - Forms inside .dropdown-menu elements (e.g., forms in account-related dropdowns)
     * - Prevents the dropdown from closing when clicking on form elements inside it
     */
    document.querySelectorAll('.dropdown-menu form').forEach(form => {
        form.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    });
    
    /**
     * Handle user account switching
     * 
     * Interacts with:
     * - Buttons with .user-switch-btn class in switch_user.html
     * - Handles the form submission for switching between user accounts
     */
    document.querySelectorAll('.user-switch-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const form = btn.closest('form');
            if (form) form.submit();
        });
    });
});

/**
 * Auto-save functionality for customer forms
 * 
 * Interacts with:
 * - Form with .customer-autosave-form class in customer_detail.html (line 27)
 * - Input fields with .autosave-field class (customer_detail.html lines 36, 49, 62, 75)
 * - Creates and manages #autosave-indicator toast for showing save status
 * - Automatically saves form changes as the user types with 500ms debounce
 */
function setupCustomerAutoSave() {
    const customerForm = document.querySelector('.customer-autosave-form');
    if (!customerForm) return;
    
    // Create save indicator
    const savingIndicator = document.createElement('div');
    savingIndicator.id = 'autosave-indicator';
    savingIndicator.className = 'position-fixed bottom-0 end-0 p-3';
    savingIndicator.style.display = 'none';
    savingIndicator.innerHTML = `
        <div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-primary text-white">
                <strong class="me-auto">Auto-saving</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                Saving changes...
            </div>
        </div>
    `;
    document.body.appendChild(savingIndicator);
    
    // Add input event listeners to all form fields with autosave-field class
    const autoSaveFields = customerForm.querySelectorAll('.autosave-field');
    let saveTimeout = null;
    
    autoSaveFields.forEach(field => {
        field.addEventListener('input', function() {
            // Clear previous timeout to prevent multiple saves
            if (saveTimeout) {
                clearTimeout(saveTimeout);
            }
            
            // Show saving indicator
            const toast = new bootstrap.Toast(document.querySelector('#autosave-indicator .toast'));
            toast.show();
            
            // Set timeout for saving (500ms after user stops typing)
            saveTimeout = setTimeout(function() {
                // Get form data
                const formData = new FormData(customerForm);
                
                // Submit form data
                fetch(customerForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    // Update toast to show success
                    document.querySelector('#autosave-indicator .toast-header').classList.remove('bg-primary');
                    document.querySelector('#autosave-indicator .toast-header').classList.add('bg-success');
                    document.querySelector('#autosave-indicator .toast-header strong').textContent = 'Saved';
                    document.querySelector('#autosave-indicator .toast-body').textContent = 'Changes saved successfully';
                    
                    // Hide toast after 1 second
                    setTimeout(() => {
                        toast.hide();
                        // Reset toast styling
                        document.querySelector('#autosave-indicator .toast-header').classList.remove('bg-success');
                        document.querySelector('#autosave-indicator .toast-header').classList.add('bg-primary');
                        document.querySelector('#autosave-indicator .toast-header strong').textContent = 'Auto-saving';
                        document.querySelector('#autosave-indicator .toast-body').textContent = 'Saving changes...';
                    }, 1000);
                })
                .catch(error => {
                    console.error('Error saving:', error);
                    // Update toast to show error
                    document.querySelector('#autosave-indicator .toast-header').classList.remove('bg-primary');
                    document.querySelector('#autosave-indicator .toast-header').classList.add('bg-danger');
                    document.querySelector('#autosave-indicator .toast-header strong').textContent = 'Error';
                    document.querySelector('#autosave-indicator .toast-body').textContent = 'Failed to save changes';
                });
            }, 500);
        });
    });
}