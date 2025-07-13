const hamburger = document.getElementById('hamburger');
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');
const mainContent = document.getElementById('mainContent');
const darkModeBtn = document.querySelector('.dark-mode-btn');
// Notification functionality
// Notification System
// function initializeNotifications() {
    
//     if (!notificationTrigger || !notificationsModal) return;

//     // Toggle modal
//     notificationTrigger.addEventListener('click', () => {
//         notificationsModal.style.display = 'flex';
//         document.body.style.overflow = 'hidden';
//         updateNotificationBadge(0);
//     });

//     // Close modal
//     notificationsModal.addEventListener('click', (e) => {
//         if (e.target === notificationsModal || e.target.classList.contains('notifications-close')) {
//             notificationsModal.style.display = 'none';
//             document.body.style.overflow = '';
//         }
//     });

//     // Tab switching
//     document.querySelectorAll('.notifications-tab').forEach(tab => {
//         tab.addEventListener('click', () => {
//             const tabId = tab.dataset.tab;
            
//             // Update active tab
//             document.querySelectorAll('.notifications-tab').forEach(t => 
//                 t.classList.remove('active'));
//             tab.classList.add('active');
            
//             // Update active content
//             document.querySelectorAll('.notifications-tab-content').forEach(content => 
//                 content.classList.remove('active'));
//             document.getElementById(tabId).classList.add('active');
//         });
//     });

//     // Mark notification as read when clicked
//     document.querySelectorAll('.notification-item').forEach(item => {
//         item.addEventListener('click', async () => {
//             const notificationId = item.dataset.id;
            
//             try {
//                 const response = await fetch(`/notifications/mark-read/${notificationId}/`, {
//                     method: 'POST',
//                     headers: {
//                         'X-CSRFToken': getCookie('csrftoken'),
//                         'Content-Type': 'application/json'
//                     }
//                 });
                
//                 if (response.ok) {
//                     item.remove();
//                     const currentCount = parseInt(document.querySelector('.notification-badge').textContent) || 0;
//                     updateNotificationBadge(Math.max(0, currentCount - 1));
                    
//                     // Check if tab is now empty
//                     const tabContent = item.closest('.notifications-tab-content');
//                     if (tabContent.querySelectorAll('.notification-item').length === 0) {
//                         tabContent.innerHTML = `
//                             <div class="notifications-empty">
//                                 No notifications found
//                             </div>
//                         `;
//                     }
//                 }
//             } catch (error) {
//                 console.error('Error marking notification as read:', error);
//                 showToast('Failed to mark notification as read', 'error');
//             }
//         });
//     });

//     // Clear all notifications
//     document.getElementById('clearNotifications').addEventListener('click', async () => {
//         try {
//             const response = await fetch('/notifications/clear-all/', {
//                 method: 'POST',
//                 headers: {
//                     'X-CSRFToken': getCookie('csrftoken'),
//                     'Content-Type': 'application/json'
//                 }
//             });
            
//             if (response.ok) {
//                 document.querySelectorAll('.notifications-tab-content').forEach(content => {
//                     content.innerHTML = `
//                         <div class="notifications-empty">
//                             No notifications found
//                         </div>
//                     `;
//                 });
//                 updateNotificationBadge(0);
//                 showToast('All notifications cleared', 'success');
//             }
//         } catch (error) {
//             console.error('Error clearing notifications:', error);
//             showToast('Failed to clear notifications', 'error');
//         }
//     });

//     // Mark all as read
//     document.getElementById('markAllAsRead').addEventListener('click', async () => {
//         try {
//             const response = await fetch('/notifications/mark-all-read/', {
//                 method: 'POST',
//                 headers: {
//                     'X-CSRFToken': getCookie('csrftoken'),
//                     'Content-Type': 'application/json'
//                 }
//             });
            
//             if (response.ok) {
//                 updateNotificationBadge(0);
//                 showToast('All notifications marked as read', 'success');
//                 notificationsModal.style.display = 'none';
//                 document.body.style.overflow = '';
//             }
//         } catch (error) {
//             console.error('Error marking notifications as read:', error);
//             showToast('Failed to mark notifications as read', 'error');
//         }
//     });
// }

