"use client";

import { useState, useRef, useEffect } from "react";

type Message = {
  id: string;
  role: "user" | "bot";
  content: string;
};

type TimelineEvent = {
  year: string;
  title: string;
  date: string;
  desc: string;
  link: string;
  linkText: string;
};

const TimelineView = ({ events }: { events: TimelineEvent[] }) => {
  const [filter, setFilter] = useState("All");

  let filteredEvents = events;
  if (filter === "2010-2012") {
    filteredEvents = events.filter(e => ["2010", "2011", "2012"].includes(e.year));
  } else if (filter === "2013-2015") {
    filteredEvents = events.filter(e => ["2013", "2014", "2015"].includes(e.year));
  } else if (filter === "2016-2018") {
    filteredEvents = events.filter(e => ["2016", "2017", "2018"].includes(e.year));
  } else if (filter === "Major Achievements") {
    filteredEvents = events.filter(e =>
      e.title.toLowerCase().includes("achieve") ||
      e.title.includes("300th") ||
      e.title.toLowerCase().includes("google") ||
      e.title.includes("Biggest") ||
      e.title.toLowerCase().includes("award")
    );
  }

  return (
    <div style={{ width: '100%', maxWidth: '600px', fontFamily: 'sans-serif', margin: '10px 0' }}>
      <h3 style={{ margin: '0 0 16px 0', fontSize: '22px', color: '#111827', display: 'flex', alignItems: 'center', gap: '8px' }}>
        🚀 OPTI MATRIX JOURNEY
      </h3>

      {/* Quick Action Buttons */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '24px' }}>
        {["All", "2010-2012", "2013-2015", "2016-2018", "Major Achievements"].map(btn => (
          <button
            key={btn}
            onClick={() => setFilter(btn)}
            style={{
              padding: '6px 14px',
              borderRadius: '20px',
              border: filter === btn ? 'none' : '1px solid #d1d5db',
              backgroundColor: filter === btn ? '#2563eb' : '#fff',
              color: filter === btn ? '#fff' : '#4b5563',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: filter === btn ? '0 4px 6px rgba(37,99,235,0.2)' : 'none'
            }}
          >
            {btn === "All" ? "🚀 Full Journey" : (btn === "Major Achievements" ? "🏆 Major Achievements" : btn)}
          </button>
        ))}
      </div>

      {/* Timeline UI */}
      <div style={{ position: 'relative', borderLeft: '3px solid #e5e7eb', marginLeft: '16px', paddingLeft: '24px' }}>
        {filteredEvents.map((ev, idx) => (
          <div key={idx} style={{ marginBottom: '28px', position: 'relative' }}>
            {/* Timeline Dot */}
            <div style={{
              position: 'absolute',
              left: '-32.5px',
              top: '4px',
              width: '16px',
              height: '16px',
              backgroundColor: '#2563eb',
              borderRadius: '50%',
              border: '3px solid #fff',
              boxShadow: '0 0 0 1px #e5e7eb'
            }} />

            <span style={{ display: 'inline-block', backgroundColor: '#eff6ff', color: '#1d4ed8', fontSize: '12px', fontWeight: 'bold', padding: '4px 10px', borderRadius: '12px', marginBottom: '8px' }}>
              {ev.year}
            </span>

            <div style={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '16px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)' }}>
              <h4 style={{ margin: '0 0 4px 0', fontSize: '16px', color: '#111827', fontWeight: 'bold' }}>{ev.title}</h4>
              <p style={{ margin: '0 0 10px 0', fontSize: '13px', color: '#6b7280', fontWeight: '500' }}>{ev.date}</p>
              <p style={{ margin: '0 0 16px 0', fontSize: '14px', color: '#4b5563', lineHeight: '1.5' }}>{ev.desc}</p>

              <a href={ev.link} target="_blank" rel="noopener noreferrer" style={{
                display: 'inline-flex',
                alignItems: 'center',
                color: '#2563eb',
                textDecoration: 'none',
                fontWeight: '600',
                fontSize: '14px'
              }}>
                {ev.linkText} <span style={{ marginLeft: '4px', fontSize: '16px' }}>→</span>
              </a>
            </div>
          </div>
        ))}
        {filteredEvents.length === 0 && (
          <p style={{ color: '#6b7280', fontSize: '14px', fontStyle: 'italic' }}>No events found for this filter.</p>
        )}
      </div>
    </div>
  );
};

