import React, { useState, useEffect } from "react";
import "../Styles/Sidebar.css";


export default function Sidebar({ projects, setProjects, activeProject, setActiveProject, renameProjectMessages }) {

    const [openMenu, setOpenMenu] = useState(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

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

   const toggleSidebar = () => {
       if (isSidebarOpen === true){
           setIsSidebarOpen(false);
           } else{
               setIsSidebarOpen(true)}
       };

   const getMenuTitle = () => {
    if (isSidebarOpen === true) {
        return "Collapse menu";
    } else {
        return "Expand menu";
    }
};

   const handleRenameProject = (ProjectToBeRenamed) => {
        const newProjectName = prompt("Enter the new name of the project?", ProjectToBeRenamed);
        if (newProjectName && newProjectName !== ProjectToBeRenamed) {
            const updatedProjects = projects.map(project =>
                project === ProjectToBeRenamed ? newProjectName : project
            );
            setProjects(updatedProjects);
            if (activeProject === ProjectToBeRenamed) {
                setActiveProject(newProjectName);
            }
            renameProjectMessages(ProjectToBeRenamed, newProjectName);

        }
    }








    return (
        <div className={isSidebarOpen === true ? "sidebar" : "sidebar collapsed"}>
            <button
            className="toggle-sidebar-btn"
            onClick={() => setIsSidebarOpen(toggleSidebar)}
            title={getMenuTitle()}
           >
               ☰
            </button>
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

                            className={`project-item ${activeProject === project ? "active" : ""}`}
                            onClick={() => setActiveProject(project)}
                        >
                            {}
                            <span className="project-name">{project}</span>

                            {}
                            <div className="menu-container">
                                {}
                                <button className="three-dots-btn" onClick={(e) => toggleMenu(project, e)}>
                                    ⋮
                                </button>

                                {}
                                {openMenu === project && (
                                    <div className="dropdown-menu">
                                        <button
                                            className="delete-btn"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDeleteProject(project);
                                            }}
                                        >
                                              Delete
                                        </button>


                                        <button
                                        className="rename-btn"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleRenameProject(project);
                                        }}
                                        >
                                            Rename
                                        </button>

                                    </div>
                                )}
                            </div>
                            {}

                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}

