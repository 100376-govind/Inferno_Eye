"use client"
// components/AlertPanel.tsx

import { useSSE } from "../context/SSEContext"
import { useEffect, useRef } from "react"
import { Bell, BellOff, X, Flame, AlertTriangle } from "lucide-react"
import { severityBg, formatTs } from "../lib/utils"
import type { AlertOut } from "../types"

function AlertCard({ alert, onDismiss }: { alert: AlertOut; onDismiss: (id: number) => void }) {
  return (
    <div className={`alert-card border ${severityBg(alert.severity)}`}>
      <div className="alert-card-header">
        <div className="alert-card-left">
          {alert.severity === "CRITICAL" ? <Flame size={15} /> : <AlertTriangle size={15} />}
          <span className="alert-severity">{alert.severity}</span>
          <span className="alert-source">{alert.camera_source}</span>
        </div>
        <div className="alert-card-right">
          <span className="alert-time">{formatTs(alert.timestamp)}</span>
          <button
            className="alert-dismiss"
            onClick={() => onDismiss(alert.id)}
            title="Acknowledge"
          >
            <X size={13} />
          </button>
        </div>
      </div>
      <p className="alert-message">{alert.message}</p>
      <div className="alert-meta">
        <span>Conf: {(alert.confidence * 100).toFixed(0)}%</span>
        <span>📍 {alert.lat.toFixed(4)}, {alert.lng.toFixed(4)}</span>
      </div>
    </div>
  )
}

export default function AlertPanel() {
  const { activeAlerts, dismissAlert } = useSSE()
  const listRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to top when new alert arrives
  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = 0
  }, [activeAlerts.length])

  return (
    <div className="panel">
      <div className="panel-header">
        <Bell size={16} className="panel-icon text-red-400" />
        <h2 className="panel-title">Active Alerts</h2>
        <span className="panel-badge badge-count">{activeAlerts.length}</span>
      </div>

      {activeAlerts.length === 0 ? (
        <div className="panel-empty">
          <BellOff size={32} className="empty-icon" />
          <p>No active alerts</p>
          <span>System is monitoring…</span>
        </div>
      ) : (
        <div className="alert-list" ref={listRef}>
          {activeAlerts.map((a) => (
            <AlertCard key={a.id} alert={a} onDismiss={dismissAlert} />
          ))}
        </div>
      )}
    </div>
  )
}
