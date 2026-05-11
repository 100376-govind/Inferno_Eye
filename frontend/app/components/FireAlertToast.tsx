"use client"
// components/FireAlertToast.tsx
// Dramatic popup toast triggered whenever a new HIGH/CRITICAL alert arrives via SSE.
// Renders ON TOP of the dashboard — no changes needed to existing components.

import { useEffect, useRef, useState } from "react"
import { useSSE } from "../context/SSEContext"
import type { AlertOut } from "../types"
import { AlertTriangle, X, MapPin, Flame, Wind } from "lucide-react"

interface ToastAlert extends AlertOut {
  toastId: string
}

const SEVERITY_CONFIG: Record<string, { bg: string; border: string; glow: string; icon: string }> = {
  CRITICAL: {
    bg:     "linear-gradient(135deg,rgba(220,38,38,0.97),rgba(153,27,27,0.97))",
    border: "rgba(239,68,68,0.8)",
    glow:   "0 0 60px rgba(239,68,68,0.5), 0 20px 60px rgba(0,0,0,0.6)",
    icon:   "#fca5a5",
  },
  HIGH: {
    bg:     "linear-gradient(135deg,rgba(194,65,12,0.97),rgba(154,52,18,0.97))",
    border: "rgba(249,115,22,0.8)",
    glow:   "0 0 60px rgba(249,115,22,0.4), 0 20px 60px rgba(0,0,0,0.6)",
    icon:   "#fdba74",
  },
  MEDIUM: {
    bg:     "linear-gradient(135deg,rgba(133,77,14,0.97),rgba(120,53,15,0.97))",
    border: "rgba(234,179,8,0.6)",
    glow:   "0 0 40px rgba(234,179,8,0.3), 0 20px 40px rgba(0,0,0,0.5)",
    icon:   "#fde68a",
  },
}

const SOURCE_LABELS: Record<string, string> = {
  esp32:  "ESP32-CAM",
  mobile: "Mobile Camera",
  upload: "Video Upload",
}

function formatCoords(lat: number, lng: number) {
  return `${lat.toFixed(5)}° N, ${lng.toFixed(5)}° E`
}

function SingleToast({ alert, onDismiss }: { alert: ToastAlert; onDismiss: () => void }) {
  const cfg = SEVERITY_CONFIG[alert.severity] ?? SEVERITY_CONFIG.MEDIUM
  const isFire = alert.alert_type?.toLowerCase() === "fire"
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    // Animate in
    const t = setTimeout(() => setVisible(true), 20)
    return () => clearTimeout(t)
  }, [])

  function handleDismiss() {
    setVisible(false)
    setTimeout(onDismiss, 350)
  }

  return (
    <div
      className="hazard-toast"
      style={{
        opacity:   visible ? 1 : 0,
        transform: visible ? "scale(1)" : "scale(0.9)",
      }}
    >
      <div className="hazard-toast-inner">
        {/* Top Warning Icon */}
        <div className="hazard-icon-circle">
          <AlertTriangle size={36} fill="white" color="transparent" />
        </div>

        {/* Title */}
        <h2 className="hazard-title">WARNING!</h2>

        {/* Message */}
        <div className="hazard-body">
          <p className="hazard-msg">{alert.message}</p>
          <div className="hazard-details">
            <span>Confidence: {(alert.confidence * 100).toFixed(0)}%</span>
            <span>Source: {alert.camera_source}</span>
            <span>Location: {alert.lat.toFixed(4)}, {alert.lng.toFixed(4)}</span>
          </div>
        </div>

        {/* Actions */}
        <div className="hazard-actions">
          <button className="hazard-btn-cancel" onClick={handleDismiss}>
            CANCEL
          </button>
          <a
            href={`https://maps.google.com/?q=${alert.lat},${alert.lng}`}
            target="_blank"
            rel="noreferrer"
            className="hazard-btn-proceed"
          >
            PROCEED
          </a>
        </div>
      </div>

      {/* Hazard Stripe Footer */}
      <div className="hazard-footer-stripes" />
    </div>
  )
}

export default function FireAlertToast() {
  const { activeAlerts } = useSSE()
  const [currentToast, setCurrentToast] = useState<ToastAlert | null>(null)
  const seenIds = useRef<Set<number>>(new Set())

  useEffect(() => {
    activeAlerts.forEach((a) => {
      if (seenIds.current.has(a.id)) return
      
      // Only pop for CRITICAL, HIGH, and MEDIUM
      if (a.severity === "CRITICAL" || a.severity === "HIGH" || a.severity === "MEDIUM") {
        seenIds.current.add(a.id)
        const toast: ToastAlert = { ...a, toastId: `${a.id}-${Date.now()}` }
        // Setting this will overwrite any current toast
        setCurrentToast(toast)
      }
    })
  }, [activeAlerts])

  if (!currentToast) return null

  return (
    <div className="fire-toast-container">
      <SingleToast
        key={currentToast.toastId}
        alert={currentToast}
        onDismiss={() => setCurrentToast(null)}
      />
    </div>
  )
}
