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

    const calendarEl = document.getElementById('calendar');
    if (calendarEl) {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            events: '/schedule/api/events/',
            eventClick: function(info) {
                showAlert('Event Details', `Title: ${info.event.title}\nDescription: ${info.event.extendedProps.description}`, 'success');
            },
            editable: true,
            selectable: true,
            select: function(info) {
                const modal = document.getElementById('add-event');
                modal.querySelector('input[name="date"]').value = info.start.toISOString().slice(0, 16);
                modal.classList.add('active');
            }
        });
        calendar.render();
    }

    // View toggle buttons
    document.querySelectorAll('.schedule-view-toggle .btn').forEach(button => {
        button.addEventListener('click', () => {
            document.querySelectorAll('.schedule-view-toggle .btn').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            const view = button.getAttribute('data-view');
            calendar.changeView(view === 'month' ? 'dayGridMonth' : view === 'week' ? 'timeGridWeek' : 'timeGridDay');
        });
    });

    // Add Event
    document.querySelector('#add-event .btn-primary').addEventListener('click', () => {
        const form = document.querySelector('#add-event form');
        const data = {
            title: form.querySelector('input[name="title"]').value,
            description: form.querySelector('textarea[name="description"]').value,
            date: form.querySelector('input[name="date"]').value
        };
        fetch('/schedule/api/events/create/', {
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
                showAlert('Success', 'Event created successfully', 'success');
                location.reload();
            } else {
                showAlert('Error', 'Failed to create event', 'error');
            }
        });
    });
});