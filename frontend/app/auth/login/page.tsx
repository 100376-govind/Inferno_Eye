"use client"
// app/auth/login/page.tsx — Admin Login Page (triggers OTP)

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Flame, Lock, Eye, EyeOff, ArrowRight, ShieldCheck } from "lucide-react"

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export default function LoginPage() {
  const router = useRouter()
  const [form, setForm] = useState({ username: "", password: "" })
  const [showPwd, setShowPwd] = useState(false)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.username.trim()) { setError("Username is required."); return }
    if (!form.password) { setError("Password is required."); return }

    setError("")
    setLoading(true)
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: form.username.trim(), password: form.password }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? "Login failed")

      // Save session
      localStorage.setItem("ie_token", data.token)
      localStorage.setItem("ie_user", JSON.stringify({
        username: data.username,
        name: data.name,
        email: data.email,
        role: data.role,
      }))

      router.replace("/dashboard")
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed")
    } finally {
      setLoading(false)
    }
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

        <h1 className="auth-title">Admin Sign In</h1>
        <p className="auth-subtitle">Welcome back! Please enter your credentials</p>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          {/* Username */}
          <div className="auth-field">
            <label className="auth-label" htmlFor="login-username">Username</label>
            <div className="auth-input-wrap">
              <span className="auth-input-icon auth-at">@</span>
              <input
                id="login-username"
                type="text"
                className="auth-input"
                placeholder="your_username"
                value={form.username}
                onChange={set("username")}
                autoComplete="username"
                required
              />
            </div>
          </div>

          {/* Password */}
          <div className="auth-field">
            <label className="auth-label" htmlFor="login-password">Password</label>
            <div className="auth-input-wrap">
              <Lock size={16} className="auth-input-icon" />
              <input
                id="login-password"
                type={showPwd ? "text" : "password"}
                className="auth-input"
                placeholder="Your password"
                value={form.password}
                onChange={set("password")}
                autoComplete="current-password"
                required
              />
              <button
                type="button"
                className="auth-toggle-pwd"
                onClick={() => setShowPwd((v) => !v)}
                aria-label={showPwd ? "Hide password" : "Show password"}
              >
                {showPwd ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          {error && <div className="auth-error" role="alert">{error}</div>}

          <button id="btn-login" type="submit" className="auth-btn" disabled={loading}>
            {loading ? (
              <span className="auth-spinner" />
            ) : (
              <>
                Sign In
                <ArrowRight size={16} className="auth-btn-arrow" />
              </>
            )}
          </button>

          <p className="auth-switch">
            Don&apos;t have an account?{" "}
            <a href="/auth/register" className="auth-link">Create one</a>
          </p>
        </form>
      </div>
    </div>
  )
}
