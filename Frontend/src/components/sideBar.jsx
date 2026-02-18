import React from "react";
import "../Styles/Sidebar.css";

export default function Sidebar() {
    return (
        <div className="sidebar">


            <div className="new-project-container">
                <button className="new-project-btn">
                    + New Project
                </button>
            </div>


            <div className="projects-section">
                <h3>Projects</h3>

                <ul className="project-list">
                    <li className="project-item">Project 1</li>
                    <li className="project-item">Project 2</li>
                    <li className="project-item">Project 3</li>
                    <li className="project-item">Project 4</li>
                </ul>
            </div>

        </div>
    );
}