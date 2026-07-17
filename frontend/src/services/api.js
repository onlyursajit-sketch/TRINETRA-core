const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const API_KEY = import.meta.env.VITE_TRINETRA_API_KEY || "";

async function request(path, options = {}) {
  const headers = {
    ...(options.headers || {}),
  };

  if (API_KEY) {
    headers["X-API-Key"] = API_KEY;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

export function fetchMarketContext(symbol = "NIFTY") {
  return request(
    `/api/v1/market/context?symbol=${encodeURIComponent(symbol)}`
  );
}

export function fetchMarketDecision(symbol = "NIFTY") {
  return request(
    `/api/v1/market/decision?symbol=${encodeURIComponent(symbol)}`
  );
}

export function fetchProviderHealth() {
  return request("/api/v1/market/providers/health");
}
