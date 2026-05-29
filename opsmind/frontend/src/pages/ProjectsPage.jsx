// src/pages/ProjectsPage.jsx

import useProjects
from "../hooks/useProjects";

import ProjectCard
from "../components/projects/ProjectCard";

import ProjectForm
from "../components/projects/ProjectForm";

import Loading
from "../components/common/Loading";

export default function ProjectsPage() {

  const {
    projects,
    loading,
    reload,
  } = useProjects();

  if (loading) {
    return <Loading />;
  }

  return (

    <div
      style={{
        padding:
          "32px 36px",
      }}
    >

      <h1>
        Projects
      </h1>

      <ProjectForm
        onSuccess={
          reload
        }
      />

      <div
        style={{
          marginTop: 24,
          display: "grid",
          gap: 16,
        }}
      >

        {projects.map(
          project => (

            <ProjectCard
              key={
                project.id
              }
              project={
                project
              }
            />

          )
        )}

      </div>

    </div>
  );
}