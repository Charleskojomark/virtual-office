document.addEventListener('DOMContentLoaded', () => {
    const chatSocket = new WebSocket('ws://' + window.location.host + '/ws/messaging/');

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        const messagesContainer = document.querySelector('.messages-container');
        const message = document.createElement('div');
        message.className = `message ${data.is_sent ? 'sent' : ''}`;
        message.innerHTML = `
            <div class="message-avatar">${data.user.initials}</div>
            <div class="message-content">
                <div class="message-text">${data.text}</div>
                <div class="message-time">${new Date().toLocaleTimeString()}</div>
            </div>`;
        messagesContainer.appendChild(message);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };

    chatSocket.onclose = function() {
        console.error('Chat socket closed unexpectedly');
    };

    // Send Message
    const messageForm = document.querySelector('.message-input-form');
    if (messageForm) {
        messageForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const messageInput = messageForm.querySelector('.message-input');
            const message = messageInput.value;
            if (message) {
                chatSocket.send(JSON.stringify({
                    message: message,
                    user_id: '{{ user.id }}' // Replace with actual user ID from context
                }));
                messageInput.value = '';
            }
        });
    }

    // Conversation Selection
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.addEventListener('click', () => {
            document.querySelectorAll('.conversation-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            // Fetch messages for selected conversation via AJAX
            fetch(`/api/messages/${item.dataset.conversationId}/`, {
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            })
            .then(response => response.json())
            .then(data => {
                const messagesContainer = document.querySelector('.messages-container');
                messagesContainer.innerHTML = '';
                data.messages.forEach(msg => {
                    const message = document.createElement('div');
                    message.className = `message ${msg.is_sent ? 'sent' : ''}`;
                    message.innerHTML = `
                        <div class="message-avatar">${msg.user.initials}</div>
                        <div class="message-content">
                            <div class="message-text">${msg.text}</div>
                            <div class="message-time">${msg.time}</div>
                        </div>`;
                    messagesContainer.appendChild(message);
                });
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            });
        });
    });

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
});