// // Update notification badge count
// function updateNotificationBadge(count) {
//     const badge = document.querySelector('.notification-badge');
//     if (!badge) return;
    
//     badge.textContent = count;
//     badge.style.display = count > 0 ? 'block' : 'none';
// }

// WebSocket for real-time notifications
function initializeNotificationWebSocket() {
    const wsScheme = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = `${wsScheme}${window.location.host}/ws/notifications/`;
    
    const socket = new WebSocket(wsUrl);
    
    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.type === 'notification') {
            // Update badge
            const currentCount = parseInt(document.querySelector('.notification-badge').textContent) || 0;
            updateNotificationBadge(currentCount + 1);
            
            // Show toast if modal isn't open
            if (document.getElementById('notificationsModal').style.display !== 'flex') {
                showToast(data.message, 'info');
            }
        }
    };
    
    socket.onclose = function(e) {
        console.log('Notification socket closed:', e);
        setTimeout(initializeNotificationWebSocket, 5000); // Reconnect after 5s
    };
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeNotificationWebSocket();
});

// WebSocket for real-time notifications (add to your existing WebSocket code)
function initializeNotificationWebSocket() {
    const wsScheme = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = `${wsScheme}${window.location.host}/ws/notifications/`;
    
    const notificationSocket = new WebSocket(wsUrl);
    
    notificationSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.type === 'notification') {
            // Update badge count
            const currentCount = parseInt(document.querySelector('.notification-badge').textContent) || 0;
            updateNotificationBadge(currentCount + 1);
            
            // Show toast notification if modal isn't open
            if (document.getElementById('notificationsModal').style.display === 'none') {
                showToast(data.message, 'info');
            }
        }
    };
    
    notificationSocket.onclose = function(e) {
        console.log('Notification WebSocket closed:', e);
        setTimeout(initializeNotificationWebSocket, 5000); // Reconnect after 5 seconds
    };
}

// Call this when the page loads
document.addEventListener('DOMContentLoaded', initializeNotificationWebSocket);

function toggleModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = modal.style.display === 'none' ? 'flex' : 'none';
    }
}

if (hamburger) {
    hamburger.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        sidebar.classList.toggle('mobile-hidden');
        sidebarOverlay.classList.toggle('active');
        hamburger.classList.toggle('active');
    });
    hamburger.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            hamburger.click();
        }
    });
}

if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', () => {
        sidebar.classList.remove('open');
        sidebar.classList.add('mobile-hidden');
        sidebarOverlay.classList.remove('active');
        hamburger.classList.remove('active');
    });
}

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
        item.classList.add('active');
        if (item.dataset.url) {
            window.location.href = item.dataset.url;
        }
        if (window.innerWidth <= 768) {
            sidebar.classList.remove('open');
            sidebar.classList.add('mobile-hidden');
            sidebarOverlay.classList.remove('active');
            hamburger.classList.remove('active');
        }
    });
    item.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            item.click();
        }
    });
});

document.querySelectorAll('.view-tasks-btn[data-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
        toggleModal(btn.dataset.modal + 'Modal');
    });
});

document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => {
        btn.closest('.modal').style.display = 'none';
    });
});

if (document.getElementById('searchInput')) {
    document.getElementById('searchInput').addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        const rows = document.querySelectorAll('#tasksTableBody tr, #recordsTableBody tr, #meetingsTableBody tr');
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    });
}

document.querySelectorAll('.view-tasks-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        btn.style.transform = 'scale(0.95)';
        setTimeout(() => {
            btn.style.transform = 'scale(1)';
        }, 150);
    });
});

