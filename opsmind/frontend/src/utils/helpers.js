export function timeAgo(iso) {
    if (!iso) return "—";
    const diff = Date.now() - new Date(iso).getTime();
    const m = Math.floor(diff / 60000);
    if (m < 1) return "just now";
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h ago`;
    return `${Math.floor(h / 24)}d ago`;
  }
  
  export function formatTime(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleTimeString("en", { hour12: false });
  }
  
  export function formatDateTime(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleString("en", {
      year: "numeric", month: "short", day: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  }
  
  export function durationMinutes(startIso, endIso) {
    const end = endIso ? new Date(endIso) : new Date();
    return Math.floor((end - new Date(startIso)) / 60000);
  }