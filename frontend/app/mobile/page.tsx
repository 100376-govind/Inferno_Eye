"use client"
// app/mobile/page.tsx — Mobile camera streaming page
// Opens device rear camera, captures JPEG frames via canvas,
// POSTs base64 to /camera/mobile/frame every 2 seconds with GPS coordinates.

import { useEffect, useRef, useState } from "react"
import { sendMobileFrame } from "../lib/api"
import { Camera, Wifi, WifiOff, Flame } from "lucide-react"

export default function MobilePage() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [active, setActive]         = useState(false)
  const [detCount, setDetCount]     = useState(0)
  const [fps, setFps]               = useState("—")
  const [error, setError]           = useState("")
  const streamRef   = useRef<MediaStream | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Get real GPS location
  const [pos, setPos] = useState({ lat: 22.5726, lng: 88.3639 })
  useEffect(() => {
    navigator.geolocation?.getCurrentPosition(
      (p) => setPos({ lat: p.coords.latitude, lng: p.coords.longitude }),
      () => {} // fallback to Kolkata default
    )
  }, [])

  async function startCamera() {
    setError("")
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: 640, height: 480 },
        audio: false,
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      streamRef.current = stream
      setActive(true)

      let frameCount = 0
      const start = Date.now()

      intervalRef.current = setInterval(async () => {
        if (!canvasRef.current || !videoRef.current) return
        const ctx = canvasRef.current.getContext("2d")!
        canvasRef.current.width  = 640
        canvasRef.current.height = 480
        ctx.drawImage(videoRef.current, 0, 0, 640, 480)
        const b64 = canvasRef.current
          .toDataURL("image/jpeg", 0.7)
          .split(",")[1]

        try {
          const result = await sendMobileFrame(b64, pos.lat, pos.lng)
          if (result.detections > 0) {
            setDetCount((c) => c + result.detections)
          }
        } catch { /* network error — ignore, retry next interval */ }

        frameCount++
        const elapsed = (Date.now() - start) / 1000
        setFps((frameCount / elapsed).toFixed(1))
      }, 2000)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Camera access denied")
    }
  }

  function stopCamera() {
    if (intervalRef.current) clearInterval(intervalRef.current)
    streamRef.current?.getTracks().forEach((t) => t.stop())
    if (videoRef.current) videoRef.current.srcObject = null
    streamRef.current = null
    setActive(false)
  }

  return (
    <div className="mobile-page">
      <div className="mobile-header">
        <Flame size={24} className="brand-flame" />
        <h1 className="mobile-title">Inferno Eye — Mobile Camera</h1>
      </div>

      <div className="mobile-status">
        <div className={`mob-pill ${active ? "mob-live" : "mob-idle"}`}>
          {active ? <Wifi size={14} /> : <WifiOff size={14} />}
          {active ? "STREAMING" : "IDLE"}
        </div>
        <div className="mob-pill">
          📍 {pos.lat.toFixed(4)}, {pos.lng.toFixed(4)}
        </div>
        {active && (
          <div className="mob-pill">🔥 {detCount} detections · {fps} fps</div>
        )}
      </div>

      <div className="mobile-feed">
        {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
        <video ref={videoRef} className="mob-video" muted playsInline />
        <canvas ref={canvasRef} className="hidden" />
        {!active && (
          <div className="mob-placeholder">
            <Camera size={48} />
            <span>Tap Start to begin streaming</span>
          </div>
        )}
      </div>

      {error && <p className="mob-error">⚠ {error}</p>}

      <div className="mob-controls">
        {!active ? (
          <button className="mob-btn mob-btn-start" onClick={startCamera}>
            <Camera size={18} /> Start Camera
          </button>
        ) : (
          <button className="mob-btn mob-btn-stop" onClick={stopCamera}>
            ■ Stop Stream
          </button>
        )}
      </div>

      <p className="mob-info">
        Frames are sent to the Inferno Eye server every 2 seconds for AI fire/smoke detection.
        Keep this page open while monitoring. Your GPS location is attached to each frame.
      </p>
    </div>
  )
}
