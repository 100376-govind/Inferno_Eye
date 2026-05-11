"use client"
// context/SSEContext.tsx — global SSE state, consumed by all dashboard components

import React, {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react"
import { sseClient } from "../lib/sse-client"
import type {
  SSEEvent,
  SensorReading,
  AlertOut,
  IncidentOut,
  BlockOut,
  DetectionResult,
  MapPin,
} from "../types"

const API_SSE = "http://localhost:8000/events/live"

interface SSEState {
  connected: boolean
  // live sensor
  latestSensor: SensorReading | null
  // latest annotated frame per source
  latestFrame: Record<string, string>          // source → base64 JPEG
  // alerts
  activeAlerts: AlertOut[]
  // incidents
  recentIncidents: IncidentOut[]
  // blockchain
  latestBlocks: BlockOut[]
  // map pins
  pins: MapPin[]
  // video progress
  videoProgress: { jobId: number; pct: number; source: string } | null
  // fire status
  fireDetected: boolean
  lastDetection: DetectionResult | null
}

interface SSEContextType extends SSEState {
  dismissAlert: (id: number) => void
}

const SSEContext = createContext<SSEContextType | null>(null)

export function SSEProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<SSEState>({
    connected: false,
    latestSensor: null,
    latestFrame: {},
    activeAlerts: [],
    recentIncidents: [],
    latestBlocks: [],
    pins: [],
    videoProgress: null,
    fireDetected: false,
    lastDetection: null,
  })

  // Audio ref for alert sound
  const audioRef = useRef<AudioContext | null>(null)

  function playBeep(frequency = 880, duration = 0.4) {
    try {
      if (!audioRef.current) audioRef.current = new AudioContext()
      const ctx = audioRef.current
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.frequency.value = frequency
      osc.type = "square"
      gain.gain.setValueAtTime(0.3, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration)
      osc.start(ctx.currentTime)
      osc.stop(ctx.currentTime + duration)
    } catch { /* ignore audio errors */ }
  }

  useEffect(() => {
    sseClient.start(API_SSE)

    const unsub = sseClient.subscribe((ev: SSEEvent) => {
      setState((prev) => {
        const next = { ...prev }

        switch (ev.type) {
          case "frame": {
            const d = ev.payload as DetectionResult
            // Guard: bail if payload is missing or malformed
            if (!d || !d.source) break
            next.latestFrame = { ...prev.latestFrame, [d.source]: d.annotated_frame ?? "" }
            next.lastDetection = d
            if (d.detections && d.detections.length > 0) {
              next.fireDetected = true
              // Add map pin
              const pin: MapPin = {
                lat: d.lat,
                lng: d.lng,
                label: d.detections[0].label,
                severity: d.detections[0].confidence > 0.7 ? "HIGH" : "MEDIUM",
                timestamp: d.timestamp,
              }
              next.pins = [pin, ...prev.pins.slice(0, 19)]
            }
            break
          }

          case "sensor": {
            next.latestSensor = ev.payload as SensorReading
            break
          }

          case "alert": {
            const a = ev.payload as AlertOut
            next.activeAlerts = [a, ...prev.activeAlerts.filter((x) => x.id !== a.id).slice(0, 49)]
            if (a.severity === "CRITICAL" || a.severity === "HIGH") {
              playBeep(880, 0.5)
            }
            break
          }

          case "incident": {
            const inc = ev.payload as IncidentOut
            next.recentIncidents = [inc, ...prev.recentIncidents.slice(0, 49)]
            break
          }

          case "blockchain": {
            const blk = ev.payload as BlockOut
            next.latestBlocks = [blk, ...prev.latestBlocks.slice(0, 19)]
            break
          }

          case "video_progress": {
            const vp = ev.payload as { job_id: number; progress_pct: number; source: string }
            next.videoProgress = {
              jobId: vp.job_id,
              pct: vp.progress_pct,
              source: vp.source,
            }
            break
          }

          case "alert_ack": {
            const ack = ev.payload as { id: number }
            next.activeAlerts = prev.activeAlerts.filter((a) => a.id !== ack.id)
            break
          }
        }

        next.connected = sseClient.isConnected()
        return next
      })
    })

    // Periodic connection check
    const tick = setInterval(() => {
      setState((prev) => ({ ...prev, connected: sseClient.isConnected() }))
    }, 2000)

    return () => {
      unsub()
      clearInterval(tick)
    }
  }, [])

  function dismissAlert(id: number) {
    setState((prev) => ({
      ...prev,
      activeAlerts: prev.activeAlerts.filter((a) => a.id !== id),
    }))
    // Also call backend
    fetch(`http://localhost:8000/alerts/${id}/acknowledge`, { method: "POST" }).catch(() => {})
  }

  return (
    <SSEContext.Provider value={{ ...state, dismissAlert }}>
      {children}
    </SSEContext.Provider>
  )
}

export function useSSE() {
  const ctx = useContext(SSEContext)
  if (!ctx) throw new Error("useSSE must be used inside SSEProvider")
  return ctx
}
