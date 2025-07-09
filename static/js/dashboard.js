document.addEventListener('DOMContentLoaded', () => {
    // Animate stat cards on load
    document.querySelectorAll('.stat-card').forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('animate-slideInUp');
        }, index * 100);
    });

    // Initialize Chart.js
    const statsChart = document.getElementById('statsChart');
    if (statsChart) {
        new Chart(statsChart, {
            type: 'bar',
            data: {
                labels: ['Users', 'Tasks', 'Events', 'Records'],
                datasets: [{
                    label: 'Activity',
                    data: [/* Replace with dynamic data from view */ 50, 30, 20, 40],
                    backgroundColor: 'var(--primary)',
                    borderColor: 'var(--primary-dark)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }
});