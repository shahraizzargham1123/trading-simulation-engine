import React from 'react'

function fmtMoney(n) {
  if (n == null) return '-'
  const sign = n < 0 ? '-' : ''
  return `${sign}$${Math.abs(Number(n)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function fmtPct(n) {
  if (n == null) return '-'
  const sign = n > 0 ? '+' : ''
  return `${sign}${Number(n).toFixed(2)}%`
}

function dirClass(n) {
  if (n > 0) return 'up'
  if (n < 0) return 'down'
  return 'flat'
}

export default function Portfolio({ snapshot }) {
  if (!snapshot) {
    return (
      <section className="panel area-portfolio">
        <div className="panel-header"><h2 className="panel-title">Portfolio</h2></div>
        <div className="muted">Loading…</div>
      </section>
    )
  }

  const pnlDir = dirClass(snapshot.total_pnl)

  return (
    <section className="panel area-portfolio">
      <div className="panel-header"><h2 className="panel-title">Portfolio</h2></div>

      <div className="kv">
        <span className="k">Total Value</span>
        <span className="v big">{fmtMoney(snapshot.total_value)}</span>
      </div>

      <div className="kv">
        <span className="k">Profit / Loss</span>
        <span className={`v ${pnlDir}`}>
          {fmtMoney(snapshot.total_pnl)} ({fmtPct(snapshot.total_pnl_pct)})
        </span>
      </div>

      <div className="kv">
        <span className="k">Cash</span>
        <span className="v">{fmtMoney(snapshot.cash_balance)}</span>
      </div>

      <div className="kv">
        <span className="k">Holdings Value</span>
        <span className="v">{fmtMoney(snapshot.holdings_value)}</span>
      </div>

      <div className="holdings">
        <div className="kv" style={{ paddingBottom: 4 }}>
          <span className="k">Holdings</span>
          <span className="k">{snapshot.holdings.length} symbol{snapshot.holdings.length === 1 ? '' : 's'}</span>
        </div>

        {snapshot.holdings.length === 0 && <div className="muted">No positions yet.</div>}

        {snapshot.holdings.map((h) => (
          <div key={h.symbol} className="h-row">
            <span className="h-sym">{h.symbol}</span>
            <span className="h-qty">{h.quantity} sh</span>
            <span>{fmtMoney(h.market_value)}</span>
            <span className={dirClass(h.unrealized_pnl)}>
              {fmtMoney(h.unrealized_pnl)} ({fmtPct(h.unrealized_pnl_pct)})
            </span>
          </div>
        ))}
      </div>
    </section>
  )
}
