import React from 'react';

import Sidebar from './components/Sidebar';
import './Styles/global.css';

function App() {
    return (

        <div className="app" style={{ display: 'flex' }}>


            <Sidebar />

            <div className="main" style={{ flex: 1, padding: '20px' }}>
                <input
                    className="chat-input"
                    placeholder="Ask something..."
                    style={{ width: '50%', padding: '10px' }}
                />
            </div>
        </div>
    );
}

export default App;