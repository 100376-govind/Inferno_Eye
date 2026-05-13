// types/index.ts — mirrors backend schemas.py exactly

export interface BBox { x: number; y: number; w: number; h: number }

export interface Detection {
  label: "fire" | "smoke" | string
  confidence: number
  bbox: BBox
}

export interface DetectionResult {
  source: "esp32" | "mobile" | "upload" | string
  detections: Detection[]
  annotated_frame?: string   // base64 JPEG
  lat: number
  lng: number
  timestamp: number
}

export interface SensorReading {
  id?: number
  device_id: string
  temperature: number
  smoke: number
  gas: number
  humidity: number
  ds18b20_temp: number
  lat: number
  lng: number
  timestamp: number
}

export interface AlertOut {
  id: number
  alert_type: string
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | string
  message: string
  camera_source: string
  confidence: number
  lat: number
  lng: number
  acknowledged: boolean
  timestamp: number
}

export interface IncidentOut {
  id: number
  camera_source: string
  confidence: number
  severity: string
  label: string
  lat: number
  lng: number
  response_recommendation: string
  timestamp: number
}

export interface BlockOut {
  id: number
  index: number
  event_type: string
  data: Record<string, unknown>
  prev_hash: string
  block_hash: string
  nonce: number
  timestamp: number
}

export interface VideoJobOut {
  id: number
  filename: string
  status: "queued" | "processing" | "done" | "error" | string
  total_frames: number
  processed_frames: number
  detections_count: number
  result_data: unknown
  timestamp: number
}

export interface HealthStatus {
  status: string
  yolo: string
  esp32: { running: boolean; url: string | null }
  sse_subscribers: number
}

// SSE event envelope — matches backend event_bus: { type, payload, ts }
export interface SSEEvent {
  type:
    | "frame"
    | "sensor"
    | "alert"
    | "incident"
    | "blockchain"
    | "camera_status"
    | "video_progress"
    | "alert_ack"
    | "gps"
  payload: unknown
  ts: number
}

export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"

export interface MapPin {
  lat: number
  lng: number
  label: string
  severity: Severity | string
  timestamp: number
}
