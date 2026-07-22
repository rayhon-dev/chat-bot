(function() {
    const API_KEY = document.currentScript.getAttribute('data-api-key');
    const API_URL = document.currentScript.getAttribute('data-api-url') || 'http://localhost:8000/adapters/chat/';

    let sessionId = localStorage.getItem('chatbot_session_id');

    async function sendMessage(message) {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_KEY}`
            },
            body: JSON.stringify({ message, session_id: sessionId })
        });
        const data = await response.json();
        sessionId = data.session_id;
        localStorage.setItem('chatbot_session_id', sessionId);
        return data.answer;
    }

    window.MyChatbot = { sendMessage };
})();