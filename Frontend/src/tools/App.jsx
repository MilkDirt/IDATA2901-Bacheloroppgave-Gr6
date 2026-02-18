// src/tools/App.jsx
import React from "react";
import "../styles/global.css";
import "../styles/chat.css";

import Sidebar from "../components/sideBar.jsx";
import ChatPanel from "../components/chatPanel.jsx";
import { useChat } from "../hooks/useChat.js";

function App() {
    const chat = useChat();

    return (
        <div className="app">
            <Sidebar />
            <ChatPanel {...chat} />
        </div>
    );
}

export default App;
