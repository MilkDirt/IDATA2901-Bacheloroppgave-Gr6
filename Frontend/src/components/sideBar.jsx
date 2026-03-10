/**
 * sideBar.jsx
 *
 * Sidebar component that displays the user's conversation history.
 * Fetches conversations from the backend on mount and when a new
 * conversation is created. Allows the user to switch between
 * conversations and start new ones.
 */

import React, { useState, useEffect } from "react";
import "../Styles/sideBar.css";

const API_BASE = "http://127.0.0.1:8000";

export default function Sidebar({
                                    token,
                                    user,
                                    onLogout,
                                    activeConversationId,
                                    setActiveConversationId,
                                    setMessages,
                                }) {
    const [conversations, setConversations] = useState([]);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

    /**
     * Fetch all conversations for the logged in user.
     * Called on mount and whenever activeConversationId changes
     * so the sidebar updates after a new conversation is created.
     */
    useEffect(() => {
        fetchConversations();
    }, [activeConversationId]);

    const fetchConversations = async () => {
        try {
            const response = await fetch(`${API_BASE}/conversations/`, {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });
            const data = await response.json();
            setConversations(data);
        } catch (error) {
            console.error("Failed to fetch conversations:", error);
        }
    };

    /**
     * Load a conversation's messages when clicked in the sidebar.
     * Fetches all messages for that conversation and sets them in state.
     *
     * @param {number} conversationId - The conversation to load
     */
    const loadConversation = async (conversationId) => {
        try {
            const response = await fetch(
                `${API_BASE}/conversations/${conversationId}/messages`,
                {
                    headers: {
                        "Authorization": `Bearer ${token}`
                    }
                }
            );
            const data = await response.json();

            // Format messages to match the frontend message structure
            const formatted = data.map((msg) => ({
                role: msg.role === "ai" ? "assistant" : "user",
                content: msg.content,
                sources: msg.sources ? JSON.parse(msg.sources) : [],
            }));

            setMessages((prev) => ({
                ...prev,
                [conversationId]: formatted,
            }));

            setActiveConversationId(conversationId);
        } catch (error) {
            console.error("Failed to load conversation:", error);
        }
    };

    /**
     * Start a fresh new conversation.
     * Clears the active conversation so the next message creates a new one.
     */
    const handleNewChat = () => {
        setActiveConversationId(null);
        setMessages((prev) => ({ ...prev, new: [] }));
    };

    return (
        <div className={isSidebarOpen ? "sidebar" : "sidebar collapsed"}>

            {/* Collapse/expand toggle */}
            <button
                className="toggle-sidebar-btn"
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                title={isSidebarOpen ? "Skjul meny" : "Vis meny"}
            >
                ☰
            </button>

            {/* New chat button */}
            <div className="new-project-container">
                <button className="new-project-btn" onClick={handleNewChat}>
                    + Ny samtale
                </button>
            </div>

            {/* Conversation list */}
            <div className="projects-section">
                <h3>Samtaler</h3>

                <ul className="projects-list">
                    {conversations.length === 0 && (
                        <li style={{ color: "#888", fontSize: "13px", padding: "8px 0" }}>
                            Ingen samtaler ennå
                        </li>
                    )}
                    {conversations.map((conv) => (
                        <li
                            key={conv.id}
                            className={`project-item ${activeConversationId === conv.id ? "active" : ""}`}
                            onClick={() => loadConversation(conv.id)}
                        >
                            <span className="project-name">{conv.title}</span>
                        </li>
                    ))}
                </ul>
            </div>

            {/* User info and logout at the bottom */}
            <div style={{
                padding: "16px 20px",
                borderTop: "1px solid #333",
                marginTop: "auto",
            }}>
                <div style={{ fontSize: "13px", color: "#94a3b8", marginBottom: "8px" }}>
                    Innlogget som
                </div>
                <div style={{ fontSize: "14px", color: "#f1f5f9", marginBottom: "12px", fontWeight: "500" }}>
                    {user?.name}
                </div>
                <button
                    onClick={onLogout}
                    style={{
                        width: "100%",
                        padding: "8px",
                        background: "transparent",
                        border: "1px solid #444",
                        borderRadius: "6px",
                        color: "#94a3b8",
                        cursor: "pointer",
                        fontSize: "13px",
                        fontFamily: "Inter, system-ui, sans-serif",
                    }}
                >
                    Logg ut
                </button>
            </div>

        </div>
    );
}
