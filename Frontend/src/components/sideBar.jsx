import React, { useState, useEffect } from "react";
import "../Styles/Sidebar.css";


export default function Sidebar({ projects, setProjects, activeProject, setActiveProject}) {

    const [openMenu, setOpenMenu] = useState(null);

    useEffect(() => {
        const lukkMeny = () =>{
            setOpenMenu(null);
            };
        document.addEventListener("click", lukkMeny);

        return () => {
            document.removeEventListener("click", lukkMeny);
        };
    }, []);

    const handleAddProject = () => {
        const newProjectName = prompt("Enter the name of the new project?")
        if (newProjectName){
            setProjects([...projects, newProjectName]);
            setActiveProject(newProjectName);
            }
        };

    const handleDeleteProject = (projectToBeDeleted) => {
        const updatedProjects = projects.filter(project => project!== projectToBeDeleted);
        setProjects(updatedProjects);
        setOpenMenu(null);
        };

    const toggleMenu = (project, e) => {
        e.stopPropagation();
        if (openMenu === project) {
            setOpenMenu(null);
        } else {
            setOpenMenu(project);
        }
    };





// --- SKJERMEN (HTML/JSX) ---
    return (
        <div className="sidebar">
            <div className="new-project-container">
                <button className="new-project-btn" onClick={handleAddProject}>
                    + New Project
                </button>
            </div>

            <div className="projects-section">
                <h3>Projects</h3>

                <ul className="projects-list">
                    {projects.map((project, index) => (
                        <li
                            key={index}
                            // Viktig: Her MÅ du bruke backticks (skrå anførselstegn), ikke vanlige!
                            className={`project-item ${activeProject === project ? "active" : ""}`}
                            onClick={() => setActiveProject(project)}
                        >
                            {/* Vi legger prosjektnavnet i en egen boks */}
                            <span className="project-name">{project}</span>

                            {/* HER BEGYNNER TRE-PRIKKER-MENYEN */}
                            <div className="menu-container">
                                {/* Selve prikk-knappen */}
                                <button className="three-dots-btn" onClick={(e) => toggleMenu(project, e)}>
                                    ⋮
                                </button>

                                {/* Dette tegnes BARE hvis openMenu er lik dette prosjektet */}
                                {openMenu === project && (
                                    <div className="dropdown-menu">
                                        <button
                                            className="delete-btn"
                                            onClick={(e) => {
                                                e.stopPropagation(); // Stopp klikket fra å treffe li-en
                                                handleDeleteProject(project); // Kjør slette-funksjonen din!
                                            }}
                                        >
                                            Delete
                                        </button>
                                    </div>
                                )}
                            </div>
                            {/* HER SLUTTER TRE-PRIKKER-MENYEN */}

                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}

