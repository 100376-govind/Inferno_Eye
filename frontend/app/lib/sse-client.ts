// lib/sse-client.ts — singleton EventSource with auto-reconnect + typed dispatch

import type { SSEEvent } from "../types"

type Listener = (event: SSEEvent) => void

const RECONNECT_DELAY = 3000

class SSEClient {
  private es: EventSource | null = null
  private listeners: Set<Listener> = new Set()
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private stopped = false

  start(url: string) {
    if (this.es) return   // already running
    this.stopped = false
    this._connect(url)
  }

  private _connect(url: string) {
    if (this.stopped) return
    this.es = new EventSource(url)

    this.es.onmessage = (ev) => {
      try {
        const parsed = JSON.parse(ev.data) as SSEEvent
        this.listeners.forEach((l) => l(parsed))
      } catch {
        // silently ignore malformed frames
      }
    }

    this.es.onerror = () => {
      this.es?.close()
      this.es = null
      if (!this.stopped) {
        this.reconnectTimer = setTimeout(() => this._connect(url), RECONNECT_DELAY)
      }
    }
  }

  stop() {
    this.stopped = true
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.es?.close()
    this.es = null
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  isConnected() {
    return this.es?.readyState === EventSource.OPEN
  }
}

// singleton — shared across the whole app
export const sseClient = new SSEClient()
