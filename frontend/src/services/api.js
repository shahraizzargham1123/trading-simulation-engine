const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      if (body?.detail) detail = body.detail
    } catch {}
    throw new Error(detail)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  getMe:        () => request('/users/me'),
  getSymbols:   () => request('/market/symbols'),
  getQuotes:    () => request('/market/quotes'),
  getHistory:   (symbol, limit = 60) =>
    request(`/market/history/${encodeURIComponent(symbol)}?limit=${limit}`),
  getPortfolio: () => request('/portfolio'),
  placeTrade:   ({ symbol, quantity, side }) =>
    request('/trades', {
      method: 'POST',
      body: JSON.stringify({ symbol, quantity, side }),
    }),
  getTrades:    (limit = 50) => request(`/trades?limit=${limit}`),
}
