'use client'

import { useEffect, useMemo, useRef, useState } from 'react'

export type RuntimeState = {
  meters: { l: number; r: number }
  notes: { note: number; vel: number }[]
  voices_active: number
}

const initialState: RuntimeState = { meters: { l: 0, r: 0 }, notes: [], voices_active: 0 }

export function useSynthSocket(url: string) {
  const [connected, setConnected] = useState(false)
  const [state, setState] = useState<RuntimeState>(initialState)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    let retry: number | null = null
    const connect = () => {
      const ws = new WebSocket(url)
      wsRef.current = ws
      ws.onopen = () => setConnected(true)
      ws.onclose = () => {
        setConnected(false)
        retry = window.setTimeout(connect, 1200)
      }
      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data)
        if (msg.type === 'runtime.state') setState(msg)
      }
    }
    connect()
    return () => {
      if (retry) window.clearTimeout(retry)
      wsRef.current?.close()
    }
  }, [url])

  const send = useMemo(
    () => (data: object) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(data))
      }
    },
    []
  )

  return { connected, state, send }
}
