import React from 'react';
import './styles/global.css'


function App() {
    return (
        <div className="app">
            <div className="sidebar">
                <h3>Projects</h3>
            </div>

            <div className="main">
                <input
                    className="chat-input"
                    placeholder="Ask something..."
                />
            </div>
        </div>
    );
}

export default App;
