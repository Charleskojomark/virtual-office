document.addEventListener('DOMContentLoaded', function() {
    // Initialize filter dropdowns with current values
    const currentFilters = window.currentFilters || {};
    
    // Set filter values if elements exist
    const searchInput = document.getElementById('search-input');
    const recordTypeFilter = document.getElementById('record-type-filter');
    const statusFilter = document.getElementById('status-filter');
    
    if (searchInput && currentFilters.search) {
        searchInput.value = currentFilters.search;
    }
    if (recordTypeFilter && currentFilters.record_type) {
        recordTypeFilter.value = currentFilters.record_type;
    }
    if (statusFilter && currentFilters.status) {
        statusFilter.value = currentFilters.status;
    }

    // Handle delete button clicks
    document.querySelectorAll('.delete-record-btn').forEach(button => {
        button.addEventListener('click', function() {
            if (confirm('Are you sure you want to delete this record?')) {
                const deleteUrl = this.getAttribute('data-delete-url');
                const originalText = this.textContent;
                
                // Show loading state
                this.textContent = 'Deleting...';
                this.disabled = true;

                // Get CSRF token
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
                const headers = {
                    'Content-Type': 'application/json',
                };
                
                if (csrfToken) {
                    headers['X-CSRFToken'] = csrfToken.value;
                }

                fetch(deleteUrl, {
                    method: 'POST',
                    headers: headers
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.status === 'success') {
                        // Remove the row from the table instead of reloading
                        const row = this.closest('tr');
                        if (row) {
                            row.remove();
                        } else {
                            location.reload();
                        }
                    } else {
                        throw new Error(data.message || 'Unknown error');
                    }
                })
                .catch(error => {
                    console.error('Delete error:', error);
                    alert('Failed to delete record: ' + error.message);
                })
                .finally(() => {
                    // Reset button state
                    this.textContent = originalText;
                    this.disabled = false;
                });
            }
        });
    });

    // Handle notification trigger
    const notificationTrigger = document.getElementById('notificationTrigger');
    if (notificationTrigger) {
        notificationTrigger.addEventListener('click', function() {
            console.log('Notifications clicked!');
            // TODO: Implement notification popup/modal
            // Example: showNotificationModal();
        });
    }

    // Search and filter functionality (server-side)
    function updateFilters() {
        if (!searchInput || !recordTypeFilter || !statusFilter) {
            console.warn('One or more filter elements not found');
            return;
        }

        const params = new URLSearchParams(window.location.search);
        
        // Set search parameter
        if (searchInput.value.trim()) {
            params.set('search', searchInput.value.trim());
        } else {
            params.delete('search');
        }
        
        // Set record type filter
        if (recordTypeFilter.value && recordTypeFilter.value !== 'all') {
            params.set('record_type', recordTypeFilter.value);
        } else {
            params.delete('record_type');
        }
        
        // Set status filter
        if (statusFilter.value && statusFilter.value !== 'all') {
            params.set('status', statusFilter.value);
        } else {
            params.delete('status');
        }
        
        // Update URL
        const newUrl = params.toString() ? `${window.location.pathname}?${params.toString()}` : window.location.pathname;
        window.location.href = newUrl;
    }

    // Add event listeners only if elements exist
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            // Debounce search to avoid excessive requests
            clearTimeout(this.debounceTimeout);
            this.debounceTimeout = setTimeout(updateFilters, 300);
        });
    }
    
    if (recordTypeFilter) {
        recordTypeFilter.addEventListener('change', updateFilters);
    }
    
    if (statusFilter) {
        statusFilter.addEventListener('change', updateFilters);
    }

    // Initialize filters from URL parameters on page load
    function initializeFiltersFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        
        if (searchInput) {
            searchInput.value = urlParams.get('search') || '';
        }
        if (recordTypeFilter) {
            recordTypeFilter.value = urlParams.get('record_type') || 'all';
        }
        if (statusFilter) {
            statusFilter.value = urlParams.get('status') || 'all';
        }
    }

    // Initialize filters if currentFilters is not available
    if (!window.currentFilters) {
        initializeFiltersFromUrl();
    }

    // Error handling for missing elements
    const requiredElements = ['search-input', 'record-type-filter', 'status-filter'];
    const missingElements = requiredElements.filter(id => !document.getElementById(id));
    
    if (missingElements.length > 0) {
        console.warn('Missing required elements:', missingElements);
    }
});