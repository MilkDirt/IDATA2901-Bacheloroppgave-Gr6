/**
 * App.jsx
 *
 * Root component of the application.
 * Checks if the user is logged in and either shows
 * the login page or the main chat interface.
 */

import React, { useState, useRef } from "react";
import Sidebar from "./components/sideBar";
import ChatPanel from "./components/ChatPanel";
import QueryPanel from "./components/QueryPanel";
import LoginPage from "./components/LoginPage";
import { useAuth } from "./hooks/useAuth";
import "./Styles/global.css";

function App() {
    const { token, user, authError, authLoading, login, register, logout, isLoggedIn } = useAuth();

    const [messages, setMessages] = useState({});
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [activeConversationId, setActiveConversationId] = useState(null);
    const [activeProjectId, setActiveProjectId] = useState(null);
    const [showForm, setShowForm] = useState(false);
    const [formData, setFormData] = useState({
        adresse: "",
        gnr: "",
        bnr: "",
        kommune: "",
        tiltakstype: "",
        bra: "",
        bya: "",
        hoyde: "",
        nabovarsel: false
    });

    const messagesEndRef = useRef(null);

    // ── Auth gate ─────────────────────────────────────────
    // If user is not logged in, show the login page instead
    if (!isLoggedIn) {
        return (
            <LoginPage
                onLogin={login}
                onRegister={register}
                authError={authError}
                authLoading={authLoading}
            />
        );
    }

    // ── Send message
    const sendMessage = async () => {
        if (!input.trim()) return;

        const userMessage = { role: "user", content: input };
        const conversationKey = activeConversationId || "new";

        setMessages(prev => ({
            ...prev,
            [conversationKey]: [...(prev[conversationKey] || []), userMessage]
        }));

        setLoading(true);

        try {
            const response = await fetch("http://127.0.0.1:8000/ask", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    question: input,
                    conversation_id: activeConversationId,
                    project_id: activeProjectId
                })
            });

            const data = await response.json();

            // update the active conversation ID in new conversation
            if (!activeConversationId && data.conversation_id) {
                setActiveConversationId(data.conversation_id);
                setMessages(prev => ({
                    ...prev,
                    [data.conversation_id]: [...(prev["new"] || []), {
                        role: "assistant",
                        content: data.answer,
                        sources: data.sources || []
                    }],
                    new: undefined
                }));
            } else {
                setMessages(prev => ({
                    ...prev,
                    [conversationKey]: [
                        ...(prev[conversationKey] || []),
                        {
                            role: "assistant",
                            content: data.answer,
                            sources: data.sources || []
                        }
                    ]
                }));
            }

        } catch (error) {
            console.error("Error:", error);
        }

        setInput("");
        setLoading(false);
    };

    // ── Generate application
    const generateApplication = async () => {
        setLoading(true);
        try {
            const response = await fetch("http://127.0.0.1:8000/generate-application", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            const conversationKey = activeConversationId || "new";

            setMessages(prev => ({
                ...prev,
                [conversationKey]: [
                    ...(prev[conversationKey] || []),
                    { role: "assistant", content: data.application_text }
                ]
            }));

            setShowForm(false);
        } catch (error) {
            console.error("Error:", error);
        }
        setLoading(false);
    };

    return (
        <div className="app" style={{ display: "flex" }}>
            <Sidebar
                token={token}
                user={user}
                onLogout={logout}
                activeConversationId={activeConversationId}
                setActiveConversationId={setActiveConversationId}
                setMessages={setMessages}
                activeProjectId={activeProjectId}
                setActiveProjectId={setActiveProjectId}
            />

            <ChatPanel
                activeProject={activeConversationId || "new"}
                input={input}
                setInput={setInput}
                messages={messages[activeConversationId || "new"] || []}
                loading={loading}
                sendMessage={sendMessage}
                messagesEndRef={messagesEndRef}
                setShowForm={setShowForm}
            />

            <QueryPanel
                show={showForm}
                setShow={setShowForm}
                formData={formData}
                setFormData={setFormData}
                generateApplication={generateApplication}
            />
        </div>
    );
}

export default App;