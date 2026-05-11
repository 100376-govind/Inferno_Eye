"use client"
// app/auth/verify-otp/page.tsx — OTP Verification Page

import { useState, useEffect, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Flame, RefreshCw, ArrowRight, ShieldCheck, CheckCircle } from "lucide-react"

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
const OTP_LENGTH = 6
const RESEND_COOLDOWN = 60 // seconds

export default function VerifyOTPPage() {
  const router = useRouter()
  const [digits, setDigits] = useState<string[]>(Array(OTP_LENGTH).fill(""))
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [resendCooldown, setResendCooldown] = useState(0)
  const [username, setUsername] = useState("")
  const [maskedEmail, setMaskedEmail] = useState("")
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    const u = sessionStorage.getItem("otp_username") ?? ""
    const m = sessionStorage.getItem("otp_masked_email") ?? ""
    if (!u) { router.replace("/auth/login"); return }
    setUsername(u)
    setMaskedEmail(m)
    // Focus first box
    inputRefs.current[0]?.focus()
  }, [router])

  const startCooldown = useCallback(() => {
    setResendCooldown(RESEND_COOLDOWN)
    if (timerRef.current) clearInterval(timerRef.current)
    timerRef.current = setInterval(() => {
      setResendCooldown((c) => {
        if (c <= 1) { clearInterval(timerRef.current!); return 0 }
        return c - 1
      })
    }, 1000)
  }, [])

  // Clean up timer on unmount
  useEffect(() => () => { if (timerRef.current) clearInterval(timerRef.current) }, [])

  const handleDigitChange = (index: number, value: string) => {
    const ch = value.replace(/\D/g, "").slice(-1)
    const next = [...digits]
    next[index] = ch
    setDigits(next)
    setError("")
    if (ch && index < OTP_LENGTH - 1) {
      inputRefs.current[index + 1]?.focus()
    }
    // Auto-submit when all filled
    if (ch && next.every((d) => d !== "")) {
      verifyOTP(next.join(""))
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, OTP_LENGTH)
    if (pasted.length === OTP_LENGTH) {
      const next = pasted.split("")
      setDigits(next)
      inputRefs.current[OTP_LENGTH - 1]?.focus()
      verifyOTP(pasted)
    }
  }

  const verifyOTP = async (otpCode: string) => {
    if (otpCode.length !== OTP_LENGTH) { setError("Please enter all 6 digits."); return }
    setError("")
    setLoading(true)
    try {
      const res = await fetch(`${API}/auth/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, otp: otpCode }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? "Invalid OTP")

      // Save session
      localStorage.setItem("ie_token", data.token)
      localStorage.setItem("ie_user", JSON.stringify({
        username: data.username,
        name: data.name,
        email: data.email,
        role: data.role,
      }))
      sessionStorage.removeItem("otp_username")
      sessionStorage.removeItem("otp_masked_email")

      setSuccess(true)
      setTimeout(() => router.replace("/dashboard"), 1000)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Verification failed")
      setDigits(Array(OTP_LENGTH).fill(""))
      inputRefs.current[0]?.focus()
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    if (resendCooldown > 0) return
    const pwd = prompt("Re-enter your password to resend OTP:")
    if (!pwd) return
    try {
      const res = await fetch(`${API}/auth/send-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password: pwd }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? "Failed to resend")
      setMaskedEmail(data.masked_email ?? maskedEmail)
      setDigits(Array(OTP_LENGTH).fill(""))
      setError("")
      startCooldown()
      inputRefs.current[0]?.focus()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Resend failed")
    }
  }

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    verifyOTP(digits.join(""))
  }

  return (
    <div className="auth-page">
      <div className="auth-glow auth-glow-1" />
      <div className="auth-glow auth-glow-2" />

      <div className="auth-card">
        {/* Logo */}
        <div className="auth-logo">
          <div className="auth-logo-icon">
            <Flame size={28} />
          </div>
          <div>
            <div className="auth-brand">INFERNO EYE</div>
            <div className="auth-brand-sub">AI Fire Command Center</div>
          </div>
        </div>

        <div className="auth-divider" />

        {success ? (
          <div className="auth-success" style={{ padding: "32px 0" }}>
            <CheckCircle size={48} style={{ color: "var(--safe)" }} />
            <span style={{ fontSize: "16px", fontWeight: 600 }}>Verified! Entering dashboard…</span>
          </div>
        ) : (
          <>
            <div className="otp-shield-icon">
              <ShieldCheck size={36} />
            </div>
            <h1 className="auth-title">Verify OTP</h1>
            <p className="auth-subtitle">
              Enter the 6-digit code sent to<br />
              <strong className="otp-email-mask">{maskedEmail || "your email"}</strong>
            </p>

            <form className="auth-form" onSubmit={handleManualSubmit} noValidate>
              {/* OTP digit boxes */}
              <div className="otp-boxes" onPaste={handlePaste}>
                {digits.map((d, i) => (
                  <input
                    key={i}
                    id={`otp-box-${i}`}
                    ref={(el) => { inputRefs.current[i] = el }}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={d}
                    onChange={(e) => handleDigitChange(i, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(i, e)}
                    className={`otp-box ${d ? "otp-box-filled" : ""} ${error ? "otp-box-error" : ""}`}
                    disabled={loading}
                    aria-label={`OTP digit ${i + 1}`}
                    autoComplete="one-time-code"
                  />
                ))}
              </div>

              {error && <div className="auth-error" role="alert">{error}</div>}

              <button id="btn-verify-otp" type="submit" className="auth-btn" disabled={loading || digits.some((d) => !d)}>
                {loading ? (
                  <span className="auth-spinner" />
                ) : (
                  <>
                    Verify & Enter Dashboard
                    <ArrowRight size={16} className="auth-btn-arrow" />
                  </>
                )}
              </button>

              {/* Resend */}
              <div className="otp-resend-row">
                <span className="auth-switch">Didn&apos;t receive it?</span>
                <button
                  id="btn-resend-otp"
                  type="button"
                  className={`otp-resend-btn ${resendCooldown > 0 ? "otp-resend-disabled" : ""}`}
                  onClick={handleResend}
                  disabled={resendCooldown > 0}
                >
                  <RefreshCw size={13} />
                  {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : "Resend OTP"}
                </button>
              </div>

              <p className="auth-switch" style={{ textAlign: "center" }}>
                <a href="/auth/login" className="auth-link">← Back to Sign In</a>
              </p>
            </form>
          </>
        )}
      </div>
    </div>
  )
}