function updateTime() {
    const now = new Date();
    const hours = now.getHours();
    const greeting = document.querySelector('.greeting');
    if (greeting) {
        if (hours < 12) {
            greeting.textContent = greeting.textContent.replace(/Good (morning|afternoon|evening)/, 'Good morning');
        } else if (hours < 17) {
            greeting.textContent = greeting.textContent.replace(/Good (morning|afternoon|evening)/, 'Good afternoon');
        } else {
            greeting.textContent = greeting.textContent.replace(/Good (morning|afternoon|evening)/, 'Good evening');
        }
    }
}

updateTime();
setInterval(updateTime, 60000);

if (notificationTrigger && notificationsModal) {
    notificationTrigger.addEventListener('click', () => {
        toggleModal('notificationsModal');
        const badge = notificationTrigger.querySelector('.notification-badge');
        if (badge) {
            badge.textContent = '0';
            badge.style.display = 'none';
        }
    });
    notificationTrigger.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            notificationTrigger.click();
        }
    });
}

if (document.getElementById('clearNotifications')) {
    document.getElementById('clearNotifications').addEventListener('click', () => {
        const modalBody = notificationsModal.querySelector('.modal-body');
        if (modalBody) {
            modalBody.innerHTML = '<p class="empty-state">No new notifications.</p>';
        }
        notificationsModal.style.display = 'none';
    });
}

const toggleDarkMode = () => {
    document.body.classList.toggle('dark-mode');
    const taskText = document.querySelector('.task-text');
    if (taskText) {
        taskText.style.color = document.body.classList.contains('dark-mode') 
            ? 'var(--dark-text-light)' 
            : 'var(--text-light)';
    }
    savePreferences();
};

if (darkModeBtn) {
    darkModeBtn.addEventListener('click', toggleDarkMode);
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
        if (sidebar && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
            sidebar.classList.add('mobile-hidden');
            sidebarOverlay.classList.remove('active');
            hamburger.classList.remove('active');
        }
    }
    if (e.key === '/' && document.activeElement !== document.getElementById('searchInput')) {
        e.preventDefault();
        const searchInput = document.getElementById('searchInput');
        if (searchInput) searchInput.focus();
    }
});

document.querySelectorAll('.meetings-table tr, .tasks-table tr, .records-table tr').forEach(row => {
    row.addEventListener('mouseenter', () => {
        row.style.transition = 'background 0.3s ease';
    });
    row.addEventListener('mouseleave', () => {
        row.style.background = document.body.classList.contains('dark-mode') 
            ? 'transparent' 
            : 'transparent';
    });
});

const savePreferences = () => {
    const preferences = {
        darkMode: document.body.classList.contains('dark-mode'),
        lastSortDirection: document.querySelector('.sort-btn')?.textContent || 'Sort ↓'
    };
    localStorage.setItem('dashboardPreferences', JSON.stringify(preferences));
};

const loadPreferences = () => {
    const preferences = JSON.parse(localStorage.getItem('dashboardPreferences'));
    if (preferences) {
        if (preferences.darkMode) {
            document.body.classList.add('dark-mode');
        }
        const sortBtn = document.querySelector('.sort-btn');
        if (sortBtn && preferences.lastSortDirection) {
            sortBtn.textContent = preferences.lastSortDirection;
        }
    }
};

window.addEventListener('load', loadPreferences);

let touchStartX = 0;
let touchEndX = 0;

document.addEventListener('touchstart', e => {
    touchStartX = e.changedTouches[0].screenX;
});

document.addEventListener('touchend', e => {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
});

function handleSwipe() {
    const swipeThreshold = 50;
    if (touchEndX < touchStartX - swipeThreshold && sidebar && sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        sidebar.classList.add('mobile-hidden');
        sidebarOverlay.classList.remove('active');
        hamburger.classList.remove('active');
    }
    if (touchEndX > touchStartX + swipeThreshold && sidebar && !sidebar.classList.contains('open')) {
        sidebar.classList.add('open');
        sidebar.classList.remove('mobile-hidden');
        sidebarOverlay.classList.add('active');
        hamburger.classList.add('active');
    }
}

