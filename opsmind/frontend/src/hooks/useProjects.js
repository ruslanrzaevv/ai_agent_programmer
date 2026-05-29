// src/hooks/useProjects.js

import {
  useEffect,
  useState,
} from "react";

import {
  getProjects,
} from "../api/projectApi";

export default function useProjects() {

  const [
    projects,
    setProjects,
  ] = useState([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  async function loadProjects() {

    try {

      const response =
        await getProjects();

      setProjects(
        response.data
      );

    } catch (error) {

      console.error(
        error
      );

    } finally {

      setLoading(
        false
      );

    }
  }

  useEffect(() => {
    loadProjects();
  }, []);

  return {
    projects,
    setProjects,
    loading,
    reload:
      loadProjects,
  };
}