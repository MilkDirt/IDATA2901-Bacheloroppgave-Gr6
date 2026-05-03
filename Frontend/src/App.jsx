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

const API_BASE = "http://127.0.0.1:8000";

function App() {
    const { token, user, authError, authLoading, login, register, logout, isLoggedIn } = useAuth();

    const [messages, setMessages] = useState({});
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [activeConversationId, setActiveConversationId] = useState(null);
    const [activeProjectId, setActiveProjectId] = useState(null);
    const [showForm, setShowForm] = useState(false);
    const [formData, setFormData] = useState({
        typeAnlegg: "",
        typeAnleggAnnet: "",
        behoveBeskrivelse: "",
        antallBrukere: "",
        kommunalePlanerBeskrivelse: "",
        avstandAndreAnlegg: "",
        avstandKm: "",
        kommune: "",
        innbyggertall: "",
        befolkningINeromraade: "",
        brukerBeskrivelse: "",
        idrettslag: "",
        antallMedlemmer: "",
        driftsansvarlig: "",
        driftsmodell: "",
    });
    const [showKostnadsoverlag, setShowKostnadsoverlag] = useState(false);
    const [kostnadsoverlagData, setKostnadsoverlagData] = useState({
        prosjektNavn: "", 
        kommune: "", 
        typeAnlegg: "", 
        anleggStorrelse: "",
        grunnarb: "", 
        dreneringKr: "", 
        aktivitetsflateKr: "",
        gjerdeUtstyrKr: "", 
        garderodeKr: "", 
        lysanleggKr: "",
        andreKostnaderTilskudd: "",
        tribuneKr: "", 
        parkeringKr: "", 
        avgifterKr: "", 
        andreKostnaderIkke: "",
        dugnadTimer: "", 
        dugnadTimepris: "", 
        dugnadBeskrivelse: "",
        spillemidlerKr: "", 
        kommunaltTilskuddKr: "", 
        egneMiddlerKr: "",
        andreTilskuddKr: "", 
        lanKr: "",
    });

    const messagesEndRef = useRef(null);

    /** Show login/register page if not authenticated */
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

    /** Send user message to /ask and append the AI response */
    const sendMessage = async () => {
        if (!input.trim()) return;

        const conversationKey = activeConversationId || "new";

        setMessages(prev => ({
            ...prev,
            [conversationKey]: [...(prev[conversationKey] || []), { role: "user", content: input }]
        }));
        setLoading(true);

        try {
            const response = await fetch(`${API_BASE}/ask`, {
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
            const aiMessage = { role: "assistant", content: data.answer, sources: data.sources || [] };

            if (!activeConversationId && data.conversation_id) {
                /** First message — move messages from "new" key to real conversation ID */
                setActiveConversationId(data.conversation_id);
                setMessages(prev => ({
                    ...prev,
                    [data.conversation_id]: [...(prev["new"] || []), aiMessage],
                    new: undefined
                }));
            } else {
                setMessages(prev => ({
                    ...prev,
                    [conversationKey]: [...(prev[conversationKey] || []), aiMessage]
                }));
            }
        } catch (error) {
            console.error("sendMessage error:", error);
        }

        setInput("");
        setLoading(false);
    };

    /** Submit form data to /generate-application and show result in chat */
    const generateApplication = async () => {
    setLoading(true);
    try {
        const response = await fetch(`${API_BASE}/api/generate-pdf`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            console.error("PDF generation failed:", err.detail);
            return;
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `behovsvurdering_${formData.kommune || "dokument"}.docx`;
        a.click();
        URL.revokeObjectURL(url);
        setShowForm(false);
    } catch (error) {
        console.error("generateApplication error:", error);
    }
    setLoading(false);
};

/** Generate function for kostnadsoverslag */
    const generateKostnadsoverlag = async () => {
    setLoading(true);
    try {
        const response = await fetch(`${API_BASE}/api/generate-kostnadsoverlag`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(kostnadsoverlagData)
        });
 
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            console.error("Kostnadsoverslag generation failed:", err.detail);
            return;
        }
 
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `kostnadsoverslag_${kostnadsoverlagData.prosjektNavn || "prosjekt"}.docx`;
        a.click();
        URL.revokeObjectURL(url);
        setShowKostnadsoverlag(false);
    } catch (error) {
        console.error("generateKostnadsoverlag error:", error);
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
                kostnadsoverlagData={kostnadsoverlagData}
                setKostnadsoverlagData={setKostnadsoverlagData}
                generateApplication={generateApplication}
                generateKostnadsoverlag={generateKostnadsoverlag}
            />
        </div>
    );
}

export default App;