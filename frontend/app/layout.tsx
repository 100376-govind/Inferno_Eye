import type { Metadata } from "next"
import "./globals.css"
import { SSEProvider } from "./context/SSEContext"
import FireAlertToast from "./components/FireAlertToast"

export const metadata: Metadata = {
  title: "Inferno Eye — AI Fire Detection Command Center",
  description:
    "Real-time fire detection & emergency response using YOLOv8 AI, ESP32-CAM, IoT sensors, and blockchain logging. Monitoring Kolkata, West Bengal.",
  keywords: "fire detection, AI, IoT, ESP32-CAM, YOLOv8, blockchain, emergency response",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          crossOrigin=""
        />
      </head>
      <body>
        <SSEProvider>
          <FireAlertToast />
          {children}
        </SSEProvider>
      </body>
    </html>
  )
}
