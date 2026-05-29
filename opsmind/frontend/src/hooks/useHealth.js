// src/hooks/useHealth.js

import {
  useEffect,
  useState,
} from "react";

import {
  getHealth,
} from "../api/healthApi";

export default function useHealth() {

  const [
    health,
    setHealth,
  ] = useState(null);

  async function loadHealth() {

    try {

      const response =
        await getHealth();

      setHealth(
        response.data
      );

    } catch (error) {

      console.error(
        error
      );

    }
  }

  useEffect(() => {

    loadHealth();

    const interval =
      setInterval(
        loadHealth,
        10000
      );

    return () =>
      clearInterval(
        interval
      );

  }, []);

  return health;
}