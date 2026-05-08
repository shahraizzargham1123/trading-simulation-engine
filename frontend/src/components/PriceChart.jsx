import React, { useEffect, useState } from 'react'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'

import { api } from '../services/api.js'

const MAX_POINTS = 120

function fmtTime(ts) {
  const d = new Date(Number(ts) * 1000)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export default function PriceChart({ symbol, livePrice }) {
  const [points, setPoints] = useState([])

  // Seed with history when the symbol changes.
  useEffect(() => {
    let cancelled = false
    setPoints([])
    if (!symbol) return
    api.getHistory(symbol, MAX_POINTS)
      .then((rows) => {
        if (cancelled) return
        setPoints(rows.map((r) => ({ t: fmtTime(r.timestamp), price: r.price, ts: r.timestamp })))
      })
      .catch(() => {
        if (!cancelled) setPoints([])
      })
    return () => { cancelled = true }
  }, [symbol])

  // Append the live tick whenever the latest price for this symbol changes.
  useEffect(() => {
    if (!livePrice || !symbol) return
    setPoints((prev) => {
      const last = prev[prev.length - 1]
      if (last && last.ts === livePrice.timestamp) return prev
      const next = [
        ...prev,
        { t: fmtTime(livePrice.timestamp), price: livePrice.price, ts: livePrice.timestamp },
      ]
      if (next.length > MAX_POINTS) next.splice(0, next.length - MAX_POINTS)
      return next
    })
  }, [livePrice, symbol])

  return (
    <section className="panel area-chart" style={{ height: 320 }}>
      <div className="panel-header">
        <h2 className="panel-title">Price Chart {symbol ? `· ${symbol}` : ''}</h2>
        {livePrice && (
          <span className="muted" style={{ fontSize: 12 }}>
            ${Number(livePrice.price).toFixed(2)}
          </span>
        )}
      </div>

      {points.length === 0 ? (
        <div className="muted">No data yet for {symbol}.</div>
      ) : (
        <ResponsiveContainer width="100%" height="88%">
          <LineChart data={points} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#2a313a" strokeDasharray="3 3" />
            <XAxis
              dataKey="t"
              tick={{ fill: '#8a93a0', fontSize: 11 }}
              minTickGap={30}
              stroke="#2a313a"
            />
            <YAxis
              domain={['auto', 'auto']}
              tick={{ fill: '#8a93a0', fontSize: 11 }}
              stroke="#2a313a"
              width={60}
              tickFormatter={(v) => `$${Number(v).toFixed(2)}`}
            />
            <Tooltip
              contentStyle={{ background: '#14181d', border: '1px solid #2a313a', borderRadius: 8 }}
              labelStyle={{ color: '#8a93a0' }}
              formatter={(v) => [`$${Number(v).toFixed(2)}`, 'Price']}
            />
            <Line
              type="monotone"
              dataKey="price"
              stroke="#4f8cff"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </section>
  )
}
