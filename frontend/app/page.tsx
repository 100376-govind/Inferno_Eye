"use client"
// app/page.tsx — Smart root redirect

import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function HomePage() {
  const router = useRouter()
  useEffect(() => {
    const token = localStorage.getItem("ie_token")
    router.replace(token ? "/dashboard" : "/auth/login")
  }, [router])

  return null
}
