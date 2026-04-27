/**
 * Sidebar component that displays the user's projects and conversations.
 * - Projects group conversations together
 * - Conversations can also exist without a project
 * - Supports creating and deleting projects
 * - Supports deleting conversations
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
                                    activeProjectId,
                                    setActiveProjectId,
                                }) {
    const [conversations, setConversations] = useState([]);
    const [projects, setProjects] = useState([]);
    const [expandedProjects, setExpandedProjects] = useState({});
    const [projectConversations, setProjectConversations] = useState({});
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [newProjectName, setNewProjectName] = useState("");
    const [showNewProjectInput, setShowNewProjectInput] = useState(false);

    useEffect(() => {
        if (token) {
            fetchConversations();
            fetchProjects();
        }
    }, [activeConversationId, token]);

    // Re-fetch conversations for the active project when a new conversation is created
    useEffect(() => {
        if (token && activeProjectId && expandedProjects[activeProjectId]) {
            fetchProjectConversations(activeProjectId);
        }
    }, [activeConversationId, activeProjectId]);

    const fetchConversations = async () => {
        try {
            const response = await fetch(`${API_BASE}/conversations/`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!response.ok) return;
            const data = await response.json();
            const all = Array.isArray(data) ? data : [];
            setConversations(all.filter(c => !c.project_id));
        } catch (error) {
            console.error("Failed to fetch conversations:", error);
        }
    };

    const fetchProjects = async () => {
        try {
            const response = await fetch(`${API_BASE}/projects/`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!response.ok) return;
            const data = await response.json();
            setProjects(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error("Failed to fetch projects:", error);
        }
    };

    const fetchProjectConversations = async (projectId) => {
        try {
            const response = await fetch(
                `${API_BASE}/projects/${projectId}/conversations`,
                { headers: { "Authorization": `Bearer ${token}` } }
            );
            if (!response.ok) return;
            const data = await response.json();
            setProjectConversations(prev => ({
                ...prev,
                [projectId]: Array.isArray(data) ? data : []
            }));
        } catch (error) {
            console.error("Failed to fetch project conversations:", error);
        }
    };

    const toggleProject = (projectId) => {
        const isExpanded = expandedProjects[projectId];
        setExpandedProjects(prev => ({ ...prev, [projectId]: !isExpanded }));
        if (!isExpanded) fetchProjectConversations(projectId);
    };

    const createProject = async () => {
        if (!newProjectName.trim()) return;
        try {
            const response = await fetch(`${API_BASE}/projects/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ name: newProjectName })
            });
            if (!response.ok) return;
            const data = await response.json();
            setProjects(prev => [data, ...prev]);
            setNewProjectName("");
            setShowNewProjectInput(false);
        } catch (error) {
            console.error("Failed to create project:", error);
        }
    };

    const deleteProject = async (projectId, e) => {
        e.stopPropagation();

        try {
            const response = await fetch(`${API_BASE}/projects/${projectId}`, {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!response.ok) return;
            setProjects(prev => prev.filter(p => p.id !== projectId));
            if (activeProjectId === projectId) setActiveProjectId(null);
            fetchConversations();
        } catch (error) {
            console.error("Failed to delete project:", error);
        }
    };

    const loadConversation = async (conversationId) => {
        try {
            const response = await fetch(
                `${API_BASE}/conversations/${conversationId}/messages`,
                { headers: { "Authorization": `Bearer ${token}` } }
            );
            const data = await response.json();
            const formatted = data.map((msg) => ({
                role: msg.role === "ai" ? "assistant" : "user",
                content: msg.content,
                sources: msg.sources ? JSON.parse(msg.sources) : [],
            }));
            setMessages((prev) => ({ ...prev, [conversationId]: formatted }));
            setActiveConversationId(conversationId);
        } catch (error) {
            console.error("Failed to load conversation:", error);
        }
    };

    const deleteConversation = async (conversationId, e) => {
        e.stopPropagation();

        try {
            const response = await fetch(
                `${API_BASE}/conversations/${conversationId}`,
                {
                    method: "DELETE",
                    headers: { "Authorization": `Bearer ${token}` }
                }
            );
            if (!response.ok) return;
            setConversations(prev => prev.filter(c => c.id !== conversationId));
            setProjectConversations(prev => {
                const updated = { ...prev };
                for (const pid in updated) {
                    updated[pid] = updated[pid].filter(c => c.id !== conversationId);
                }
                return updated;
            });
            if (activeConversationId === conversationId) {
                setActiveConversationId(null);
            }
        } catch (error) {
            console.error("Failed to delete conversation:", error);
        }
    };

    const handleNewChat = (projectId = null) => {
        setActiveConversationId(null);
        setActiveProjectId(projectId);
        setMessages((prev) => ({ ...prev, new: [] }));
        // Auto-expand the project so new conversation appears immediately
        if (projectId) {
            setExpandedProjects(prev => ({ ...prev, [projectId]: true }));
            fetchProjectConversations(projectId);
        }
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
                <button className="new-project-btn" onClick={() => handleNewChat(null)}>
                    + Ny samtale
                </button>
            </div>

            {/* Projects + conversations */}
            <div className="projects-section">

                {/* Projects header */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <h3 style={{ margin: 0 }}>Prosjekter</h3>
                    <button
                        onClick={() => setShowNewProjectInput(!showNewProjectInput)}
                        style={{
                            background: "none", border: "none",
                            color: "#F47920", cursor: "pointer",
                            fontSize: "18px", lineHeight: 1,
                        }}
                        title="Nytt prosjekt"
                    >+</button>
                </div>

                {/* New project input */}
                {showNewProjectInput && (
                    <div style={{ display: "flex", gap: "6px", marginBottom: "10px", minWidth: 0 }}>
                        <input
                            value={newProjectName}
                            onChange={e => setNewProjectName(e.target.value)}
                            onKeyDown={e => e.key === "Enter" && createProject()}
                            placeholder="Prosjektnavn..."
                            autoFocus
                            style={{
                                flex: 1,
                                minWidth: 0,
                                background: "rgba(255,255,255,0.06)",
                                border: "1px solid rgba(255,255,255,0.12)",
                                borderRadius: "6px", padding: "6px 10px",
                                color: "#e5e7eb", fontSize: "12px",
                                fontFamily: "Inter, system-ui, sans-serif",
                            }}
                        />
                        <button
                            onClick={createProject}
                            style={{
                                background: "#F47920", border: "none",
                                borderRadius: "6px", padding: "6px 10px",
                                color: "#fff", cursor: "pointer",
                                fontSize: "12px", fontWeight: "600",
                                flexShrink: 0,
                            }}
                        >OK</button>
                    </div>
                )}

                {/* Project list */}
                {projects.length === 0 && (
                    <div className="empty-state" style={{ marginBottom: "16px" }}>
                        Ingen prosjekter ennå
                    </div>
                )}

                {projects.map(project => (
                    <div key={project.id} style={{ marginBottom: "4px" }}>
                        <div
                            className="project-item"
                            onClick={() => toggleProject(project.id)}
                            style={{ fontWeight: "500" }}
                        >
                            <span style={{ marginRight: "6px", fontSize: "11px" }}>
                                {expandedProjects[project.id] ? "▼" : "▶"}
                            </span>
                            <span className="project-name"> {project.name}</span>
                            <button
                                className="delete-conversation-btn"
                                onClick={(e) => deleteProject(project.id, e)}
                                title="Slett prosjekt"
                            >✕</button>
                        </div>

                        {expandedProjects[project.id] && (
                            <div style={{ marginLeft: "16px" }}>
                                <button
                                    onClick={() => handleNewChat(project.id)}
                                    style={{
                                        width: "100%", background: "none",
                                        border: "1px dashed #444", borderRadius: "5px",
                                        color: "#888", cursor: "pointer",
                                        padding: "5px", fontSize: "12px",
                                        marginBottom: "4px",
                                        fontFamily: "Inter, system-ui, sans-serif",
                                    }}
                                >
                                    + Ny samtale
                                </button>
                                {(projectConversations[project.id] || []).length === 0 ? (
                                    <div className="empty-state">Ingen samtaler ennå</div>
                                ) : (
                                    <ul className="projects-list">
                                        {(projectConversations[project.id] || []).map(conv => (
                                            <li
                                                key={conv.id}
                                                className={`project-item ${activeConversationId === conv.id ? "active" : ""}`}
                                                onClick={() => loadConversation(conv.id)}
                                            >
                                                <span className="project-name">{conv.title}</span>
                                                <button
                                                    className="delete-conversation-btn"
                                                    onClick={(e) => deleteConversation(conv.id, e)}
                                                    title="Slett samtale"
                                                >✕</button>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                        )}
                    </div>
                ))}

                {/* Divider */}
                <div style={{ borderTop: "1px solid #2a2a2a", margin: "12px 0" }} />

                {/* Conversations without project */}
                <h3>Samtaler</h3>
                <ul className="projects-list">
                    {conversations.length === 0 && (
                        <li className="empty-state">Ingen samtaler ennå</li>
                    )}
                    {conversations.map((conv) => (
                        <li
                            key={conv.id}
                            className={`project-item ${activeConversationId === conv.id ? "active" : ""}`}
                            onClick={() => loadConversation(conv.id)}
                        >
                            <span className="project-name">{conv.title}</span>
                            <button
                                className="delete-conversation-btn"
                                onClick={(e) => deleteConversation(conv.id, e)}
                                title="Slett samtale"
                            >✕</button>
                        </li>
                    ))}
                </ul>
            </div>

            {/* User info and logout — hidden when collapsed */}
            <div className="sidebar-user">
                <div style={{ fontSize: "13px", color: "#94a3b8", marginBottom: "4px" }}>
                    Innlogget som
                </div>
                <div style={{ fontSize: "14px", color: "#f1f5f9", marginBottom: "12px", fontWeight: "500" }}>
                    {user?.name}
                </div>
                <button
                    onClick={onLogout}
                    style={{
                        width: "100%", padding: "8px",
                        background: "transparent", border: "1px solid #444",
                        borderRadius: "6px", color: "#94a3b8",
                        cursor: "pointer", fontSize: "13px",
                        fontFamily: "Inter, system-ui, sans-serif",
                    }}
                >
                    Logg ut
                </button>
            </div>

        </div>
    );
}