import React, { useEffect, useState } from 'react'

import { api } from '../services/api.js'

export default function TradePanel({ defaultSymbol, onTraded }) {
  const [symbol, setSymbol]   = useState(defaultSymbol || '')
  const [quantity, setQuantity] = useState('1')
  const [busy, setBusy] = useState(false)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    if (defaultSymbol) setSymbol(defaultSymbol)
  }, [defaultSymbol])

  async function submit(side) {
    setToast(null)
    const qty = parseInt(quantity, 10)
    if (!symbol || !Number.isFinite(qty) || qty <= 0) {
      setToast({ kind: 'error', text: 'Enter a symbol and a positive quantity.' })
      return
    }
    setBusy(true)
    try {
      const trade = await api.placeTrade({
        symbol: symbol.trim().toUpperCase(),
        quantity: qty,
        side,
      })
      setToast({
        kind: 'ok',
        text: `${side} ${trade.quantity} ${trade.symbol} @ $${Number(trade.price).toFixed(2)}`,
      })
      onTraded?.(trade)
    } catch (e) {
      setToast({ kind: 'error', text: e.message || 'Trade failed' })
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel area-trade">
      <div className="panel-header"><h2 className="panel-title">Trade</h2></div>

      <div className="trade-form">
        <input
          className="input"
          placeholder="Symbol (e.g. AAPL)"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          spellCheck={false}
        />
        <input
          className="input"
          placeholder="Qty"
          type="number"
          min="1"
          step="1"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
        />
        <button className="btn buy"  onClick={() => submit('BUY')}  disabled={busy}>BUY</button>
        <button className="btn sell" onClick={() => submit('SELL')} disabled={busy}>SELL</button>
      </div>

      {toast && (
        <div className={`toast ${toast.kind}`}>{toast.text}</div>
      )}
    </section>
  )
}
