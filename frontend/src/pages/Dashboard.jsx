import React, { useCallback, useEffect, useMemo, useState } from 'react'

import MarketPrices from '../components/MarketPrices.jsx'
import Portfolio    from '../components/Portfolio.jsx'
import PriceChart   from '../components/PriceChart.jsx'
import TradePanel   from '../components/TradePanel.jsx'

import { api } from '../services/api.js'
import { useWebSocket } from '../services/useWebSocket.js'

export default function Dashboard() {
  // quotes keyed by symbol so updates by-symbol don't re-render the whole list state
  const [quotes, setQuotes] = useState({})
  const [snapshot, setSnapshot] = useState(null)
  const [selected, setSelected] = useState(null)

  // Initial REST fetch so the UI has data even before the first WS tick.
  useEffect(() => {
    api.getQuotes().then((rows) => {
      const byKey = {}
      for (const q of rows) byKey[q.symbol] = q
      setQuotes(byKey)
      if (!selected && rows.length > 0) setSelected(rows[0].symbol)
    }).catch(() => {})
    api.getPortfolio().then(setSnapshot).catch(() => {})
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleMessage = useCallback((msg) => {
    if (!msg || !msg.type) return
    if (msg.type === 'price_update' && Array.isArray(msg.quotes)) {
      setQuotes((prev) => {
        const next = { ...prev }
        for (const q of msg.quotes) next[q.symbol] = q
        return next
      })
    } else if (msg.type === 'portfolio_update' && msg.snapshot) {
      setSnapshot(msg.snapshot)
    }
  }, [])

  const { status: wsStatus } = useWebSocket(handleMessage)

  const livePrice = useMemo(
    () => (selected ? quotes[selected] : null),
    [selected, quotes],
  )

  const handleTraded = useCallback(() => {
    // Backend already pushed a portfolio_update; refetch as a safety net
    // in case the WS was reconnecting at that exact moment.
    api.getPortfolio().then(setSnapshot).catch(() => {})
  }, [])

  return (
    <div className="app">
      <MarketPrices
        quotes={quotes}
        selectedSymbol={selected}
        onSelect={setSelected}
        wsStatus={wsStatus}
      />
      <Portfolio snapshot={snapshot} />
      <PriceChart symbol={selected} livePrice={livePrice} />
      <TradePanel defaultSymbol={selected} onTraded={handleTraded} />
    </div>
  )
}
