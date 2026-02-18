import React from "react";

export default function ChatPanel({
                                      input,
                                      setInput,
                                      messages,
                                      loading,
                                      sendMessage,
                                      messagesEndRef,
                                  }) {
    return (
        <div className={`main ${messages.length === 0 ? "main--empty" : "main--active"}`}>
            <div className="chat-col">
                <div className="chat-container">
                    {messages.map((msg, i) => (
                        <div
                            key={i}
                            className={`message ${msg.role === "user" ? "user" : "assistant"}`}
                        >
                            <div className="message-content">{msg.content}</div>

                            {msg.role === "assistant" &&
                                msg.sources &&
                                msg.sources.length > 0 && (
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

                <form
                    className="input-container"
                    onSubmit={(e) => {
                        e.preventDefault();
                        sendMessage();
                    }}
                >
          <textarea
              className="chat-input"
              placeholder="Ask something..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                  // Enter sends, Shift+Enter newline
                  if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage();
                  }
              }}
          />

                    <button type="submit" disabled={loading}>
                        Send
                    </button>
                </form>
            </div>
        </div>
    );
}
