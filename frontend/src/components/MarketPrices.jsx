import React from 'react'

function fmtPrice(n) {
  if (n == null) return '-'
  return Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function fmtPct(n) {
  if (n == null) return '-'
  const sign = n > 0 ? '+' : ''
  return `${sign}${Number(n).toFixed(2)}%`
}

export default function MarketPrices({ quotes, selectedSymbol, onSelect, wsStatus }) {
  const list = Object.values(quotes || {})
  list.sort((a, b) => a.symbol.localeCompare(b.symbol))

  return (
    <section className="panel area-market">
      <div className="panel-header">
        <h2 className="panel-title">Market Prices</h2>
        <span className="muted" style={{ fontSize: 12 }}>
          <span className={`status-dot ${wsStatus}`}></span>
          {wsStatus === 'live' ? 'live' : wsStatus === 'offline' ? 'reconnecting…' : 'connecting…'}
        </span>
      </div>

      {list.length === 0 && <div className="muted">Waiting for first tick…</div>}

      {list.map((q) => {
        const dir = q.change_pct > 0 ? 'up' : q.change_pct < 0 ? 'down' : 'flat'
        const selected = q.symbol === selectedSymbol
        return (
          <div
            key={q.symbol}
            className={`row ${selected ? 'selected' : ''}`}
            onClick={() => onSelect?.(q.symbol)}
          >
            <span className="sym">{q.symbol}</span>
            <span className="px">${fmtPrice(q.price)}</span>
            <span className={`chg ${dir}`}>{fmtPct(q.change_pct)}</span>
          </div>
        )
      })}
    </section>
  )
}
