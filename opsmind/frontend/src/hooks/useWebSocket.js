import { useEffect, useState } from "react";
import { wsService } from "../services/websocket";


export function useWebSocket(projectId) {
  const [connected, setConnected] = useState(wsService.connected);

  useEffect(() => {
    const offConnected    = wsService.on("connected",    () => setConnected(true));
    const offDisconnected = wsService.on("disconnected", () => setConnected(false));

    setConnected(wsService.connected);

    return () => {
      offConnected();
      offDisconnected();
    };
  }, [projectId]);

  return { connected };
}