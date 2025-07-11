document.addEventListener('DOMContentLoaded', function() {
    // Bar Chart: Tasks Completed vs Overdue
    const tasksBarCtx = document.getElementById('tasksBarChart');
    if (tasksBarCtx) {
        new Chart(tasksBarCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: window.tasksBarData ? window.tasksBarData.labels : ['Completed', 'Overdue'],
                datasets: [{
                    label: 'Tasks',
                    data: window.tasksBarData ? window.tasksBarData.data : [25, 5],
                    backgroundColor: ['#36A2EB', '#FF6384'],
                    borderColor: ['#36A2EB', '#FF6384'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Tasks'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Status'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    // Pie Chart: Task Categories
    const categoriesPieCtx = document.getElementById('taskCategoriesPieChart');
    if (categoriesPieCtx) {
        new Chart(categoriesPieCtx.getContext('2d'), {
            type: 'pie',
            data: {
                labels: window.categoriesPieData ? window.categoriesPieData.labels : ['Work', 'Personal', 'Urgent', 'Project'],
                datasets: [{
                    data: window.categoriesPieData ? window.categoriesPieData.data : [12, 8, 5, 10],
                    backgroundColor: ['#36A2EB', '#FF6384', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'],
                    borderColor: ['#ffffff'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    }

    // Line Chart: Task Completion Over Time
    const taskCompletionCtx = document.getElementById('taskCompletionChart');
    if (taskCompletionCtx) {
        new Chart(taskCompletionCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: window.taskCompletionData ? window.taskCompletionData.labels : ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Completed Tasks',
                    data: window.taskCompletionData ? window.taskCompletionData.data : [10, 20, 15, 30, 25, 40],
                    borderColor: '#36A2EB',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Tasks Completed'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Month'
                        }
                    }
                }
            }
        });
    }

    // Bar Chart: User Activity
    const userActivityCtx = document.getElementById('userActivityChart');
    if (userActivityCtx) {
        new Chart(userActivityCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: window.userActivityData ? window.userActivityData.labels : ['User1', 'User2', 'User3'],
                datasets: [{
                    label: 'Tasks Assigned',
                    data: window.userActivityData ? window.userActivityData.data : [50, 30, 20],
                    backgroundColor: '#4BC0C0',
                    borderColor: '#4BC0C0',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Tasks Assigned'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Users'
                        }
                    }
                }
            }
        });
    }

    // Handle filter changes
    const filters = ['date-filter', 'user-filter', 'task-type-filter'];
    filters.forEach(filterId => {
        const select = document.getElementById(filterId);
        if (select) {
            select.addEventListener('change', function() {
                const params = new URLSearchParams(window.location.search);
                params.set(filterId.replace('-filter', ''), this.value);
                window.location.search = params.toString();
            });
        }
    });

    // Handle export buttons
    const exportButtons = document.querySelectorAll('[data-modal="export-report"]');
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const format = this.getAttribute('data-format');
            if (format) {
                console.log(`Exporting report as ${format.toUpperCase()}...`);
                // TODO: Implement AJAX call to backend endpoint for export
                // Example: 
                // fetch(`/export-report?format=${format}&${window.location.search}`)
                //     .then(response => response.blob())
                //     .then(blob => {
                //         const url = window.URL.createObjectURL(blob);
                //         const a = document.createElement('a');
                //         a.href = url;
                //         a.download = `report.${format}`;
                //         a.click();
                //     })
                //     .catch(error => console.error('Export failed:', error));
            } else {
                console.error('Export format not specified');
            }
        });
    });

    // Handle notification trigger
    const notificationTrigger = document.getElementById('notificationTrigger');
    if (notificationTrigger) {
        notificationTrigger.addEventListener('click', function() {
            console.log('Notifications clicked!');
            // TODO: Implement notification popup/modal
            // Example:
            // showNotificationModal();
        });
    }

    // Helper function to safely get data from window object
    function getChartData(dataName, defaultData) {
        return window[dataName] || defaultData;
    }

    // Error handling for Chart.js
    window.addEventListener('error', function(event) {
        if (event.error && event.error.message && event.error.message.includes('Chart')) {
            console.error('Chart.js error:', event.error);
            // Could show a user-friendly message here
        }
    });
});