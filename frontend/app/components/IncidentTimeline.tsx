"use client"
// components/IncidentTimeline.tsx

import { useSSE } from "../context/SSEContext"
import { useEffect, useState } from "react"
import { Clock, Flame, AlertTriangle } from "lucide-react"
import { fetchIncidents } from "../lib/api"
import { formatDateTime, severityBg } from "../lib/utils"
import type { IncidentOut } from "../types"

export default function IncidentTimeline() {
  const { recentIncidents } = useSSE()
  const [initial, setInitial] = useState<IncidentOut[]>([])

  // Load initial history from REST
  useEffect(() => {
    fetchIncidents(30)
      .then(setInitial)
      .catch(() => {})
  }, [])

  // Merge SSE live + REST history (deduplicate by id)
  const merged = [
    ...recentIncidents,
    ...initial.filter((h) => !recentIncidents.some((r) => r.id === h.id)),
  ]
    .sort((a, b) => b.timestamp - a.timestamp)
    .slice(0, 40)

  return (
    <div className="panel">
      <div className="panel-header">
        <Clock size={16} className="panel-icon" />
        <h2 className="panel-title">Incident Timeline</h2>
        <span className="panel-badge badge-count">{merged.length}</span>
      </div>

      {merged.length === 0 ? (
        <div className="panel-empty">
          <Flame size={28} className="empty-icon" />
          <p>No incidents recorded yet</p>
        </div>
      ) : (
        <div className="timeline">
          {merged.map((inc, i) => (
            <div key={inc.id} className={`timeline-item ${i === 0 ? "timeline-latest" : ""}`}>
              <div className="timeline-dot-col">
                <div className={`timeline-dot border ${severityBg(inc.severity)}`}>
                  {inc.label === "fire" ? <Flame size={10} /> : <AlertTriangle size={10} />}
                </div>
                {i < merged.length - 1 && <div className="timeline-line" />}
              </div>
              <div className="timeline-content">
                <div className="timeline-header">
                  <span className={`tl-label border ${severityBg(inc.severity)}`}>
                    {inc.severity}
                  </span>
                  <span className="tl-source">{inc.camera_source}</span>
                  <span className="tl-time">{formatDateTime(inc.timestamp)}</span>
                </div>
                <p className="tl-detection">
                  {inc.label.toUpperCase()} — {(inc.confidence * 100).toFixed(0)}% confidence
                </p>
                <p className="tl-response">{inc.response_recommendation}</p>
                <p className="tl-location">
                  📍 {inc.lat.toFixed(4)}, {inc.lng.toFixed(4)}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
