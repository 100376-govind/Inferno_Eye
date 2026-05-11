"use client"
// context/AuthContext.tsx — admin authentication state

import React, { createContext, useContext, useState, useEffect, useCallback } from "react"

const API = "http://localhost:8000/auth"

export interface AdminUser {
  username: string
  email: string
  role: string
  token: string
}

interface AuthContextType {
  user: AdminUser | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser]       = useState<AdminUser | null>(null)
  const [loading, setLoading] = useState(true)

  // Rehydrate from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem("inferno_admin")
      if (stored) setUser(JSON.parse(stored))
    } catch { /* ignore */ }
    setLoading(false)
  }, [])

  const persist = (u: AdminUser) => {
    setUser(u)
    localStorage.setItem("inferno_admin", JSON.stringify(u))
  }

  const login = useCallback(async (username: string, password: string) => {
    const res = await fetch(`${API}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail ?? "Login failed")
    }
    persist(await res.json())
  }, [])

  const register = useCallback(async (username: string, email: string, password: string) => {
    const res = await fetch(`${API}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail ?? "Registration failed")
    }
    persist(await res.json())
  }, [])

  const logout = useCallback(() => {
    setUser(null)
    localStorage.removeItem("inferno_admin")
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be inside AuthProvider")
  return ctx
}
