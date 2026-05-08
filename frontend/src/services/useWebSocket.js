import { useEffect, useRef, useState } from 'react'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

/**
 * Connects to the backend websocket and feeds typed messages back to the
 * caller via onMessage. Reconnects with backoff so a backend restart
 * doesn't strand the UI.
 */
export function useWebSocket(onMessage) {
  const [status, setStatus] = useState('idle') // idle | live | offline
  const handlerRef = useRef(onMessage)
  handlerRef.current = onMessage

  useEffect(() => {
    let ws
    let retry = 0
    let stopped = false
    let reconnectTimer

    const connect = () => {
      ws = new WebSocket(WS_URL)
      setStatus('idle')

      ws.onopen = () => {
        retry = 0
        setStatus('live')
      }
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data)
          handlerRef.current?.(msg)
        } catch {
          // ignore malformed payloads
        }
      }
      ws.onerror = () => {
        // browser will trigger onclose right after; status is set there
      }
      ws.onclose = () => {
        setStatus('offline')
        if (stopped) return
        retry += 1
        const delay = Math.min(1000 * 2 ** retry, 10000)
        reconnectTimer = setTimeout(connect, delay)
      }
    }

    connect()
    return () => {
      stopped = true
      clearTimeout(reconnectTimer)
      try { ws?.close() } catch {}
    }
  }, [])

  return { status }
}
