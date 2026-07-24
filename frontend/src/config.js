// Central API configuration
// In production, set VITE_API_URL in your Vercel environment variables.
// Locally it falls back to localhost:8000.

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// WebSocket base: replace http(s) with ws(s) automatically
export const WS_BASE = API_BASE.replace(/^http/, "ws");

export default API_BASE;
