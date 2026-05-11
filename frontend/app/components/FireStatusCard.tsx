"use client"
// components/FireStatusCard.tsx

import { useSSE } from "../context/SSEContext"
import { Flame, ShieldCheck } from "lucide-react"

export default function FireStatusCard() {
  const { fireDetected, lastDetection, activeAlerts } = useSSE()
  const critAlert = activeAlerts.find((a) => a.severity === "CRITICAL")
  const severity  = critAlert?.severity ?? (activeAlerts[0]?.severity ?? "NONE")

  return (
    <div className={`fire-status-card ${fireDetected ? "fsc-fire" : "fsc-safe"}`}>
      <div className="fsc-icon">
        {fireDetected ? (
          <Flame size={48} className="icon-fire animate-pulse" />
        ) : (
          <ShieldCheck size={48} className="icon-safe" />
        )}
      </div>
      <div className="fsc-text">
        <h3 className="fsc-title">
          {fireDetected ? "🔥 FIRE DETECTED" : "✅ ALL CLEAR"}
        </h3>
        <p className="fsc-sub">
          {fireDetected
            ? `Severity: ${severity} | Source: ${lastDetection?.source ?? "—"}`
            : "No fire or smoke detected"}
        </p>
        {lastDetection && lastDetection.detections.length > 0 && (
          <p className="fsc-conf">
            Confidence: {(lastDetection.detections[0].confidence * 100).toFixed(1)}%
          </p>
        )}
      </div>
    </div>
  )
}
