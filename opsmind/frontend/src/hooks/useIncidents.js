// src/hooks/useIncidents.js

import {
  useEffect,
  useState,
} from "react";

import {
  getIncidents,
} from "../api/incidentApi";

export default function useIncidents() {

  const [
    incidents,
    setIncidents,
  ] = useState([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  async function loadIncidents() {

    try {

      const response =
        await getIncidents();

      setIncidents(
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
    loadIncidents();
  }, []);

  return {
    incidents,
    setIncidents,
    loading,
    reload:
      loadIncidents,
  };
}