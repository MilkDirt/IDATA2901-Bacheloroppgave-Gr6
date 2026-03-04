
import React, { useRef, useEffect } from "react";
import sendIcon from "../assets/button.png";
import "../Styles/chat.css";

export default function ChatPanel({ input, setInput, messages, loading, sendMessage, messagesEndRef, setShowForm }) {
    const textareaRef = useRef(null);

    const resizeTextarea = () => {
        const el = textareaRef.current;
        if (!el) return;
        el.style.height = "auto";
        el.style.height = `${el.scrollHeight}px`;
    };

    // Set initial height on mount
    useEffect(resizeTextarea, []);

    // Scroll to latest message
    useEffect(() => {
        messagesEndRef?.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    const handleSend = () => {
        if (!input.trim() || loading) return;
        sendMessage();
        setInput("");
        resizeTextarea();
    };

    return (
        <div className={`main ${messages.length === 0 ? "main--empty" : "main--active"}`}>
            <div className="chat-col">

                <div className="chat-container">
                    {messages.map((msg, i) => (
                        <div key={i} className={`message ${msg.role}`}>
                            <div className="message-content">{msg.content}</div>

                            {msg.role === "assistant" && msg.sources?.length > 0 && (
                                <div className="sources">
                                    <strong>Kilder:</strong>
                                    <ul>
                                        {msg.sources.map((source, j) => (
                                            <li key={j}>{source.source_file} (side {source.page})</li>
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
                <button type="button" className="form-btn" onClick={() => setShowForm(true)}>+ Søknad</button>

                <form className="input-container" onSubmit={(e) => { e.preventDefault(); handleSend(); }}>
                    <div className="input-wrapper">
                        <textarea
                            ref={textareaRef}
                            className="chat-input"
                            placeholder="Ask something..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onInput={resizeTextarea}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSend();
                                }
                            }}
                        />
                        <button type="submit" className="send-btn" disabled={loading || !input.trim()}>
                            <img src={sendIcon} alt="Send" className="send-icon" />
                        </button>
                    </div>
                </form>

            </div>
        </div>
    );
}