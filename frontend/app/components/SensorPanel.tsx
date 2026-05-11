"use client"
// components/SensorPanel.tsx

import { useSSE } from "../context/SSEContext"
import { Thermometer, Wind, Droplets, Zap } from "lucide-react"

function Gauge({
  label,
  value,
  max,
  unit,
  warnAt,
  critAt,
  icon: Icon,
}: {
  label: string
  value: number
  max: number
  unit: string
  warnAt: number
  critAt: number
  icon: React.ComponentType<{ size?: number }>
}) {
  const pct = Math.min(100, (value / max) * 100)
  const color =
    value >= critAt ? "#ef4444" : value >= warnAt ? "#f97316" : "#22c55e"

  return (
    <div className="gauge-card">
      <div className="gauge-header">
        <div className="gauge-icon" style={{ color }}>
          <Icon size={18} />
        </div>
        <span className="gauge-label">{label}</span>
      </div>
      <div className="gauge-value" style={{ color }}>
        {typeof value === "number" ? value.toFixed(1) : "—"}
        <span className="gauge-unit">{unit}</span>
      </div>
      <div className="gauge-track">
        <div
          className="gauge-fill"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <div className="gauge-thresholds">
        <span style={{ color: "#f97316" }}>⚠ {warnAt}</span>
        <span style={{ color: "#ef4444" }}>🔴 {critAt}</span>
      </div>
    </div>
  )
}

export default function SensorPanel() {
  const { latestSensor } = useSSE()

  const s = latestSensor ?? {
    temperature: 0,
    smoke: 0,
    gas: 0,
    humidity: 0,
    device_id: "—",
    lat: 22.5726,
    lng: 88.3639,
    timestamp: 0,
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <Zap size={16} className="panel-icon" />
        <h2 className="panel-title">IoT Sensors</h2>
        {latestSensor && (
          <span className="panel-badge badge-live">● LIVE</span>
        )}
      </div>
      <div className="sensor-grid">
        <Gauge
          label="Temperature"
          value={s.temperature}
          max={300}
          unit="°C"
          warnAt={60}
          critAt={150}
          icon={Thermometer}
        />
        <Gauge
          label="Smoke"
          value={s.smoke}
          max={100}
          unit="%"
          warnAt={40}
          critAt={70}
          icon={Wind}
        />
        <Gauge
          label="Gas (PPM)"
          value={s.gas}
          max={1000}
          unit="ppm"
          warnAt={300}
          critAt={600}
          icon={Zap}
        />
        <Gauge
          label="Humidity"
          value={s.humidity}
          max={100}
          unit="%"
          warnAt={90}
          critAt={100}
          icon={Droplets}
        />
      </div>
      {latestSensor && (
        <div className="sensor-meta">
          <span>Device: {latestSensor.device_id}</span>
          <span>
            📍 {latestSensor.lat.toFixed(4)}, {latestSensor.lng.toFixed(4)}
          </span>
        </div>
      )}
    </div>
  )
}
