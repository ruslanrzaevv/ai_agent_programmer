// src/hooks/useLogs.js

import {
  useEffect,
  useState,
} from "react";

import {
  getLogs,
} from "../api/logApi";

export default function useLogs(
  projectId
) {

  const [
    logs,
    setLogs,
  ] = useState([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  async function loadLogs() {

    if (!projectId)
      return;

    try {

      const response =
        await getLogs(
          projectId
        );

      setLogs(
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
    loadLogs();
  }, [projectId]);

  return {
    logs,
    loading,
    reload:
      loadLogs,
  };
}