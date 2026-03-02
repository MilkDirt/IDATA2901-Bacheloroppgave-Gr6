// src/tools/App.jsx
import React,{useState} from "react";
import "../styles/global.css";
import "../styles/chat.css";

import Sidebar from "../components/sideBar.jsx";
import ChatPanel from "../components/chatPanel.jsx";
import { useChat } from "../hooks/useChat.js";

function App() {

     const [projects, setProjects] = useState(["BachelorSkrivingen", "Fysikkeksamen", "Matteeksamen"]);
     const [activeProject, setActiveProject] = useState("BachelorSkrivingen");
     const chat = useChat(activeProject);

    return (
        <div className="app">
            <Sidebar
                projects={projects}
                setProjects={setProjects}
                activeProject={activeProject}
                setActiveProject={setActiveProject}
             />

            <ChatPanel activeProject={activeProject} {...chat} />

        </div>
    );
}

export default App;
