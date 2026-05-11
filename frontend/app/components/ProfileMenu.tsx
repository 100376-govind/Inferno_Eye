"use client"
// components/ProfileMenu.tsx — User profile dropdown with sign-out confirmation

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { User, ChevronDown, LogOut, Shield, X } from "lucide-react"

interface UserInfo {
  username: string
  name: string
  email: string
  role: string
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join("")
}

export default function ProfileMenu() {
  const router = useRouter()
  const [user, setUser] = useState<UserInfo | null>(null)
  const [open, setOpen] = useState(false)
  const [showSignOutModal, setShowSignOutModal] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    try {
      const raw = localStorage.getItem("ie_user")
      if (raw) setUser(JSON.parse(raw))
    } catch { /* ignore */ }
  }, [])

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  const handleSignOut = () => {
    localStorage.removeItem("ie_token")
    localStorage.removeItem("ie_user")
    setShowSignOutModal(false)
    router.replace("/auth/login")
  }

  if (!user) return null

  const initials = getInitials(user.name || user.username)
  const displayName = user.name || user.username

  return (
    <>
      {/* Profile Avatar Button */}
      <div className="profile-menu-wrap" ref={menuRef}>
        <button
          id="btn-profile-menu"
          className={`profile-avatar-btn ${open ? "profile-avatar-open" : ""}`}
          onClick={() => setOpen((v) => !v)}
          aria-haspopup="true"
          aria-expanded={open}
          title="Profile"
        >
          <div className="profile-avatar">
            {initials || <User size={14} />}
          </div>
          <span className="profile-username">{user.username}</span>
          <ChevronDown size={14} className={`profile-chevron ${open ? "profile-chevron-open" : ""}`} />
        </button>

        {/* Dropdown */}
        {open && (
          <div className="profile-dropdown" role="menu">
            {/* User info card */}
            <div className="profile-info-card">
              <div className="profile-avatar profile-avatar-lg">
                {initials || <User size={20} />}
              </div>
              <div className="profile-info-text">
                <div className="profile-full-name">{displayName}</div>
                <div className="profile-email">{user.email}</div>
                <div className="profile-role-badge">
                  <Shield size={10} />
                  {user.role.toUpperCase()}
                </div>
              </div>
            </div>

            <div className="profile-menu-divider" />

            {/* Username row */}
            <div className="profile-menu-row">
              <span className="profile-menu-label">Username</span>
              <span className="profile-menu-value">@{user.username}</span>
            </div>

            <div className="profile-menu-divider" />

            {/* Sign Out */}
            <button
              id="btn-signout-trigger"
              className="profile-signout-btn"
              role="menuitem"
              onClick={() => { setOpen(false); setShowSignOutModal(true) }}
            >
              <LogOut size={15} />
              Sign Out
            </button>
          </div>
        )}
      </div>

      {/* ── Sign-Out Confirmation Modal ────────────────────────────────────── */}
      {showSignOutModal && (
        <div className="signout-overlay" role="dialog" aria-modal="true" aria-label="Sign out confirmation">
          <div className="signout-modal">
            <button
              id="btn-close-signout-modal"
              className="signout-close"
              onClick={() => setShowSignOutModal(false)}
              aria-label="Cancel"
            >
              <X size={16} />
            </button>

            <div className="signout-icon">
              <LogOut size={28} />
            </div>
            <h2 className="signout-title">Sign Out?</h2>
            <p className="signout-body">
              You are about to sign out of <strong>Inferno Eye</strong>.<br />
              Active monitoring will continue in the background.
            </p>

            <div className="signout-actions">
              <button
                id="btn-cancel-signout"
                className="signout-btn-cancel"
                onClick={() => setShowSignOutModal(false)}
              >
                Stay Signed In
              </button>
              <button
                id="btn-confirm-signout"
                className="signout-btn-confirm"
                onClick={handleSignOut}
              >
                <LogOut size={15} />
                Yes, Sign Out
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
