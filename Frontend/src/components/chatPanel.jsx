import React, { useRef, useEffect } from "react";
import sendIcon from "../assets/button.png";
import soknadIcon from "../assets/soknad-icon1.png";
import multiconsultLogo from "../assets/multiconsult-logo.png";
import "../Styles/chat.css";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function ChatPanel({ input, setInput, messages, loading, sendMessage, messagesEndRef, setShowForm }) {
    const textareaRef = useRef(null);

    const resizeTextarea = () => {
        const el = textareaRef.current;
        if (!el) return;
        el.style.height = "auto";
        el.style.height = `${el.scrollHeight}px`;
    };

    useEffect(resizeTextarea, []);

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
            <img src={multiconsultLogo} alt="Multiconsult" className="multiconsult-logo" />
            <div className="chat-col">

                {/* ── Welcome screen (empty state only) ── */}
                {messages.length === 0 && (
                    <div className="welcome">
                        <img src={multiconsultLogo} alt="Multiconsult" className="welcome-logo" />
                        <h1 className="welcome-title">Hva kan jeg hjelpe deg med?</h1>
                        <p className="welcome-subtitle">Still spørsmål om dine prosjekter, bestemmelser og søknader.</p>
                        <div className="welcome-suggestions">
                            <button className="suggestion-chip" onClick={() => { setInput("Hva er kravene for spillemidler?"); }}>
                                Hva er kravene for spillemidler?
                            </button>
                            <button className="suggestion-chip" onClick={() => { setInput("Hvilke lover gjelder for byggesaker?"); }}>
                                Hvilke lover gjelder for byggesaker?
                            </button>
                            <button className="suggestion-chip" onClick={() => { setInput("Hva er en behovsvurdering?"); }}>
                                Hva er en behovsvurdering?
                            </button>
                        </div>
                    </div>
                )}

                <div className="chat-container">
                    {messages.map((msg, i) => (
                        <div key={i} className={`message ${msg.role}`}>
                            <div className="message-content">
                                {msg.role === "assistant"
                                    ?<ReactMarkdown
                                        remarkPlugins={[remarkGfm]}
                                        components={{
                                            // Remove extra <p> wrapping inside list items
                                            li: ({children}) => <li>{children}</li>,
                                            p: ({children, node}) => {
                                                // If <p> is inside a list item render as span not block
                                                const parent = node?.position;
                                                return <p style={{margin: "0 0 4px 0"}}>{children}</p>;
                                            },
                                            ul: ({children}) => <ul style={{paddingLeft: "20px", margin: "4px 0"}}>{children}</ul>,
                                            ol: ({children}) => <ol style={{paddingLeft: "20px", margin: "4px 0"}}>{children}</ol>,
                                            h1: ({children}) => <h1 style={{margin: "8px 0 2px 0"}}>{children}</h1>,
                                            h2: ({children}) => <h2 style={{margin: "8px 0 2px 0"}}>{children}</h2>,
                                            h3: ({children}) => <h3 style={{margin: "6px 0 2px 0"}}>{children}</h3>,
                                        }}
                                    >
                                        {msg.content}
                                    </ReactMarkdown>
                                    : msg.content
                                }
                            </div>

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

                {/* Input row with søknad icon on the left */}
                <div className="input-row">

                    {/* Søknad icon — toggles the panel open/closed */}
                    <button
                        type="button"
                        className="soknad-icon-btn"
                        onClick={() => setShowForm(prev => !prev)}
                        title="Åpne/lukk søknadsskjema"
                    >
                        <img src={soknadIcon} alt="Søknad" className="soknad-icon" />
                    </button>

                    <form
                        className="input-container"
                        onSubmit={(e) => { e.preventDefault(); handleSend(); }}
                    >
                        <div className="input-wrapper">
                            <textarea
                                ref={textareaRef}
                                className="chat-input"
                                placeholder="Still et spørsmål..."
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
        </div>
    );
}