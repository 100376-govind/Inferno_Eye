"use client"
// app/dashboard/page.tsx — Full dashboard layout (auth-guarded)

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import dynamic from "next/dynamic"
import StatusBar from "../components/StatusBar"
import FireStatusCard from "../components/FireStatusCard"
import SensorPanel from "../components/SensorPanel"
import AlertPanel from "../components/AlertPanel"
import IncidentTimeline from "../components/IncidentTimeline"
import BlockchainPanel from "../components/BlockchainPanel"
import LiveMonitorPanel from "../components/LiveMonitorPanel"
import FireAlertToast from "../components/FireAlertToast"

// Map must be client-side only (no SSR)
const MapPanel = dynamic(() => import("../components/MapPanel"), { ssr: false })

export default function DashboardPage() {
  const router = useRouter()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem("ie_token")
    if (!token) {
      router.replace("/auth/login")
    } else {
      setReady(true)
    }
  }, [router])

  // Show nothing while checking auth (prevents flash)
  if (!ready) {
    return (
      <div className="auth-guard-loader">
        <div className="auth-guard-spinner" />
      </div>
    )
  }

  return (
    <div className="dashboard-root">
      <FireAlertToast />
      <StatusBar />

      <main className="dashboard-main">
        {/* Row 1 — Status hero + sensor grid */}
        <div className="row-top">
          <FireStatusCard />
          <SensorPanel />
        </div>

        {/* Row 2 — Full-width live monitor */}
        <div className="row-monitor">
          <LiveMonitorPanel />
        </div>

        {/* Row 3 — Map + Alerts */}
        <div className="row-map-alerts">
          <MapPanel />
          <AlertPanel />
        </div>

        {/* Row 4 — Incident timeline + Blockchain */}
        <div className="row-history">
          <IncidentTimeline />
          <BlockchainPanel />
        </div>
      </main>

      <footer className="dashboard-footer">
        <span>🔥 Inferno Eye · AI + IoT + Blockchain · Kolkata, West Bengal</span>
        <span>No WebSockets · SSE Only · Real-time Hardware Integration</span>
      </footer>
    </div>
  )
}

