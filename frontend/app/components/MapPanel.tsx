"use client"
// components/MapPanel.tsx
// Leaflet map centred on Kolkata — renders SSE fire pins + real GPS

import { useSSE } from "../context/SSEContext"
import { useEffect, useRef } from "react"
import { MapPin } from "lucide-react"
import { severityColor } from "../lib/utils"

// Kolkata HQ coordinates (from .env DEFAULT_LAT/LNG)
const KOLKATA = { lat: 22.5726, lng: 88.3639 }

export default function MapPanel() {
  const { pins } = useSSE()
  const mapRef    = useRef<HTMLDivElement>(null)
  const initedRef = useRef(false)          // guard against StrictMode double-invoke
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const leafRef   = useRef<any>(null)      // holds L.Map instance

  // Init Leaflet once on mount
  useEffect(() => {
    if (typeof window === "undefined") return
    if (initedRef.current) return           // already initialised (StrictMode guard)
    initedRef.current = true

    // Dynamic import to avoid SSR issues
    import("leaflet").then((L) => {
      if (!mapRef.current) return
      // If leaflet already bound this container (e.g. hot reload), remove it first
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const existingMap = (mapRef.current as any)._leaflet_id
      if (existingMap) return   // already has a live map — skip

      // Fix default marker icons (Leaflet webpack issue)
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (L.Icon.Default.prototype as any)._getIconUrl
      L.Icon.Default.mergeOptions({
        iconRetinaUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      })

      const map = L.map(mapRef.current, {
        center: [KOLKATA.lat, KOLKATA.lng],
        zoom: 13,
        zoomControl: true,
      })

      // OpenStreetMap tile layer
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution:
          '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 19,
      }).addTo(map)

      // HQ marker
      const hqIcon = L.divIcon({
        html: `<div style="background:#3b82f6;border:2px solid #fff;border-radius:50%;width:18px;height:18px;display:flex;align-items:center;justify-content:center;font-size:10px">🏢</div>`,
        className: "",
        iconSize: [18, 18],
        iconAnchor: [9, 9],
      })
      L.marker([KOLKATA.lat, KOLKATA.lng], { icon: hqIcon })
        .addTo(map)
        .bindPopup("<b>Inferno Eye HQ</b><br/>Kolkata, West Bengal")

      leafRef.current = { map, L, markers: [] }
    })

    return () => {
      leafRef.current?.map?.remove()
      leafRef.current = null
    }
  }, [])

  // Add a new fire pin whenever pins state changes
  useEffect(() => {
    if (!leafRef.current || pins.length === 0) return
    const { map, L, markers } = leafRef.current
    const latestPin = pins[0]
    const color = severityColor(latestPin.severity)

    const fireIcon = L.divIcon({
      html: `<div style="background:${color};border:2px solid #fff;border-radius:50%;width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-size:13px;box-shadow:0 0 8px ${color}88">🔥</div>`,
      className: "",
      iconSize: [22, 22],
      iconAnchor: [11, 11],
    })

    const marker = L.marker([latestPin.lat, latestPin.lng], { icon: fireIcon })
      .addTo(map)
      .bindPopup(
        `<b>${latestPin.label.toUpperCase()}</b><br/>` +
        `Severity: ${latestPin.severity}<br/>` +
        `Lat: ${latestPin.lat.toFixed(5)}<br/>` +
        `Lng: ${latestPin.lng.toFixed(5)}`
      )

    markers.push(marker)

    // Keep only last 20 markers
    if (markers.length > 20) {
      const old = markers.shift()
      map.removeLayer(old)
    }

    // Pan map to latest pin
    map.panTo([latestPin.lat, latestPin.lng], { animate: true, duration: 0.8 })

    leafRef.current.markers = markers
  }, [pins])

  return (
    <div className="panel map-panel">
      <div className="panel-header">
        <MapPin size={16} className="panel-icon text-blue-400" />
        <h2 className="panel-title">GPS Incident Map</h2>
        <span className="panel-badge" style={{ background: "#1e3a5f", color: "#60a5fa" }}>
          Kolkata, WB
        </span>
        <span className="panel-badge badge-count">{pins.length} pins</span>
      </div>
      {/* Leaflet container */}
      <div ref={mapRef} className="map-container" />
      <p className="map-footer">
        Real-time fire/smoke detection pins · OpenStreetMap · Click pin for details
      </p>
    </div>
  )
}
