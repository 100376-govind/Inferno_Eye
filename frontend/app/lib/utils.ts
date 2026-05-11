// lib/utils.ts

export function severityColor(severity: string): string {
  switch (severity?.toUpperCase()) {
    case "CRITICAL": return "#ef4444"
    case "HIGH":     return "#f97316"
    case "MEDIUM":   return "#eab308"
    case "LOW":      return "#22c55e"
    default:         return "#6b7280"
  }
}

export function severityBg(severity: string): string {
  switch (severity?.toUpperCase()) {
    case "CRITICAL": return "bg-red-600/20 border-red-600/50 text-red-400"
    case "HIGH":     return "bg-orange-600/20 border-orange-600/50 text-orange-400"
    case "MEDIUM":   return "bg-yellow-500/20 border-yellow-500/50 text-yellow-300"
    case "LOW":      return "bg-green-600/20 border-green-600/50 text-green-400"
    default:         return "bg-gray-700/30 border-gray-600/40 text-gray-400"
  }
}

export function formatTs(ts: number): string {
  if (!ts) return "—"
  const d = new Date(ts * 1000)
  return d.toLocaleTimeString("en-IN", { hour12: false })
}

export function formatDateTime(ts: number): string {
  if (!ts) return "—"
  const d = new Date(ts * 1000)
  return d.toLocaleString("en-IN", { hour12: false })
}

export function shortHash(hash: string): string {
  if (!hash) return "—"
  return `${hash.slice(0, 8)}…${hash.slice(-8)}`
}

export function pct(a: number, b: number): number {
  return b === 0 ? 0 : Math.round((a / b) * 100)
}

export function clamp(val: number, min: number, max: number): number {
  return Math.min(Math.max(val, min), max)
}
