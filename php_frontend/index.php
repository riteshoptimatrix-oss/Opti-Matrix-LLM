
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Company AI Assistant - PHP</title>
    <style>
        :root {
          --bg-color: #f0f2f5;
          --chat-bg: #ffffff;
          --text-primary: #1a1a1a;
          --text-secondary: #666666;
          --accent-color: #2563eb;
          --accent-hover: #1d4ed8;
          --border-color: #e5e7eb;
          --user-msg-bg: #2563eb;
          --user-msg-text: #ffffff;
          --bot-msg-bg: #f3f4f6;
          --bot-msg-text: #1a1a1a;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          background-color: var(--bg-color);
          color: var(--text-primary);
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 100vh;
        }

        .chat-container {
          width: 100%;
          max-width: 800px;
          height: 90vh;
          background-color: var(--chat-bg);
          border-radius: 8px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
          display: flex;
          flex-direction: column;
          overflow: hidden;
          border: 1px solid var(--border-color);
        }

        .chat-header {
          padding: 24px;
          border-bottom: 1px solid var(--border-color);
          text-align: center;
          background-color: var(--chat-bg);
          z-index: 10;
        }

        .chat-header h1 { font-size: 1.5rem; font-weight: 600; color: var(--text-primary); letter-spacing: -0.5px; }
        .chat-header p { font-size: 0.95rem; color: var(--text-secondary); margin-top: 6px; }

        .chat-messages {
          flex: 1;
          padding: 24px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 16px;
          background-color: #ffffff;
        }

        .message-wrapper { display: flex; width: 100%; }
        .message-wrapper.user { justify-content: flex-end; }
        .message-wrapper.bot { justify-content: flex-start; }

        .message {
          max-width: 75%;
          padding: 12px 18px;
          border-radius: 8px;
          font-size: 0.95rem;
          line-height: 1.5;
          animation: slideUp 0.15s ease-out forwards;
          opacity: 0;
          transform: translateY(6px);
          white-space: pre-wrap;
        }

        .message.user {
          background-color: var(--user-msg-bg);
          color: var(--user-msg-text);
          border-bottom-right-radius: 2px;
        }

        .message.bot {
          background-color: var(--bot-msg-bg);
          color: var(--bot-msg-text);
          border-bottom-left-radius: 2px;
          border: 1px solid var(--border-color);
        }

        .chat-input-container { padding: 16px 24px; border-top: 1px solid var(--border-color); background-color: var(--chat-bg); }
        .chat-form { display: flex; gap: 12px; }
        
        .chat-input {
          flex: 1;
          padding: 14px 18px;
          border: 1px solid var(--border-color);
          border-radius: 6px;
          font-size: 0.95rem;
          outline: none;
          transition: border-color 0.15s ease;
          background-color: #ffffff;
        }

        .chat-input:focus { border-color: var(--accent-color); box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1); }
        
        .send-button {
          background-color: var(--accent-color);
          color: white;
          border: none;
          border-radius: 6px;
          padding: 0 24px;
          font-size: 0.95rem;
          font-weight: 500;
          cursor: pointer;
          transition: background-color 0.15s ease;
        }

        .send-button:hover:not(:disabled) { background-color: var(--accent-hover); }
        .send-button:disabled { opacity: 0.6; cursor: not-allowed; }

        .typing-indicator {
          padding: 12px 18px;
          background-color: var(--bot-msg-bg);
          border-radius: 8px;
          border-bottom-left-radius: 2px;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          color: var(--text-secondary);
          font-size: 0.95rem;
          animation: slideUp 0.15s ease-out forwards;
          border: 1px solid var(--border-color);
        }

        .dot {
          width: 5px;
          height: 5px;
          background-color: var(--text-secondary);
          border-radius: 50%;
          animation: bounce 1.4s infinite ease-in-out both;
        }

        .dot:nth-child(1) { animation-delay: -0.32s; }
        .dot:nth-child(2) { animation-delay: -0.16s; }
        .dot:nth-child(3) { animation-delay: 0s; }

        @keyframes slideUp { to { opacity: 1; transform: translateY(0); } }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0.6); } 40% { transform: scale(1); } }

        .chat-messages::-webkit-scrollbar { width: 6px; }
        .chat-messages::-webkit-scrollbar-track { background: transparent; }
        .chat-messages::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 3px; }
        .chat-messages::-webkit-scrollbar-thumb:hover { background-color: #94a3b8; }
        
        .md-link {
            display: inline-block;
            margin-top: 10px;
            margin-bottom: 6px;
            margin-right: 8px;
            padding: 8px 16px;
            background-color: #2563eb;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            font-size: 14px;
            box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
            border: 1px solid #1d4ed8;
            word-break: break-word;
            text-align: center;
        }
        
        .filter-btn {
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }
    </style>
</head>
<body>
    <div class="chat-container">
      <div class="chat-header">
        <h1>Company AI Assistant</h1>
        <div style="display: flex; align-items: center; justify-content: center; gap: 6px; margin-top: 4px;">
          <div style="width: 8px; height: 8px; background-color: #22c55e; border-radius: 50%;"></div>
          <p style="margin: 0;">Online | Ask me anything</p>
        </div>
      </div>

      <div class="chat-messages" id="chat-messages">
        <!-- Messages will be injected here -->
      </div>

      <div class="chat-input-container">
        <form id="chat-form" class="chat-form">
          <input type="text" id="chat-input" class="chat-input" placeholder="Type your question here..." />
          <button type="submit" id="send-button" class="send-button" disabled>Send</button>
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

        function scrollToBottom() {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        chatInput.addEventListener('input', () => {
            sendButton.disabled = !chatInput.value.trim() || isLoading;
        });

        function renderMessageContent(content) {
            // Check for PROFILE_CARD
            if (content.startsWith("PROFILE_CARD:")) {
                const parts = content.split(":");
                const dataStr = parts.slice(1).join(":");
                const data = dataStr.split("|");
                if (data.length === 5) {
                    const [name, title, company, linkedin, image] = data;
                    return `
                        <div style="display: flex; flex-direction: column; align-items: center; background-color: #ffffff; padding: 24px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); color: #333; max-width: 300px; border: 1px solid #e5e7eb; margin: 10px 0;">
                            <img src="${image}" alt="${name}" style="width: 140px; height: 140px; border-radius: 50%; object-fit: cover; border: 4px solid #2563eb; padding: 4px; background-color: #fff; box-shadow: 0 4px 10px rgba(37,99,235,0.2);" />
                            <h3 style="margin: 16px 0 4px 0; font-size: 20px; font-weight: bold; color: #111827;">${name}</h3>
                            <p style="margin: 0 0 6px 0; font-weight: 600; color: #3b82f6; font-size: 15px;">${title}</p>
                            <p style="margin: 0 0 20px 0; font-size: 14px; color: #6b7280; font-weight: 500;">${company}</p>
                            <a href="${linkedin}" target="_blank" rel="noopener noreferrer" style="padding: 10px 20px; background-color: #0a66c2; color: white; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 15px; display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; transition: all 0.2s ease; box-shadow: 0 4px 6px rgba(10,102,194,0.2);">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M0 1.146C0 .513.526 0 1.175 0h13.65C15.474 0 16 .513 16 1.146v13.708c0 .633-.526 1.146-1.175 1.146H1.175C.526 16 0 15.487 0 14.854zm4.943 12.248V6.169H2.542v7.225zm-1.2-8.212c.837 0 1.358-.554 1.358-1.248-.015-.709-.52-1.248-1.342-1.248S2.4 3.226 2.4 3.934c0 .694.521 1.248 1.327 1.248zm4.908 8.212V9.359c0-.216.016-.432.08-.586.173-.431.568-.878 1.232-.878.869 0 1.216.662 1.216 1.634v3.865h2.401V9.25c0-2.22-1.184-3.252-2.764-3.252-1.274 0-1.845.7-2.165 1.193v.025h-.016l.016-.025V6.169h-2.4c.03.678 0 7.225 0 7.225z" /></svg>
                                View LinkedIn Profile
                            </a>
                        </div>`;
                }
            }

            // Check for TIMELINE_DATA
            if (content.startsWith("TIMELINE_DATA:")) {
                const jsonStr = content.substring("TIMELINE_DATA:".length);
                try {
                    const events = JSON.parse(jsonStr);
                    const timelineId = 'timeline-' + Date.now();
                    window['timelineData_' + timelineId] = events;
                    
                    return `
                    <div id="${timelineId}" style="width: 100%; max-width: 600px; font-family: sans-serif; margin: 10px 0;">
                        <h3 style="margin: 0 0 16px 0; font-size: 22px; color: #111827; display: flex; align-items: center; gap: 8px;">
                            🚀 OPTI MATRIX JOURNEY
                        </h3>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 24px;" class="timeline-filters">
                            <button onclick="renderTimeline('${timelineId}', 'All')" class="filter-btn filter-active" style="border: none; background-color: #2563eb; color: #fff; box-shadow: 0 4px 6px rgba(37,99,235,0.2);">🚀 Full Journey</button>
                            <button onclick="renderTimeline('${timelineId}', '2010-2012')" class="filter-btn" style="border: 1px solid #d1d5db; background-color: #fff; color: #4b5563;">2010-2012</button>
                            <button onclick="renderTimeline('${timelineId}', '2013-2015')" class="filter-btn" style="border: 1px solid #d1d5db; background-color: #fff; color: #4b5563;">2013-2015</button>
                            <button onclick="renderTimeline('${timelineId}', '2016-2018')" class="filter-btn" style="border: 1px solid #d1d5db; background-color: #fff; color: #4b5563;">2016-2018</button>
                            <button onclick="renderTimeline('${timelineId}', 'Major Achievements')" class="filter-btn" style="border: 1px solid #d1d5db; background-color: #fff; color: #4b5563;">🏆 Major Achievements</button>
                        </div>
                        <div class="timeline-content" style="position: relative; border-left: 3px solid #e5e7eb; margin-left: 16px; padding-left: 24px;">
                            ${generateTimelineHTML(events)}
                        </div>
                    </div>
                    `;
                } catch(e) {
                    console.error("Error parsing timeline JSON:", e);
                }
            }

            // Markdown link and plain URL parsing
            const linkRegex = /\[([^\]]+)\]\(([^)]+)\)|(https?:\/\/[^\s]+)/g;
            let formattedContent = content.replace(linkRegex, function(match, mdText, mdUrl, plainUrl) {
                const isMarkdown = !!mdText && !!mdUrl;
                const url = isMarkdown ? mdUrl : plainUrl;
                let text = isMarkdown ? mdText : url;
                
                if (!isMarkdown && url.toLowerCase().includes('apply')) {
                    text = "Apply Here";
                } else if (!isMarkdown) {
                    text = "Visit Link";
                }
                
                return '<a href="' + url + '" target="_blank" rel="noopener noreferrer" class="md-link">' + text + '</a>';
            });
            return formattedContent;
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
                    btn.style.border = 'none';
                    btn.style.backgroundColor = '#2563eb';
                    btn.style.color = '#fff';
                    btn.style.boxShadow = '0 4px 6px rgba(37,99,235,0.2)';
                } else {
                    btn.style.border = '1px solid #d1d5db';
                    btn.style.backgroundColor = '#fff';
                    btn.style.color = '#4b5563';
                    btn.style.boxShadow = 'none';
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
                contentDiv.innerHTML = '<p style="color: #6b7280; font-size: 14px; font-style: italic;">No events found for this filter.</p>';
            } else {
                contentDiv.innerHTML = generateTimelineHTML(filteredEvents);
            }
        };

        function generateTimelineHTML(events) {
            return events.map((ev) => `
                <div style="margin-bottom: 28px; position: relative;">
                    <div style="position: absolute; left: -32.5px; top: 4px; width: 16px; height: 16px; background-color: #2563eb; border-radius: 50%; border: 3px solid #fff; box-shadow: 0 0 0 1px #e5e7eb;"></div>
                    <span style="display: inline-block; background-color: #eff6ff; color: #1d4ed8; font-size: 12px; font-weight: bold; padding: 4px 10px; border-radius: 12px; margin-bottom: 8px;">${ev.year}</span>
                    <div style="background-color: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                        <h4 style="margin: 0 0 4px 0; font-size: 16px; color: #111827; font-weight: bold;">${ev.title}</h4>
                        <p style="margin: 0 0 10px 0; font-size: 13px; color: #6b7280; font-weight: 500;">${ev.date}</p>
                        <p style="margin: 0 0 16px 0; font-size: 14px; color: #4b5563; line-height: 1.5;">${ev.desc}</p>
                        <a href="${ev.link}" target="_blank" rel="noopener noreferrer" style="display: inline-flex; align-items: center; color: #2563eb; text-decoration: none; font-weight: 600; font-size: 14px;">
                            ${ev.linkText} <span style="margin-left: 4px; font-size: 16px;">→</span>
                        </a>
                    </div>
                </div>
            `).join('');
        }

        function addMessage(role, content) {
            const wrapper = document.createElement('div');
            wrapper.className = `message-wrapper ${role}`;
            
            const messageEl = document.createElement('div');
            messageEl.className = `message ${role}`;
            
            messageEl.innerHTML = renderMessageContent(content);
            
            wrapper.appendChild(messageEl);
            chatMessages.appendChild(wrapper);
            scrollToBottom();
        }

        function showTyping() {
            const wrapper = document.createElement('div');
            wrapper.className = 'message-wrapper bot typing-wrapper';
            wrapper.innerHTML = `
                <div class="typing-indicator">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            `;
            chatMessages.appendChild(wrapper);
            scrollToBottom();
        }

        function hideTyping() {
            const typing = chatMessages.querySelector('.typing-wrapper');
            if(typing) typing.remove();
        }

        // Generate a unique session ID for context tracking
        const sessionId = localStorage.getItem("chatSessionId") || crypto.randomUUID();
        localStorage.setItem("chatSessionId", sessionId);

        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const userMsg = chatInput.value.trim();
            if (!userMsg || isLoading) return;

            // User Message
            addMessage('user', userMsg);
            chatInput.value = "";
            sendButton.disabled = true;
            isLoading = true;
            
            showTyping();

            try {
                // Hitting the FastAPI backend directly on port 8000 via .env config
                const response = await fetch(BACKEND_API_URL + "/ask", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ question: userMsg, session_id: sessionId }),
                });

                if (!response.ok) {
                    throw new Error("Failed to communicate with the server.");
                }

                const data = await response.json();
                hideTyping();
                addMessage('bot', data.answer || "I'm sorry, I don't have enough information to answer that question accurately. Please contact Opti Matrix for more information.");
            } catch (error) {
                console.error("Error fetching response:", error);
                hideTyping();
                addMessage('bot', "I'm sorry, I don't have enough information to answer that question accurately. Please contact Opti Matrix for more information.");
            } finally {
                isLoading = false;
                if(chatInput.value.trim()) sendButton.disabled = false;
            }
        });

        // Initialize with default greeting
        addMessage('bot', "Hello! I am the OptiMatrix AI assistant. You can ask me about our services, location, or general company information.");
    </script>
</body>
</html>