"use client"
// components/LiveMonitorPanel.tsx
// Shows 3 camera feeds: ESP32-CAM, Mobile/Drone, Uploaded Video
// Annotated frames come in via SSE as base64 JPEG

import { useSSE } from "../context/SSEContext"
import { useState, useRef } from "react"
import { Camera, Upload, Smartphone, Wifi, WifiOff, Play, Square, Flashlight, RefreshCw, Zap } from "lucide-react"
import { connectESP32, disconnectESP32, uploadVideo, connectExternal, disconnectExternal, setExternalTorch, setExternalHighFreq, switchExternalCamera } from "../lib/api"

interface FeedProps {
  title: string
  source: string
  frame?: string
  icon: React.ComponentType<{ size?: number; className?: string }>
  badge?: string
  badgeColor?: string
}

function CameraFeed({ title, source, frame, icon: Icon, badge, badgeColor }: FeedProps) {
  return (
    <div className="feed-card">
      <div className="feed-header">
        <Icon size={14} className="feed-icon" />
        <span className="feed-title">{title}</span>
        {badge && (
          <span className="feed-badge" style={{ background: badgeColor ?? "#374151" }}>
            {badge}
          </span>
        )}
      </div>
      <div className="feed-frame">
        {frame ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={`data:image/jpeg;base64,${frame}`}
            alt={`${source} annotated feed`}
            className="feed-img"
          />
        ) : (
          <div className="feed-placeholder">
            <Icon size={36} className="placeholder-icon" />
            <span>Waiting for {title} stream…</span>
            <span className="placeholder-sub">Connect a source below</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default function LiveMonitorPanel() {
  const { latestFrame, videoProgress } = useSSE()

  // ESP32 control state
  const [esp32Url, setEsp32Url]     = useState("http://192.168.1.100:81/stream")
  const [esp32Connected, setEsp32Connected] = useState(false)
  const [esp32Loading, setEsp32Loading]     = useState(false)

  // Video upload
  const fileRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [jobId, setJobId]         = useState<number | null>(null)

  // External Mobile Stream
  const [extUrl, setExtUrl]             = useState("http://192.168.1.5:8080/video")
  const [extConnected, setExtConnected] = useState(false)
  const [extLoading, setExtLoading]     = useState(false)
  const [torchOn, setTorchOn]           = useState(false)
  const [highFreq, setHighFreq]         = useState(false)

  async function handleESP32Toggle() {
    setEsp32Loading(true)
    try {
      if (esp32Connected) {
        await disconnectESP32()
        setEsp32Connected(false)
      } else {
        await connectESP32(esp32Url)
        setEsp32Connected(true)
      }
    } catch (e) {
      console.error(e)
    }
    setEsp32Loading(false)
  }

  async function handleVideoUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const job = await uploadVideo(file, 22.5726, 88.3639)
      setJobId(job.id)
    } catch (err) {
      console.error(err)
    }
    setUploading(false)
  }

  async function handleExtToggle() {
    setExtLoading(true)
    try {
      if (extConnected) {
        await disconnectExternal()
        setExtConnected(false)
      } else {
        await connectExternal(extUrl)
        setExtConnected(true)
      }
    } catch (e) {
      console.error(e)
    }
    setExtLoading(false)
  }

  async function handleTorch() {
    const next = !torchOn
    await setExternalTorch(next)
    setTorchOn(next)
  }

  async function handleHighFreq() {
    const next = !highFreq
    await setExternalHighFreq(next)
    setHighFreq(next)
  }

  async function handleSwitchCamera() {
    await switchExternalCamera()
  }

  return (
    <div className="panel monitor-panel">
      <div className="panel-header">
        <Camera size={16} className="panel-icon" />
        <h2 className="panel-title">Live Monitor</h2>
        <span className="panel-badge badge-live">● AI Vision Active</span>
      </div>

      {/* 3-column feed grid */}
      <div className="feeds-grid">
        <CameraFeed
          title="ESP32-CAM"
          source="esp32"
          frame={latestFrame["esp32"]}
          icon={Wifi}
          badge={esp32Connected ? "CONNECTED" : "OFFLINE"}
          badgeColor={esp32Connected ? "#16a34a" : "#6b7280"}
        />
        <CameraFeed
          title="Mobile / Drone"
          source="mobile"
          frame={latestFrame["mobile"]}
          icon={Smartphone}
          badge={extConnected ? "CONNECTED" : "OFFLINE"}
          badgeColor={extConnected ? "#16a34a" : "#6b7280"}
        />
        <CameraFeed
          title="Uploaded Video"
          source="upload"
          frame={latestFrame["upload"]}
          icon={Upload}
          badge={jobId ? `Job #${jobId}` : "Upload"}
          badgeColor="#0e7490"
        />
      </div>

      {/* Video upload progress */}
      {videoProgress && (
        <div className="video-progress">
          <div className="vp-label">
            <span>Processing Job #{videoProgress.jobId}</span>
            <span>{videoProgress.pct}%</span>
          </div>
          <div className="vp-track">
            <div className="vp-fill" style={{ width: `${videoProgress.pct}%` }} />
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="monitor-controls">
        {/* ESP32 */}
        <div className="control-group">
          <label className="control-label">ESP32-CAM Stream URL</label>
          <div className="control-row">
            <input
              type="text"
              className="control-input"
              value={esp32Url}
              onChange={(e) => setEsp32Url(e.target.value)}
              placeholder="http://192.168.x.x:81/stream"
            />
            <button
              className={`ctrl-btn ${esp32Connected ? "btn-red" : "btn-green"}`}
              onClick={handleESP32Toggle}
              disabled={esp32Loading}
            >
              {esp32Loading ? (
                "…"
              ) : esp32Connected ? (
                <><Square size={13} /> Stop</>
              ) : (
                <><Play size={13} /> Connect</>
              )}
            </button>
          </div>
        </div>

        {/* Video upload */}
        <div className="control-group">
          <label className="control-label">Upload Video for AI Analysis</label>
          <div className="control-row">
            <input
              type="text"
              className="control-input"
              value={uploading ? "Uploading…" : (jobId ? `Job #${jobId} queued` : "No file selected")}
              readOnly
              onClick={() => fileRef.current?.click()}
            />
            <button
              className="ctrl-btn btn-blue"
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
            >
              <Upload size={13} /> {uploading ? "…" : "Browse"}
            </button>
            <input
              ref={fileRef}
              type="file"
              accept="video/mp4,video/*"
              className="hidden"
              onChange={handleVideoUpload}
            />
          </div>
        </div>

        {/* Mobile camera link */}
        <div className="control-group">
          <label className="control-label">IP Camera Stream (Mobile App)</label>
          <div className="control-row" style={{ marginBottom: extConnected ? '0.5rem' : '0' }}>
            <input
              type="text"
              className="control-input"
              value={extUrl}
              onChange={(e) => setExtUrl(e.target.value)}
              placeholder="http://192.168.x.x:8080/video"
            />
            <button
              className={`ctrl-btn ${extConnected ? "btn-red" : "btn-green"}`}
              onClick={handleExtToggle}
              disabled={extLoading}
            >
              {extLoading ? (
                "…"
              ) : extConnected ? (
                <><Square size={13} /> Stop</>
              ) : (
                <><Play size={13} /> Connect</>
              )}
            </button>
          </div>
          {extConnected && (
            <div className="control-row">
              <button className={`ctrl-btn ${torchOn ? "btn-blue" : ""}`} onClick={handleTorch}>
                <Flashlight size={13} /> {torchOn ? "Torch Off" : "Torch"}
              </button>
              <button className="ctrl-btn" onClick={handleSwitchCamera}>
                <RefreshCw size={13} /> Flip
              </button>
              <button className={`ctrl-btn ${highFreq ? "btn-purple" : ""}`} onClick={handleHighFreq}>
                <Zap size={13} /> {highFreq ? "Normal Freq" : "High Freq"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
