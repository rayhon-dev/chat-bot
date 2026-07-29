(function() {
    const script = document.currentScript;
    const API_KEY = script.getAttribute('data-api-key');
    const API_URL = script.getAttribute('data-api-url') || 'http://127.0.0.1:8000/adapters/chat/';

    let sessionId = localStorage.getItem('chatbot_session_id_' + API_KEY);

    const container = document.createElement('div');
    container.id = 'my-chatbot-widget';
    container.innerHTML = `
        <style>
            #my-chatbot-widget * { box-sizing: border-box; font-family: sans-serif; }
            #cb-bubble { position: fixed; bottom: 20px; right: 20px; width: 60px; height: 60px;
                border-radius: 50%; background: #4f46e5; color: white; display: flex;
                align-items: center; justify-content: center; cursor: pointer; font-size: 24px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2); z-index: 9999; }
            #cb-window { position: fixed; bottom: 90px; right: 20px; width: 350px; height: 500px;
                background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.2);
                display: none; flex-direction: column; z-index: 9999; overflow: hidden; }
            #cb-window.open { display: flex; }
            #cb-header { background: #4f46e5; color: white; padding: 12px; font-weight: bold; }
            #cb-messages { flex: 1; overflow-y: auto; padding: 12px; }
            .cb-msg { margin-bottom: 10px; white-space: pre-wrap; line-height: 1.4; }
            .cb-msg.user { text-align: right; }
            .cb-msg.user .cb-bubble-text { background: #4f46e5; color: white; padding: 8px 12px;
                border-radius: 10px; display: inline-block; }
            .cb-msg.bot .cb-bubble-text { background: #f1f1f1; color: #111; padding: 8px 12px;
                border-radius: 10px; display: inline-block; }
            #cb-input-row { display: flex; padding: 8px; border-top: 1px solid #eee; }
            #cb-input { flex: 1; border: 1px solid #ddd; border-radius: 8px; padding: 8px; }
            #cb-send { margin-left: 6px; background: #4f46e5; color: white; border: none;
                border-radius: 8px; padding: 8px 14px; cursor: pointer; }
        </style>
        <div id="cb-bubble">💬</div>
        <div id="cb-window">
            <div id="cb-header">Yordamchi</div>
            <div id="cb-messages"></div>
            <div id="cb-input-row">
                <input id="cb-input" type="text" placeholder="Savolingizni yozing..." />
                <button id="cb-send">Yubor</button>
            </div>
        </div>
    `;
    document.body.appendChild(container);

    const win = container.querySelector('#cb-window');
    const bubbleBtn = container.querySelector('#cb-bubble');
    const messages = container.querySelector('#cb-messages');
    const input = container.querySelector('#cb-input');
    const sendBtn = container.querySelector('#cb-send');

    bubbleBtn.onclick = () => win.classList.toggle('open');

    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.className = 'cb-msg ' + sender;
        div.innerHTML = `<span class="cb-bubble-text"></span>`;
        div.querySelector('.cb-bubble-text').textContent = text;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;
        addMessage(text, 'user');
        input.value = '';

        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_KEY}`
            },
            body: JSON.stringify({ message: text, session_id: sessionId })
        });
        const data = await response.json();
        sessionId = data.session_id;
        localStorage.setItem('chatbot_session_id_' + API_KEY, sessionId);
        addMessage(data.answer, 'bot');
    }

    sendBtn.onclick = sendMessage;
    input.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });
})();