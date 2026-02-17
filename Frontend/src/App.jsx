import React, { useState, useRef, useEffect } from "react";
import "./styles/global.css";

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll til bunnen
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      role: "user",
      content: input
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          question: input
        })
      });

      const data = await response.json();

      const aiMessage = {
        role: "assistant",
        content: data.answer,
        sources: data.sources || []
      };

      setMessages(prev => [...prev, aiMessage]);

    } catch (error) {
      console.error("Feil:", error);
    }

    setLoading(false);
  };

  return (
    <div className="app">
      <div className="sidebar">
        <h3>Projects</h3>
      </div>

      <div className="main">

        <div className="chat-container">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`message ${msg.role === "user" ? "user" : "assistant"}`}
            >
              <div className="message-content">
                {msg.content}
              </div>

              {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                <div className="sources">
                  <strong>Kilder:</strong>
                  <ul>
                    {msg.sources.map((source, index) => (
                      <li key={index}>
                        {source.source_file} (side {source.page})
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="message assistant">
              <div className="message-content">Skriver...</div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <input
            className="chat-input"
            placeholder="Ask something..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                sendMessage();
              }
            }}
          />
          <button onClick={sendMessage} disabled={loading}>
            Send
          </button>
        </div>

      </div>
    </div>
  );
}

export default App;
