// WebSocket with automatic reconnect and a keep-alive ping.
// Usage: const stop = connectSocket('/ws/clinic', (msg) => ..., (connected) => ...)

export function connectSocket(path, onMessage, onStatus = () => {}) {
  let ws = null
  let stopped = false
  let retry = 0
  let pingTimer = null
  let retryTimer = null

  const url = () => `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}${path}`

  const open = () => {
    if (stopped) return
    ws = new WebSocket(url())
    ws.onopen = () => {
      retry = 0
      onStatus(true)
      pingTimer = setInterval(() => ws?.readyState === WebSocket.OPEN && ws.send('ping'), 20000)
    }
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type !== 'pong') onMessage(msg)
      } catch {
        /* ignore malformed messages */
      }
    }
    ws.onclose = () => {
      clearInterval(pingTimer)
      onStatus(false)
      if (stopped) return
      // 0.5s, 1s, 2s, 4s ... capped at 5s
      const delay = Math.min(5000, 500 * 2 ** retry++)
      retryTimer = setTimeout(open, delay)
    }
    ws.onerror = () => ws.close()
  }

  open()
  return () => {
    stopped = true
    clearInterval(pingTimer)
    clearTimeout(retryTimer)
    ws?.close()
  }
}
