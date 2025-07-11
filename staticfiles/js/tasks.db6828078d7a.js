document.addEventListener('DOMContentLoaded', () => {
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

    // Search Tasks
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            const filter = searchInput.value.toLowerCase();
            document.querySelectorAll('.task-item').forEach(item => {
                const title = item.querySelector('.task-title').textContent.toLowerCase();
                item.style.display = title.includes(filter) ? '' : 'none';
            });
        });
    }

    // Filter by Status
    const statusFilter = document.querySelector('.filter-select');
    if (statusFilter) {
        statusFilter.addEventListener('change', () => {
            const status = statusFilter.value;
            document.querySelectorAll('.task-item').forEach(item => {
                const taskStatus = item.querySelector('.task-meta').textContent.toLowerCase();
                item.style.display = status === '' || taskStatus.includes(status) ? '' : 'none';
            });
        });
    }

    // Task Actions (Edit/Delete)
    document.querySelectorAll('.task-actions .edit').forEach(button => {
        button.addEventListener('click', () => {
            const taskId = button.getAttribute('data-id');
            fetch(`/tasks/api/${taskId}/`, {
                method: 'GET',
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            })
            .then(response => response.json())
            .then(data => {
                const modal = document.getElementById('edit-task');
                modal.querySelector('input[name="title"]').value = data.title;
                modal.querySelector('textarea[name="description"]').value = data.description;
                modal.querySelector('input[name="due_date"]').value = data.due_date;
                modal.querySelector('select[name="status"]').value = data.status;
                modal.classList.add('active');
            });
        });
    });

    document.querySelectorAll('.task-actions .delete').forEach(button => {
        button.addEventListener('click', () => {
            const taskId = button.getAttribute('data-id');
            showConfirmation('Are you sure you want to delete this task?', () => {
                const modal = document.getElementById('confirm-password');
                modal.classList.add('active');
                modal.querySelector('.btn-primary').onclick = () => {
                    const password = modal.querySelector('input[name="password"]').value;
                    fetch(`/tasks/api/${taskId}/delete/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({ password })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            showAlert('Success', 'Task deleted successfully', 'success');
                            location.reload();
                        } else {
                            showAlert('Error', 'Invalid password', 'error');
                        }
                    });
                };
            });
        });
    });

    // Add Task
    document.querySelector('#add-task .btn-primary').addEventListener('click', () => {
        const form = document.querySelector('#add-task form');
        const data = {
            title: form.querySelector('input[name="title"]').value,
            description: form.querySelector('textarea[name="description"]').value,
            due_date: form.querySelector('input[name="due_date"]').value,
            status: form.querySelector('select[name="status"]').value
        };
        fetch('/tasks/api/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showAlert('Success', 'Task created successfully', 'success');
                location.reload();
            } else {
                showAlert('Error', 'Failed to create task', 'error');
            }
        });
    });
});