// records.js - Merged client-side and server-side filter functionality

document.addEventListener('DOMContentLoaded', function() {
    // Get filter elements
    const searchInput = document.getElementById('search-input');
    const recordTypeFilter = document.getElementById('record-type-filter');
    const statusFilter = document.getElementById('status-filter');
    const tableBody = document.getElementById('records-table-body');

    // Check for missing elements
    const requiredElements = ['search-input', 'record-type-filter', 'status-filter', 'records-table-body'];
    const missingElements = requiredElements.filter(id => !document.getElementById(id));
    if (missingElements.length > 0) {
        console.warn('Missing required elements:', missingElements);
        return;
    }

    // Store original table rows for client-side filtering
    const originalRows = Array.from(tableBody.querySelectorAll('.record-row'));

    // Initialize filters from URL parameters or currentFilters
    function initializeFilters() {
        const urlParams = new URLSearchParams(window.location.search);
        const currentFilters = window.currentFilters || {};

        searchInput.value = currentFilters.search || urlParams.get('search') || '';
        recordTypeFilter.value = currentFilters.record_type || urlParams.get('record-type-filter') || 'all';
        statusFilter.value = currentFilters.status || urlParams.get('status-filter') || 'all';

        // Apply client-side filters on initialization
        applyClientSideFilters();
    }

    // Function to apply client-side filters
    function applyClientSideFilters() {
        const searchTerm = searchInput.value.toLowerCase().trim();
        const selectedRecordType = recordTypeFilter.value;
        const selectedStatus = statusFilter.value;

        originalRows.forEach(row => {
            const name = row.cells[0].textContent.toLowerCase();
            const recordType = row.cells[1].textContent.trim();
            const status = row.cells[3].textContent.trim();

            const matchesSearch = !searchTerm || name.includes(searchTerm);
            const matchesRecordType = selectedRecordType === 'all' || recordType === getRecordTypeDisplayName(selectedRecordType);
            const matchesStatus = selectedStatus === 'all' || status === selectedStatus;

            row.style.display = matchesSearch && matchesRecordType && matchesStatus ? '' : 'none';
        });

        updateEmptyState();
    }

    // Function to get display name for record type
    function getRecordTypeDisplayName(value) {
        const typeMap = {
            'Image': 'Image',
            'Document': 'Document',
            'Video': 'Video',
            'Audio': 'Audio',
            'Other': 'Other'
        };
        return typeMap[value] || value;
    }

    // Function to update empty state
    function updateEmptyState() {
        const visibleRows = originalRows.filter(row => row.style.display !== 'none');
        const emptyRow = tableBody.querySelector('tr:not(.record-row)');

        if (visibleRows.length === 0 && originalRows.length > 0) {
            if (!emptyRow) {
                const noResultsRow = document.createElement('tr');
                noResultsRow.innerHTML = `
                    <td colspan="5" class="empty-state">
                        <div class="empty-icon">🔍</div>
                        <p>No records match your current filters.</p>
                        <button class="auth-btn" onclick="clearFilters()">Clear Filters</button>
                    </td>
                `;
                noResultsRow.classList.add('no-results-row');
                tableBody.appendChild(noResultsRow);
            }
        } else {
            const noResultsRow = tableBody.querySelector('.no-results-row');
            if (noResultsRow) {
                noResultsRow.remove();
            }
        }
    }

    // Function to clear all filters
    window.clearFilters = function() {
        searchInput.value = '';
        recordTypeFilter.value = 'all';
        statusFilter.value = 'all';
        applyClientSideFilters();
        updateServerSideFilters();
    };

    // Function to update server-side filters
    function updateServerSideFilters() {
        const params = new URLSearchParams(window.location.search);

        if (searchInput.value.trim()) {
            params.set('search', searchInput.value.trim());
        } else {
            params.delete('search');
        }

        if (recordTypeFilter.value && recordTypeFilter.value !== 'all') {
            params.set('record-type-filter', recordTypeFilter.value);
        } else {
            params.delete('record-type-filter');
        }

        if (statusFilter.value && statusFilter.value !== 'all') {
            params.set('status-filter', statusFilter.value);
        } else {
            params.delete('status-filter');
        }

        const newUrl = params.toString() ? `${window.location.pathname}?${params.toString()}` : window.location.pathname;
        window.location.href = newUrl;
    }

    // Add event listeners for filters
    let debounceTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
            applyClientSideFilters();
            updateServerSideFilters();
        }, 300);
    });

    recordTypeFilter.addEventListener('change', () => {
        applyClientSideFilters();
        updateServerSideFilters();
    });

    statusFilter.addEventListener('change', () => {
        applyClientSideFilters();
        updateServerSideFilters();
    });

    // Handle delete record functionality
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-record-btn')) {
            e.preventDefault();
            if (confirm('Are you sure you want to delete this record?')) {
                const recordId = e.target.dataset.recordId;
                const deleteUrl = e.target.dataset.deleteUrl;
                const row = e.target.closest('tr');
                const originalText = e.target.textContent;

                // Show loading state
                e.target.textContent = 'Deleting...';
                e.target.disabled = true;

                deleteRecord(recordId, deleteUrl, row, e.target, originalText);
            }
        }
    });

    // Function to delete record
    function deleteRecord(recordId, deleteUrl, row, button, originalText) {
        fetch(deleteUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Remove row from original rows array
                const index = originalRows.indexOf(row);
                if (index > -1) {
                    originalRows.splice(index, 1);
                }

                // Remove row from DOM
                row.remove();
                updateEmptyState();
                showNotification(data.message, 'success');
            } else {
                throw new Error(data.message || 'Unknown error');
            }
        })
        .catch(error => {
            console.error('Delete error:', error);
            showNotification(`Failed to delete record: ${error.message}`, 'error');
        })
        .finally(() => {
            // Reset button state
            button.textContent = originalText;
            button.disabled = false;
        });
    }

    // Function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Notification handling
    const notificationTrigger = document.getElementById('notificationTrigger');
    if (notificationTrigger) {
        notificationTrigger.addEventListener('click', () => {
            const modal = document.getElementById('notificationsModal');
            if (modal) {
                modal.style.display = 'flex';
            }
        });
        
        document.querySelectorAll('.notifications-tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tabId = btn.dataset.tab;
                document.querySelectorAll('.notifications-tabs .tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.notifications-content .tab-content').forEach(c => c.classList.remove('active'));
                btn.classList.add('active');
                document.getElementById(tabId).classList.add('active');
            });
        });
        
        document.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', async () => {
                const notificationId = item.dataset.notificationId;
                try {
                    const response = await fetch(`/messaging/notifications/mark-read/${notificationId}/`, {
                        method: 'POST',
                        headers: { 'X-CSRFToken': getCookie('csrftoken') }
                    });
                    
                    if (response.ok) {
                        item.remove();
                        const countElement = document.querySelector('.notification-badge');
                        if (countElement) {
                            const currentCount = parseInt(countElement.textContent) || 0;
                            countElement.textContent = Math.max(0, currentCount - 1);
                        }
                    }
                } catch (error) {
                    console.error('Error marking notification as read:', error);
                }
            });
        });
    }

    // Close modals when clicking outside
    window.addEventListener('click', (e) => {
        
        if (e.target.id === 'notificationsModal') {
            document.getElementById('notificationsModal').style.display = 'none';
        }
    });

    // Initialize filters
    initializeFilters();
});