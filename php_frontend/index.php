<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Opti Matrix AI Assistant - Premium Experience</title>
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Marked.js for Robust Markdown Parsing -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    
    <style>
        :root {
          --bg-gradient: linear-gradient(135deg, #f6f8fb 0%, #e5ebf4 100%);
          --chat-bg: rgba(255, 255, 255, 0.85);
          --text-primary: #111827;
          --text-secondary: #4b5563;
          --accent-color: #2563eb;
          --accent-hover: #1d4ed8;
          --accent-gradient: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
          --border-color: rgba(229, 231, 235, 0.7);
          --user-msg-text: #ffffff;
          --bot-msg-bg: #ffffff;
          --bot-msg-text: #1f2937;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
          font-family: 'Inter', sans-serif;
          background: var(--bg-gradient);
          color: var(--text-primary);
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 100vh;
          -webkit-font-smoothing: antialiased;
        }

        /* Glassmorphism Chat Container */
        .chat-container {
          width: 100%;
          max-width: 900px;
          height: 92vh;
          background: var(--chat-bg);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border-radius: 20px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.05);
          display: flex;
          flex-direction: column;
          overflow: hidden;
          border: 1px solid rgba(255, 255, 255, 0.5);
        }

        .chat-header {
          padding: 24px 32px;
          border-bottom: 1px solid var(--border-color);
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: rgba(255, 255, 255, 0.6);
          backdrop-filter: blur(8px);
          z-index: 10;
        }

        .chat-header-info {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .avatar-container {
          position: relative;
        }

        .avatar-img {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background: var(--accent-gradient);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          font-size: 1.2rem;
          box-shadow: 0 4px 10px rgba(37, 99, 235, 0.2);
        }

        .status-dot {
          position: absolute;
          bottom: 2px;
          right: 2px;
          width: 12px;
          height: 12px;
          background-color: #22c55e;
          border-radius: 50%;
          border: 2px solid #ffffff;
        }

        .chat-header h1 { 
          font-size: 1.3rem; 
          font-weight: 700; 
          color: var(--text-primary); 
          letter-spacing: -0.02em; 
        }
        
        .chat-header p { 
          font-size: 0.9rem; 
          color: var(--text-secondary); 
          margin-top: 2px;
          font-weight: 500;
        }

        .chat-messages {
          flex: 1;
          padding: 32px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .message-wrapper { 
          display: flex; 
          width: 100%; 
          gap: 12px;
        }
        .message-wrapper.user { justify-content: flex-end; }
        .message-wrapper.bot { justify-content: flex-start; }

        .bot-avatar-small {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: var(--accent-gradient);
          flex-shrink: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          font-size: 14px;
          margin-top: 4px;
          box-shadow: 0 2px 6px rgba(37,99,235,0.2);
        }

        .message-inner {
            display: flex;
            flex-direction: column;
            max-width: 75%;
        }
        .message-wrapper.bot .message-inner { align-items: flex-start; }
        .message-wrapper.user .message-inner { align-items: flex-end; }

        .message {
          padding: 14px 20px;
          font-size: 0.95rem;
          line-height: 1.6;
          animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
          opacity: 0;
          transform: translateY(10px);
          box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        }

        .message.user {
          background: var(--accent-gradient);
          color: var(--user-msg-text);
          border-radius: 18px 18px 4px 18px;
        }

        .message.bot {
          background-color: var(--bot-msg-bg);
          color: var(--bot-msg-text);
          border-radius: 18px 18px 18px 4px;
          border: 1px solid var(--border-color);
        }

        /* Markdown Styles inside bot message */
        .message.bot p { margin-bottom: 0.75em; }
        .message.bot p:last-child { margin-bottom: 0; }
        .message.bot strong { color: #111827; font-weight: 600; }
        .message.bot ul, .message.bot ol { margin-left: 1.5em; margin-bottom: 0.75em; }
        .message.bot li { margin-bottom: 0.25em; }
        .message.bot code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9em; color: #db2777; }
        .message.bot pre code { display: block; background: #1e293b; color: #e2e8f0; padding: 12px; overflow-x: auto; border-radius: 8px; }

        /* Links inside messages */
        .message a {
            display: inline-block;
            margin-top: 10px;
            margin-bottom: 4px;
            margin-right: 8px;
            padding: 8px 18px;
            background-color: #eff6ff;
            color: var(--accent-color);
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
            border: 1px solid #bfdbfe;
            transition: all 0.2s ease;
        }
        .message a:hover {
            background-color: var(--accent-color);
            color: white;
            border-color: var(--accent-color);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
        }

        /* Input Area */
        .chat-input-container { 
          padding: 24px 32px; 
          border-top: 1px solid var(--border-color); 
          background: rgba(255, 255, 255, 0.6);
          backdrop-filter: blur(8px);
        }
        
        .chat-form { 
          display: flex; 
          gap: 12px; 
          background: #ffffff;
          padding: 8px;
          border-radius: 24px;
          border: 1px solid var(--border-color);
          box-shadow: 0 2px 10px rgba(0,0,0,0.03);
          transition: border-color 0.2s, box-shadow 0.2s;
        }
        .chat-form:focus-within {
            border-color: var(--accent-color);
            box-shadow: 0 4px 20px rgba(37,99,235,0.1);
        }
        
        .chat-input {
          flex: 1;
          padding: 12px 16px;
          border: none;
          background: transparent;
          font-size: 1rem;
          outline: none;
          color: var(--text-primary);
          font-family: inherit;
        }
        .chat-input::placeholder { color: #9ca3af; }
        
        .send-button {
          background: var(--accent-gradient);
          color: white;
          border: none;
          border-radius: 50%;
          width: 44px;
          height: 44px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s ease;
          flex-shrink: 0;
        }
        .send-button:hover:not(:disabled) { 
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(37,99,235,0.3);
        }
        .send-button:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; }
        .send-button svg { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; margin-left: -2px; }

        /* Typing Indicator */
        .typing-indicator {
          padding: 14px 20px;
          background-color: var(--bot-msg-bg);
          border-radius: 18px 18px 18px 4px;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          border: 1px solid var(--border-color);
          animation: slideUp 0.3s ease-out forwards;
        }
        .dot {
          width: 6px;
          height: 6px;
          background-color: #9ca3af;
          border-radius: 50%;
          animation: bounce 1.4s infinite ease-in-out both;
        }
        .dot:nth-child(1) { animation-delay: -0.32s; }
        .dot:nth-child(2) { animation-delay: -0.16s; }
        .dot:nth-child(3) { animation-delay: 0s; }

        @keyframes slideUp { to { opacity: 1; transform: translateY(0); } }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; } 40% { transform: scale(1); opacity: 1; } }

        /* Scrollbars */
        .chat-messages::-webkit-scrollbar { width: 8px; }
        .chat-messages::-webkit-scrollbar-track { background: transparent; }
        .chat-messages::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 4px; border: 2px solid #ffffff; }
        .chat-messages::-webkit-scrollbar-thumb:hover { background-color: #94a3b8; }
        
        /* Suggestions */
        .suggestions-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 14px;
        }
        .filter-btn {
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
            font-family: inherit;
            cursor: pointer;
            transition: all 0.2s ease;
            background: #ffffff;
            border: 1px solid #d1d5db;
            color: #4b5563;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        .filter-btn:hover {
            border-color: var(--accent-color);
            color: var(--accent-color);
            background: #eff6ff;
            transform: translateY(-1px);
        }
    </style>
</head>
<body>
    <div class="chat-container">
      <div class="chat-header">
        <div class="chat-header-info">
            <div class="avatar-container">
                <div class="avatar-img">AI</div>
                <div class="status-dot"></div>
            </div>
            <div>
                <h1>Opti Matrix Assistant</h1>
                <p>Always here to help optimize your matrix.</p>
            </div>
        </div>
      </div>

      <div class="chat-messages" id="chat-messages">
        <!-- Messages will be injected here -->
      </div>

      <div class="chat-input-container">
        <form id="chat-form" class="chat-form">
          <input type="text" id="chat-input" class="chat-input" placeholder="Ask me anything..." autocomplete="off" />
          <button type="submit" id="send-button" class="send-button" disabled>
            <svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
          </button>
        </form>
      </div>
    </div>

    <script>
        const BACKEND_API_URL = "https://opti-matrix-llm.onrender.com";
        
        const chatMessages = document.getElementById('chat-messages');
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-button');
        const chatForm = document.getElementById('chat-form');
        
        let isLoading = false;

        // Configure marked.js options
        const renderer = new marked.Renderer();
        renderer.link = function(href, title, text) {
            return `<a target="_blank" rel="noopener noreferrer" href="${href}" title="${title || ''}">${text}</a>`;
        };
        marked.setOptions({
            renderer: renderer,
            breaks: true,
            gfm: true
        });

        function scrollToBottom() {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        chatInput.addEventListener('input', () => {
            sendButton.disabled = !chatInput.value.trim() || isLoading;
        });

        function renderMessageContent(content) {
            // Custom Block: PROFILE_CARD
            if (content.startsWith("PROFILE_CARD:")) {
                const parts = content.split(":");
                const dataStr = parts.slice(1).join(":");
                const data = dataStr.split("|");
                if (data.length === 5) {
                    const [name, title, company, linkedin, image] = data;
                    return `
                        <div style="display: flex; flex-direction: column; align-items: center; background-color: #ffffff; padding: 24px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); color: #333; max-width: 280px; border: 1px solid #e5e7eb; margin: 10px 0;">
                            <img src="${image}" alt="${name}" style="width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 3px solid #2563eb; padding: 4px; box-shadow: 0 4px 10px rgba(37,99,235,0.15);" />
                            <h3 style="margin: 16px 0 4px 0; font-size: 1.1rem; font-weight: 700; color: #111827;">${name}</h3>
                            <p style="margin: 0 0 4px 0; font-weight: 600; color: #3b82f6; font-size: 0.9rem;">${title}</p>
                            <p style="margin: 0 0 20px 0; font-size: 0.85rem; color: #6b7280; font-weight: 500; text-align: center;">${company}</p>
                            <a href="${linkedin}" target="_blank" rel="noopener noreferrer" style="margin:0; padding: 10px 16px; background-color: #0a66c2; color: white; border: none; border-radius: 8px; font-weight: 600; font-size: 14px; display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; transition: all 0.2s ease;">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M0 1.146C0 .513.526 0 1.175 0h13.65C15.474 0 16 .513 16 1.146v13.708c0 .633-.526 1.146-1.175 1.146H1.175C.526 16 0 15.487 0 14.854zm4.943 12.248V6.169H2.542v7.225zm-1.2-8.212c.837 0 1.358-.554 1.358-1.248-.015-.709-.52-1.248-1.342-1.248S2.4 3.226 2.4 3.934c0 .694.521 1.248 1.327 1.248zm4.908 8.212V9.359c0-.216.016-.432.08-.586.173-.431.568-.878 1.232-.878.869 0 1.216.662 1.216 1.634v3.865h2.401V9.25c0-2.22-1.184-3.252-2.764-3.252-1.274 0-1.845.7-2.165 1.193v.025h-.016l.016-.025V6.169h-2.4c.03.678 0 7.225 0 7.225z" /></svg>
                                View Profile
                            </a>
                        </div>`;
                }
            }

            // Custom Block: TIMELINE_DATA
            if (content.startsWith("TIMELINE_DATA:")) {
                const jsonStr = content.substring("TIMELINE_DATA:".length);
                try {
                    const events = JSON.parse(jsonStr);
                    const timelineId = 'timeline-' + Date.now();
                    window['timelineData_' + timelineId] = events;
                    
                    return `
                    <div id="${timelineId}" style="width: 100%; max-width: 100%; margin: 10px 0;">
                        <h3 style="margin: 0 0 16px 0; font-size: 1.2rem; color: #111827; display: flex; align-items: center; gap: 8px;">
                            🚀 Opti Matrix Journey
                        </h3>
                        <div class="suggestions-container" style="margin-bottom: 24px;">
                            <button onclick="renderTimeline('${timelineId}', 'All')" class="filter-btn" style="border-color:#2563eb; background:#eff6ff; color:#1d4ed8;">Full Journey</button>
                            <button onclick="renderTimeline('${timelineId}', '2010-2012')" class="filter-btn">2010-2012</button>
                            <button onclick="renderTimeline('${timelineId}', '2013-2015')" class="filter-btn">2013-2015</button>
                            <button onclick="renderTimeline('${timelineId}', '2016-2018')" class="filter-btn">2016-2018</button>
                            <button onclick="renderTimeline('${timelineId}', 'Major Achievements')" class="filter-btn">🏆 Major Achievements</button>
                        </div>
                        <div class="timeline-content" style="position: relative; border-left: 2px solid #e5e7eb; margin-left: 12px; padding-left: 24px;">
                            ${generateTimelineHTML(events)}
                        </div>
                    </div>
                    `;
                } catch(e) {
                    console.error("Error parsing timeline JSON:", e);
                }
            }

            // Standard text parsing using Marked.js
            return marked.parse(content);
        }

        window.renderTimeline = function(containerId, filter) {
            const container = document.getElementById(containerId);
            if(!container) return;
            
            const buttons = container.querySelectorAll('.filter-btn');
            buttons.forEach(btn => {
                const btnText = btn.innerText;
                const isMatch = (filter === 'All' && btnText.includes('Full Journey')) || 
                               (filter === 'Major Achievements' && btnText.includes('Major Achievements')) ||
                               btnText === filter;
                
                if(isMatch) {
                    btn.style.borderColor = '#2563eb';
                    btn.style.backgroundColor = '#eff6ff';
                    btn.style.color = '#1d4ed8';
                } else {
                    btn.style.borderColor = '#d1d5db';
                    btn.style.backgroundColor = '#fff';
                    btn.style.color = '#4b5563';
                }
            });

            const allEvents = window['timelineData_' + containerId];
            let filteredEvents = allEvents;
            if (filter === "2010-2012") {
                filteredEvents = allEvents.filter(e => ["2010", "2011", "2012"].includes(e.year));
            } else if (filter === "2013-2015") {
                filteredEvents = allEvents.filter(e => ["2013", "2014", "2015"].includes(e.year));
            } else if (filter === "2016-2018") {
                filteredEvents = allEvents.filter(e => ["2016", "2017", "2018"].includes(e.year));
            } else if (filter === "Major Achievements") {
                filteredEvents = allEvents.filter(e =>
                    e.title.toLowerCase().includes("achieve") ||
                    e.title.includes("300th") ||
                    e.title.toLowerCase().includes("google") ||
                    e.title.includes("Biggest") ||
                    e.title.toLowerCase().includes("award")
                );
            }

            const contentDiv = container.querySelector('.timeline-content');
            if(filteredEvents.length === 0) {
                contentDiv.innerHTML = '<p style="color: #6b7280; font-size: 0.9rem; font-style: italic;">No events found for this filter.</p>';
            } else {
                contentDiv.innerHTML = generateTimelineHTML(filteredEvents);
            }
        };

        function generateTimelineHTML(events) {
            return events.map((ev) => `
                <div style="margin-bottom: 24px; position: relative;">
                    <div style="position: absolute; left: -31px; top: 4px; width: 14px; height: 14px; background-color: #2563eb; border-radius: 50%; border: 3px solid #fff; box-shadow: 0 0 0 1px #e5e7eb;"></div>
                    <span style="display: inline-block; background-color: #f1f5f9; color: #334155; font-size: 0.75rem; font-weight: 700; padding: 4px 10px; border-radius: 12px; margin-bottom: 8px; letter-spacing: 0.05em;">${ev.year}</span>
                    <div style="background-color: #fff; border: 1px solid #f1f5f9; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);">
                        <h4 style="margin: 0 0 4px 0; font-size: 1rem; color: #111827; font-weight: 700;">${ev.title}</h4>
                        <p style="margin: 0 0 10px 0; font-size: 0.8rem; color: #6b7280; font-weight: 500;">${ev.date}</p>
                        <p style="margin: 0 0 16px 0; font-size: 0.9rem; color: #4b5563; line-height: 1.5;">${ev.desc}</p>
                        ${ev.link ? `
                        <a href="${ev.link}" target="_blank" rel="noopener noreferrer" style="margin:0; display: inline-flex; align-items: center; justify-content: center; background-color: #eff6ff; color: #2563eb; padding: 8px 16px; border-radius: 6px; border: 1px solid #bfdbfe; text-decoration: none; font-weight: 600; font-size: 0.85rem; transition: all 0.2s ease;">
                            ${ev.linkText} <span style="margin-left: 6px; font-size: 1rem;">→</span>
                        </a>` : ''}
                    </div>
                </div>
            `).join('');
        }

        function addMessage(role, content, suggestions = []) {
            const wrapper = document.createElement('div');
            wrapper.className = `message-wrapper ${role}`;
            
            // Add Avatar for bot
            if (role === 'bot') {
                const avatar = document.createElement('div');
                avatar.className = 'bot-avatar-small';
                avatar.innerText = 'AI';
                wrapper.appendChild(avatar);
            }
            
            const innerWrapper = document.createElement('div');
            innerWrapper.className = 'message-inner';
            
            const messageEl = document.createElement('div');
            messageEl.className = `message ${role}`;
            messageEl.innerHTML = renderMessageContent(content);
            
            innerWrapper.appendChild(messageEl);

            if (role === 'bot' && suggestions && suggestions.length > 0) {
                const suggestionsDiv = document.createElement('div');
                suggestionsDiv.className = 'suggestions-container';
                
                suggestions.forEach(suggestion => {
                    const btn = document.createElement('button');
                    btn.className = 'filter-btn';
                    btn.innerText = suggestion;
                    btn.onclick = () => {
                        chatInput.value = suggestion;
                        chatForm.dispatchEvent(new Event('submit'));
                    };
                    suggestionsDiv.appendChild(btn);
                });
                innerWrapper.appendChild(suggestionsDiv);
            }

            wrapper.appendChild(innerWrapper);
            chatMessages.appendChild(wrapper);
            scrollToBottom();
        }

        function showTyping() {
            const wrapper = document.createElement('div');
            wrapper.className = 'message-wrapper bot typing-wrapper';
            
            const avatar = document.createElement('div');
            avatar.className = 'bot-avatar-small';
            avatar.innerText = 'AI';
            wrapper.appendChild(avatar);
            
            const innerWrapper = document.createElement('div');
            innerWrapper.className = 'message-inner';
            
            innerWrapper.innerHTML = `
                <div class="typing-indicator">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            `;
            
            wrapper.appendChild(innerWrapper);
            chatMessages.appendChild(wrapper);
            scrollToBottom();
        }

        function hideTyping() {
            const typing = chatMessages.querySelector('.typing-wrapper');
            if(typing) typing.remove();
        }

        function generateUUID() {
            if (typeof crypto !== 'undefined' && crypto.randomUUID) {
                return crypto.randomUUID();
            }
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0;
                const v = c === 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        }
        
        const sessionId = generateUUID();

        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const userMsg = chatInput.value.trim();
            if (!userMsg || isLoading) return;

            addMessage('user', userMsg);
            chatInput.value = "";
            sendButton.disabled = true;
            isLoading = true;
            
            showTyping();

            try {
                const response = await fetch(BACKEND_API_URL + "/ask", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ question: userMsg, session_id: sessionId }),
                });

                if (!response.ok) throw new Error("Server communication failed");

                const data = await response.json();
                hideTyping();
                addMessage('bot', data.answer || "I'm sorry, I couldn't process that. Please try again.", data.suggested_questions);
            } catch (error) {
                console.error("Error:", error);
                hideTyping();
                addMessage('bot', "Connection error. Please ensure the backend is running and try again.");
            } finally {
                isLoading = false;
                if(chatInput.value.trim()) sendButton.disabled = false;
            }
        });

        async function loadChatHistory() {
            try {
                const response = await fetch(BACKEND_API_URL + "/history/" + sessionId);
                if (response.ok) {
                    const data = await response.json();
                    if (data.chat_history && data.chat_history.length > 0) {
                        data.chat_history.forEach(msg => {
                            const role = msg.role === 'assistant' ? 'bot' : 'user';
                            addMessage(role, msg.content);
                        });
                        return;
                    }
                }
            } catch (error) {
                console.error("History loading error:", error);
            }
            
            addMessage('bot', "Hello! I am the **Opti Matrix AI Assistant**. \n\nWe specialize in optimizing complicated digital challenges. How can I help you today?", [
                "What services do you offer?", 
                "Where is your office located?",
                "Can you show me your portfolio?"
            ]);
        }
        
        loadChatHistory();
    </script>
</body>
</html>
