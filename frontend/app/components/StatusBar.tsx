"use client"
// components/StatusBar.tsx

import { useSSE } from "../context/SSEContext"
import { Activity, Wifi, WifiOff, Flame, Shield, Cpu } from "lucide-react"
import ProfileMenu from "./ProfileMenu"

export default function StatusBar() {
  const { connected, fireDetected, activeAlerts, latestSensor } = useSSE()

  const critCount = activeAlerts.filter((a) => a.severity === "CRITICAL").length
  const highCount  = activeAlerts.filter((a) => a.severity === "HIGH").length

  return (
    <div className="status-bar">
      {/* Brand */}
      <div className="status-brand">
        <Flame size={22} className="brand-flame" />
        <span className="brand-name">INFERNO EYE</span>
        <span className="brand-tag">AI Fire Command</span>
      </div>

      {/* Center status pills */}
      <div className="status-pills">
        {fireDetected && (
          <div className="pill pill-fire">
            <Flame size={14} />
            FIRE DETECTED
          </div>
        )}
        {critCount > 0 && (
          <div className="pill pill-critical">
            <Shield size={14} />
            {critCount} CRITICAL
          </div>
        )}
        {highCount > 0 && (
          <div className="pill pill-high">
            <Shield size={14} />
            {highCount} HIGH
          </div>
        )}
      </div>

      {/* Right indicators */}
      <div className="status-indicators">
        {latestSensor && (
          <div className="indicator">
            <Cpu size={14} />
            <span>{latestSensor.temperature.toFixed(1)}°C</span>
          </div>
        )}
        <div className={`indicator ${connected ? "ind-connected" : "ind-disconnected"}`}>
          {connected ? <Wifi size={14} /> : <WifiOff size={14} />}
          <span>{connected ? "LIVE" : "CONNECTING…"}</span>
        </div>
        <div className="indicator ind-pulse">
          <Activity size={14} />
          <span>{activeAlerts.length} Active</span>
        </div>
        <div className="status-bar-divider" />
        <ProfileMenu />
      </div>
    </div>
  )
}
