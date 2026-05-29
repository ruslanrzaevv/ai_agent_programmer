// src/hooks/useMetrics.js

import {
    useEffect,
    useState,
  } from "react";
  
  import {
    getMetrics,
  } from "../api/metricsApi";
  
  export default function useMetrics() {
  
    const [
      metrics,
      setMetrics,
    ] = useState("");
  
    async function loadMetrics() {
  
      try {
  
        const response =
          await getMetrics();
  
        setMetrics(
          response.data
        );
  
      } catch (error) {
  
        console.error(
          error
        );
  
      }
    }
  
    useEffect(() => {
      loadMetrics();
    }, []);
  
    return metrics;
  }