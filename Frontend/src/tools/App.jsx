// src/tools/App.jsx
import React,{useState} from "react";
import "../styles/global.css";
import "../styles/chat.css";

import Sidebar from "../components/sideBar.jsx";
import ChatPanel from "../components/chatPanel.jsx";
import { useChat } from "../hooks/useChat.js";

function App() {

     const [projects, setProjects] = useState(["Project 1", "Project 2", "Project 3"]);
     const [activeProject, setActiveProject] = useState("Project 1");
     const chat = useChat(activeProject);


    return (
        <div className="app">
            <Sidebar
                projects={projects}
                setProjects={setProjects}
                activeProject={activeProject}
                setActiveProject={setActiveProject}
                renameProjectMessages={chat.renameProjectMessages}

             />

            <ChatPanel activeProject={activeProject} {...chat} />

        </div>
    );
}

export default App;
