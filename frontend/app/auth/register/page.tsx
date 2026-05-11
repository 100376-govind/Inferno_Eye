"use client"
// app/auth/register/page.tsx — Admin Registration Page

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Flame, User, Mail, Lock, Eye, EyeOff, ArrowRight, UserPlus, CheckCircle } from "lucide-react"

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export default function RegisterPage() {
  const router = useRouter()
  const [form, setForm] = useState({
    name: "", email: "", username: "", password: "", confirmPassword: "",
  })
  const [showPwd, setShowPwd] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }))

  const validate = () => {
    if (!form.name.trim() || form.name.trim().length < 2) return "Full name must be at least 2 characters."
    if (!form.email.includes("@")) return "Please enter a valid email address."
    if (form.username.trim().length < 3) return "Username must be at least 3 characters."
    if (form.password.length < 6) return "Password must be at least 6 characters."
    if (form.password !== form.confirmPassword) return "Passwords do not match."
    return ""
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const err = validate()
    if (err) { setError(err); return }

    setError("")
    setLoading(true)
    try {
      const res = await fetch(`${API}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name.trim(),
          username: form.username.trim(),
          email: form.email.trim(),
          password: form.password,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? "Registration failed")
      
      // Store info for OTP page
      sessionStorage.setItem("otp_username", form.username.trim())
      sessionStorage.setItem("otp_masked_email", data.masked_email ?? "")
      router.push("/auth/verify-otp")
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      {/* Background glow */}
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

        <h1 className="auth-title">Create Admin Account</h1>
        <p className="auth-subtitle">Verify your email to complete registration</p>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>

            {/* Full Name */}
            <div className="auth-field">
              <label className="auth-label" htmlFor="reg-name">Full Name</label>
              <div className="auth-input-wrap">
                <User size={16} className="auth-input-icon" />
                <input
                  id="reg-name"
                  type="text"
                  className="auth-input"
                  placeholder="John Doe"
                  value={form.name}
                  onChange={set("name")}
                  autoComplete="name"
                  required
                />
              </div>
            </div>

            {/* Email */}
            <div className="auth-field">
              <label className="auth-label" htmlFor="reg-email">Email Address</label>
              <div className="auth-input-wrap">
                <Mail size={16} className="auth-input-icon" />
                <input
                  id="reg-email"
                  type="email"
                  className="auth-input"
                  placeholder="admin@example.com"
                  value={form.email}
                  onChange={set("email")}
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            {/* Username */}
            <div className="auth-field">
              <label className="auth-label" htmlFor="reg-username">Username</label>
              <div className="auth-input-wrap">
                <span className="auth-input-icon auth-at">@</span>
                <input
                  id="reg-username"
                  type="text"
                  className="auth-input"
                  placeholder="admin_user"
                  value={form.username}
                  onChange={set("username")}
                  autoComplete="username"
                  required
                />
              </div>
            </div>

            {/* Password */}
            <div className="auth-field">
              <label className="auth-label" htmlFor="reg-password">Password</label>
              <div className="auth-input-wrap">
                <Lock size={16} className="auth-input-icon" />
                <input
                  id="reg-password"
                  type={showPwd ? "text" : "password"}
                  className="auth-input"
                  placeholder="Min. 6 characters"
                  value={form.password}
                  onChange={set("password")}
                  autoComplete="new-password"
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

            {/* Confirm Password */}
            <div className="auth-field">
              <label className="auth-label" htmlFor="reg-confirm">Confirm Password</label>
              <div className="auth-input-wrap">
                <Lock size={16} className="auth-input-icon" />
                <input
                  id="reg-confirm"
                  type={showConfirm ? "text" : "password"}
                  className="auth-input"
                  placeholder="Repeat your password"
                  value={form.confirmPassword}
                  onChange={set("confirmPassword")}
                  autoComplete="new-password"
                  required
                />
                <button
                  type="button"
                  className="auth-toggle-pwd"
                  onClick={() => setShowConfirm((v) => !v)}
                  aria-label={showConfirm ? "Hide confirm password" : "Show confirm password"}
                >
                  {showConfirm ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            {error && <div className="auth-error" role="alert">{error}</div>}

            <button id="btn-register" type="submit" className="auth-btn" disabled={loading}>
              {loading ? (
                <span className="auth-spinner" />
              ) : (
                <>
                  <UserPlus size={16} />
                  Create Account
                  <ArrowRight size={16} className="auth-btn-arrow" />
                </>
              )}
            </button>

            <p className="auth-switch">
              Already have an account?{" "}
              <a href="/auth/login" className="auth-link">Sign In</a>
            </p>
          </form>
      </div>
    </div>
  )
}
