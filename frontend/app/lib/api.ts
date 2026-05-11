// lib/api.ts — typed REST helpers for FastAPI backend

import type {
  AlertOut,
  IncidentOut,
  BlockOut,
  VideoJobOut,
  HealthStatus,
  SensorReading,
} from "../types"

export const API = "http://localhost:8000"

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { cache: "no-store" })
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`)
  return res.json() as Promise<T>
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`)
  return res.json() as Promise<T>
}

// ── Health ─────────────────────────────────────────────────────────────────
export const fetchHealth = () => get<HealthStatus>("/health")

// ── Alerts ─────────────────────────────────────────────────────────────────
export const fetchLiveAlerts = () => get<AlertOut[]>("/alerts/live")
export const fetchAlertHistory = (limit = 50) =>
  get<AlertOut[]>(`/alerts/history?limit=${limit}`)
export const acknowledgeAlert = (id: number) =>
  post<{ ok: boolean }>(`/alerts/${id}/acknowledge`, {})

// ── Incidents ──────────────────────────────────────────────────────────────
export const fetchIncidents = (limit = 50) =>
  get<IncidentOut[]>(`/incidents?limit=${limit}`)

// ── Blockchain ─────────────────────────────────────────────────────────────
export const fetchBlockchain = () => get<BlockOut[]>("/blockchain/log")
export const validateChain = () =>
  get<{ valid: boolean; length: number }>("/blockchain/validate")

// ── Detections ─────────────────────────────────────────────────────────────
export const fetchLatestDetection = () =>
  get<{ source: string; label: string; confidence: number; timestamp: number } | null>(
    "/detections/latest"
  )

// ── Sensors ────────────────────────────────────────────────────────────────
export const fetchLatestSensor = () =>
  get<SensorReading | null>("/sensors/latest")
export const sendSensorReading = (payload: Omit<SensorReading, "id" | "timestamp">) =>
  post<SensorReading>("/sensors/ingest", payload)

// ── Camera ─────────────────────────────────────────────────────────────────
export const connectESP32 = (stream_url: string) =>
  post<{ ok: boolean; url: string }>("/camera/esp32/connect", { stream_url })
export const disconnectESP32 = () =>
  post<{ ok: boolean }>("/camera/esp32/disconnect", {})
export const getESP32Status = () =>
  get<{ running: boolean; url: string | null }>("/camera/esp32/status")

// ── External Phone Camera ──────────────────────────────────────────────────
export const connectExternal = (stream_url: string) =>
  post<{ ok: boolean; url: string }>("/camera/external/connect", { stream_url })
export const disconnectExternal = () =>
  post<{ ok: boolean }>("/camera/external/disconnect", {})
export const setExternalTorch = (enabled: boolean) =>
  post<{ ok: boolean }>("/camera/external/torch?enabled=" + enabled, {})
export const setExternalHighFreq = (enabled: boolean) =>
  post<{ ok: boolean }>(`/camera/external/high_freq?enabled=${enabled}`, {})
export const switchExternalCamera = () =>
  post<{ ok: boolean }>("/camera/external/camera/switch", {})

export const sendMobileFrame = (frame: string, lat: number, lng: number) =>
  post<{ detections: number }>("/camera/mobile/frame", { frame, lat, lng })

// ── Video ──────────────────────────────────────────────────────────────────
export const uploadVideo = async (
  file: File,
  lat: number,
  lng: number
): Promise<VideoJobOut> => {
  const form = new FormData()
  form.append("file", file)
  form.append("lat", lat.toString())
  form.append("lng", lng.toString())
  const res = await fetch(`${API}/video/upload`, { method: "POST", body: form })
  if (!res.ok) throw new Error(`Video upload → ${res.status}`)
  return res.json()
}
export const fetchVideoJob = (id: number) =>
  get<VideoJobOut>(`/video/job/${id}`)
