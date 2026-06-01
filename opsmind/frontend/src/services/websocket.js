import { WS_URL } from "../utils/constants";

class WebSocketService {
  constructor() {
    this.socket = null;
    this.handlers = {};
    this.projectId = null;
    this.reconnectTimer = null;
    this.reconnectDelay = 2000;
  }

  connect(projectId) {
    if (this.socket?.readyState === WebSocket.OPEN && this.projectId === projectId) return;
    this.projectId = projectId;
    this._connect();
  }

  _connect() {
    const token = localStorage.getItem("access_token");
    if (!token || !this.projectId) return;

    const url = `${WS_URL}/api/v1/ws/${this.projectId}?token=${token}`;
    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      console.log("[WS] connected to project", this.projectId);
      this.reconnectDelay = 2000;
      this._emit("connected", {});
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this._emit(data.type, data);
        this._emit("*", data); // wildcard listener
      } catch (e) {
        console.warn("[WS] parse error", e);
      }
    };

    this.socket.onclose = () => {
      console.log("[WS] disconnected, reconnecting in", this.reconnectDelay, "ms");
      this._emit("disconnected", {});
      this.reconnectTimer = setTimeout(() => {
        this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 30000);
        this._connect();
      }, this.reconnectDelay);
    };

    this.socket.onerror = (e) => {
      console.warn("[WS] error", e);
    };
  }

  disconnect() {
    clearTimeout(this.reconnectTimer);
    if (this.socket) {
      this.socket.onclose = null; // prevent reconnect
      this.socket.close();
      this.socket = null;
    }
    this.projectId = null;
  }

  on(type, handler) {
    if (!this.handlers[type]) this.handlers[type] = [];
    this.handlers[type].push(handler);
    return () => this.off(type, handler);
  }

  off(type, handler) {
    this.handlers[type] = (this.handlers[type] || []).filter((h) => h !== handler);
  }

  send(data) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    }
  }

  ping() {
    this.send({ type: "ping" });
  }

  _emit(type, data) {
    (this.handlers[type] || []).forEach((h) => h(data));
  }

  get connected() {
    return this.socket?.readyState === WebSocket.OPEN;
  }
}

export const wsService = new WebSocketService();