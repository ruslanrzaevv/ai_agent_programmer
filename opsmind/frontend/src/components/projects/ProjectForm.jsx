// src/components/projects/ProjectForm.jsx

import {
    useState,
  } from "react";
  
  import {
    createProject,
  } from "../../api/projectApi";
  
  export default function ProjectForm({
    onSuccess,
  }) {
  
    const [form,
      setForm] =
      useState({
  
        name: "",
  
        environment:
          "production",
  
        docker_engine_url:
          "",
  
        gitlab_url:
          "https://gitlab.com",
  
        gitlab_token:
          "",
  
        gitlab_project_id:
          "",
  
        error_threshold_per_minute:
          5,
  
      });
  
    const handleChange =
      (e) => {
  
        setForm(
          (prev) => ({
  
            ...prev,
  
            [e.target.name]:
              e.target.value,
  
          })
        );
  
      };
  
    async function submit(
      e
    ) {
  
      e.preventDefault();
  
      try {
  
        await createProject(
          form
        );
  
        onSuccess?.();
  
        alert(
          "Project created"
        );
  
      } catch (
        error
      ) {
  
        alert(
          error.response?.data?.detail ||
          "Error"
        );
  
      }
    }
  
    return (
  
      <form
        onSubmit={submit}
      >
  
        <input
          name="name"
          placeholder="Project name"
          value={
            form.name
          }
          onChange={
            handleChange
          }
        />
  
        <input
          name="docker_engine_url"
          placeholder="Docker URL"
          value={
            form.docker_engine_url
          }
          onChange={
            handleChange
          }
        />
  
        <input
          name="gitlab_project_id"
          placeholder="GitLab Project ID"
          value={
            form.gitlab_project_id
          }
          onChange={
            handleChange
          }
        />
  
        <input
          name="gitlab_token"
          placeholder="GitLab Token"
          value={
            form.gitlab_token
          }
          onChange={
            handleChange
          }
        />
  
        <button
          type="submit"
        >
          Create Project
        </button>
  
      </form>
  
    );
  }