// AJAX for Modal Forms
function submitForm(formId, url, successModal = 'successAlertModal') {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const csrfToken = form.querySelector('input[name="csrfmiddlewaretoken"]');
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken ? csrfToken.value : ''
                }
            });
            if (response.ok) {
                toggleModal(successModal);
                form.closest('.modal').style.display = 'none';
                window.location.reload(); // Refresh to update data
            } else {
                toggleModal('failureAlertModal');
            }
        } catch (error) {
            console.error('Form submission error:', error);
            toggleModal('failureAlertModal');
        }
    });
}

// Initialize form handlers using data attributes
document.addEventListener('DOMContentLoaded', function() {
    // Get URLs from data attributes or hidden inputs
    const scheduleForm = document.getElementById('scheduleForm');
    if (scheduleForm) {
        const url = scheduleForm.dataset.submitUrl || scheduleForm.querySelector('input[name="submit_url"]')?.value;
        if (url) submitForm('scheduleForm', url);
    }
    
    const addTaskForm = document.getElementById('addTaskForm');
    if (addTaskForm) {
        const url = addTaskForm.dataset.submitUrl || addTaskForm.querySelector('input[name="submit_url"]')?.value;
        if (url) submitForm('addTaskForm', url);
    }
    
    const editTaskForm = document.getElementById('editTaskForm');
    if (editTaskForm) {
        const url = editTaskForm.dataset.submitUrl || editTaskForm.querySelector('input[name="submit_url"]')?.value;
        if (url) submitForm('editTaskForm', url);
    }
    
    const newRecordForm = document.getElementById('newRecordForm');
    if (newRecordForm) {
        const url = newRecordForm.dataset.submitUrl || newRecordForm.querySelector('input[name="submit_url"]')?.value;
        if (url) submitForm('newRecordForm', url);
    }
    
    const editRecordForm = document.getElementById('editRecordForm');
    if (editRecordForm) {
        const url = editRecordForm.dataset.submitUrl || editRecordForm.querySelector('input[name="submit_url"]')?.value;
        if (url) submitForm('editRecordForm', url);
    }
});

// Generic delete function
async function deleteItem(itemId, deleteUrl, modalId, successModal = 'successAlertModal') {
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value ||
                     document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    
    try {
        const response = await fetch(deleteUrl, {
            method: 'POST',
            body: JSON.stringify({ id: itemId }),
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        });
        if (response.ok) {
            toggleModal(successModal);
            document.getElementById(modalId).style.display = 'none';
            window.location.reload();
        } else {
            toggleModal('failureAlertModal');
        }
    } catch (error) {
        console.error('Delete error:', error);
        toggleModal('failureAlertModal');
    }
}

// Delete handlers using data attributes
document.addEventListener('click', function(e) {
    if (e.target.id === 'deleteSchedule') {
        e.preventDefault();
        const id = document.getElementById('scheduleId')?.value;
        const deleteUrl = e.target.dataset.deleteUrl;
        if (id && deleteUrl) {
            deleteItem(id, deleteUrl, 'scheduleModal');
        }
    }
    
    if (e.target.id === 'deleteTask') {
        e.preventDefault();
        const id = document.getElementById('taskId')?.value;
        const deleteUrl = e.target.dataset.deleteUrl;
        if (id && deleteUrl) {
            deleteItem(id, deleteUrl, 'editTaskModal');
        }
    }
    
    if (e.target.id === 'deleteRecord') {
        e.preventDefault();
        const id = document.getElementById('recordId')?.value;
        const deleteUrl = e.target.dataset.deleteUrl;
        if (id && deleteUrl) {
            deleteItem(id, deleteUrl, 'editRecordModal');
        }
    }
    
    if (e.target.id === 'exportPDF') {
        e.preventDefault();
        const exportUrl = e.target.dataset.exportUrl;
        if (exportUrl) {
            window.location.href = exportUrl;
        }
    }
    
    if (e.target.id === 'exportExcel') {
        e.preventDefault();
        const exportUrl = e.target.dataset.exportUrl;
        if (exportUrl) {
            window.location.href = exportUrl;
        }
    }
});