export default function ChatSystem() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "bot",
      content: "Hello! I am the OptiMatrix AI assistant. You can ask me about our services, location, or general company information.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const renderMessage = (content: string) => {
    // Check for special Profile Card formatting
    if (content.startsWith("PROFILE_CARD:")) {
      const parts = content.split(":");
      const dataStr = parts.slice(1).join(":"); // rejoin in case of colons in URL
      const data = dataStr.split("|");
      if (data.length === 5) {
        const [name, title, company, linkedin, image] = data;
        return (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', backgroundColor: '#ffffff', padding: '24px', borderRadius: '16px', boxShadow: '0 10px 25px rgba(0,0,0,0.1)', color: '#333', maxWidth: '300px', border: '1px solid #e5e7eb', margin: '10px 0' }}>
            <img src={image} alt={name} style={{ width: '140px', height: '140px', borderRadius: '50%', objectFit: 'cover', border: '4px solid #2563eb', padding: '4px', backgroundColor: '#fff', boxShadow: '0 4px 10px rgba(37,99,235,0.2)' }} />
            <h3 style={{ margin: '16px 0 4px 0', fontSize: '20px', fontWeight: 'bold', color: '#111827' }}>{name}</h3>
            <p style={{ margin: '0 0 6px 0', fontWeight: '600', color: '#3b82f6', fontSize: '15px' }}>{title}</p>
            <p style={{ margin: '0 0 20px 0', fontSize: '14px', color: '#6b7280', fontWeight: '500' }}>{company}</p>
            <a href={linkedin} target="_blank" rel="noopener noreferrer" style={{ padding: '10px 20px', backgroundColor: '#0a66c2', color: 'white', textDecoration: 'none', borderRadius: '8px', fontWeight: '600', fontSize: '15px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', width: '100%', transition: 'all 0.2s ease', boxShadow: '0 4px 6px rgba(10,102,194,0.2)' }}>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M0 1.146C0 .513.526 0 1.175 0h13.65C15.474 0 16 .513 16 1.146v13.708c0 .633-.526 1.146-1.175 1.146H1.175C.526 16 0 15.487 0 14.854zm4.943 12.248V6.169H2.542v7.225zm-1.2-8.212c.837 0 1.358-.554 1.358-1.248-.015-.709-.52-1.248-1.342-1.248S2.4 3.226 2.4 3.934c0 .694.521 1.248 1.327 1.248zm4.908 8.212V9.359c0-.216.016-.432.08-.586.173-.431.568-.878 1.232-.878.869 0 1.216.662 1.216 1.634v3.865h2.401V9.25c0-2.22-1.184-3.252-2.764-3.252-1.274 0-1.845.7-2.165 1.193v.025h-.016l.016-.025V6.169h-2.4c.03.678 0 7.225 0 7.225z" /></svg>
              View LinkedIn Profile
            </a>
          </div>
        );
      }
    }

    // Check for special Timeline formatting
    if (content.startsWith("TIMELINE_DATA:")) {
      const jsonStr = content.substring("TIMELINE_DATA:".length);
      try {
        const events = JSON.parse(jsonStr);
        return <TimelineView events={events} />;
      } catch (e) {
        console.error("Error parsing timeline JSON:", e);
      }
    }

    // Basic markdown link parser for [text](url) AND plain URLs
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)|(https?:\/\/[^\s]+)/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = linkRegex.exec(content)) !== null) {
      // Add text before the link
      if (match.index > lastIndex) {
        parts.push(content.substring(lastIndex, match.index));
      }
      
      const isMarkdown = match[1] && match[2];
      const url = isMarkdown ? match[2] : match[3];
      let text = isMarkdown ? match[1] : url;
      
      // If it's a plain URL and contains 'apply', make it look like an Apply button
      if (!isMarkdown && url.toLowerCase().includes('apply')) {
        text = "Apply Here";
      } else if (!isMarkdown) {
        text = "Visit Link";
      }

      // Add the link as a button/anchor
      parts.push(
        <a
          key={`link-${match.index}`}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: "inline-block",
            marginTop: "10px",
            marginBottom: "6px",
            marginRight: "8px",
            padding: "8px 16px",
            backgroundColor: "#2563eb",
            color: "white",
            textDecoration: "none",
            borderRadius: "6px",
            fontWeight: "500",
            fontSize: "14px",
            boxShadow: "0 2px 4px rgba(37, 99, 235, 0.2)",
            border: "1px solid #1d4ed8",
            wordBreak: "break-word",
            textAlign: "center"
          }}
        >
          {text}
        </a>
      );
      lastIndex = linkRegex.lastIndex;
    }
    // Add remaining text
    if (lastIndex < content.length) {
      parts.push(content.substring(lastIndex));
    }

    // If no links were found, just return the content
    if (parts.length === 0) return content;

    return parts.map((part, i) => <span key={i}>{part}</span>);
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = input.trim();
    setInput("");

    const newUserMsg: Message = { id: Date.now().toString(), role: "user", content: userMsg };
    setMessages((prev) => [...prev, newUserMsg]);
    setIsLoading(true);

    try {
      // Connect to the Next.js API backend route (proxies to FastAPI service)
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: userMsg }),
      });

      if (!response.ok) {
        throw new Error("Failed to communicate with the server.");
      }

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "bot",
          content: data.answer || "I'm sorry, I don't have enough information to answer that question accurately. Please contact Opti Matrix for more information.",
        },
      ]);
    } catch (error) {
      console.error("Error fetching response:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "bot",
          content: "Sorry, I am having trouble connecting to the server. Please verify that the application backend is active.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>Company AI Assistant</h1>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', marginTop: '4px' }}>
          <div style={{ width: '8px', height: '8px', backgroundColor: '#22c55e', borderRadius: '50%' }}></div>
          <p style={{ margin: 0 }}>Online | Ask me anything</p>
        </div>
      </div>

      <div className="chat-messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-wrapper ${msg.role}`}>
            <div className={`message ${msg.role}`} style={{ whiteSpace: "pre-wrap" }}>
              {renderMessage(msg.content)}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message-wrapper bot">
            <div className="typing-indicator">
              <div className="dot"></div>
              <div className="dot"></div>
              <div className="dot"></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <form onSubmit={handleSubmit} className="chat-form">
          <input
            type="text"
            className="chat-input"
            placeholder="Type your question here..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
          />
          <button type="submit" className="send-button" disabled={!input.trim() || isLoading}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
