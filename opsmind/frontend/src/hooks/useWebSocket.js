import { useEffect, useState } from "react";
import { wsService } from "../services/websocket";
import { useLogStore } from "../store/logStore";
import { useIncidentStore } from "../store/incidentStore";

export function useWebSocket(projectId) {
  const [connected, setConnected] = useState(false);
  const pushLog = useLogStore((s) => s.pushRealtime);
  const addIncident = useIncidentStore((s) => s.addRealtime);

  useEffect(() => {
    if (!projectId) return;

    wsService.connect(projectId);

    const offConnected = wsService.on("connected", () => setConnected(true));
    const offDisconnected = wsService.on("disconnected", () => setConnected(false));

    // Route log events to log store
    const offLog = wsService.on("log", (msg) => {
      if (msg.data) pushLog(msg.data);
    });

    // Route incident events to incident store
    const offIncident = wsService.on("incident_created", (msg) => {
      if (msg) addIncident(msg);
    });

    // Ping every 30s to keep connection alive
    const pingInterval = setInterval(() => wsService.ping(), 30000);

    return () => {
      offConnected();
      offDisconnected();
      offLog();
      offIncident();
      clearInterval(pingInterval);
    };
  }, [projectId, pushLog, addIncident]);

  return { connected };
}