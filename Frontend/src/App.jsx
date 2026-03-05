import React, { useState, useRef } from "react";
import Sidebar from "./components/sideBar";
import ChatPanel from "./components/ChatPanel";
import QueryPanel from "./components/QueryPanel";
import { useChat } from "./hooks/useChat";
import "./Styles/global.css";

function App() {
  const [projects, setProjects] = useState(["Project 1", "Project 2", "Project 3"]);
  const [activeProject, setActiveProject] = useState("Project 1");



  const renameProjectMessages = (oldName, newName) => {
  setMessages((prev) => {
    const updated = { ...prev };
    if (updated[oldName]) {
      updated[newName] = updated[oldName];
      delete updated[oldName];
    }
    return updated;
  });
};



  const [messages, setMessages] = useState({});
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // Slide in panel state
  const [showForm, setShowForm] = useState(false);

  // Structured form data
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
  const activeMessages = messages[activeProject] || [];



  // Normal chat
  const sendMessage = async () => {
  if (!input.trim()) return;

  const userMessage = { role: "user", content: input };

  setMessages(prev => ({
    ...prev,
    [activeProject]: [...(prev[activeProject] || []), userMessage]
  }));

  setLoading(true);


    try {
      const response = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ question: input })
      });

      const data = await response.json();

      setMessages(prev => ({
        ...prev,
        [activeProject]: [
          ...(prev[activeProject] || []),
          {
            role: "assistant",
            content: data.answer,
            sources: data.sources || []
          }
        ]
      }));

    } catch (error) {
      console.error("Error:", error);
    }

    setLoading(false);
  };

  // Query chat
  const generateApplication = async () => {
    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/generate-application",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(formData)
        }
      );

      const data = await response.json();

    setMessages(prev => ({
  ...prev,
  [activeProject]: [
    ...(prev[activeProject] || []),
    {
      role: "assistant",
      content: data.application_text
    }
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
        projects={projects}
        setProjects={setProjects}
        activeProject={activeProject}
        setActiveProject={setActiveProject}
        renameProjectMessages={renameProjectMessages}
       />

      <ChatPanel
        activeProject={activeProject}
        input={input}
        setInput={setInput}
        messages={messages[activeProject] || []}
        loading={loading}
        sendMessage={sendMessage}
        messagesEndRef={messagesEndRef}
        setShowForm={setShowForm}   // 👈 viktig
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