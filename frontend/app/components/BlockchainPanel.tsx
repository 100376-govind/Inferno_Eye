"use client"
// components/BlockchainPanel.tsx

import { useSSE } from "../context/SSEContext"
import { useEffect, useState } from "react"
import { Link2, CheckCircle, XCircle } from "lucide-react"
import { fetchBlockchain, validateChain } from "../lib/api"
import { formatDateTime, shortHash } from "../lib/utils"
import type { BlockOut } from "../types"

export default function BlockchainPanel() {
  const { latestBlocks } = useSSE()
  const [initial, setInitial] = useState<BlockOut[]>([])
  const [valid, setValid]     = useState<boolean | null>(null)
  const [chainLen, setChainLen] = useState<number>(0)

  useEffect(() => {
    fetchBlockchain()
      .then(setInitial)
      .catch(() => {})
    validateChain()
      .then((r) => { setValid(r.valid); setChainLen(r.length) })
      .catch(() => {})
  }, [])

  // Refresh chain validity when new block arrives via SSE
  useEffect(() => {
    if (latestBlocks.length > 0) {
      validateChain()
        .then((r) => { setValid(r.valid); setChainLen(r.length) })
        .catch(() => {})
    }
  }, [latestBlocks.length])

  const merged = [
    ...latestBlocks,
    ...initial.filter((b) => !latestBlocks.some((l) => l.id === b.id)),
  ]
    .sort((a, b) => b.index - a.index)
    .slice(0, 30)

  return (
    <div className="panel">
      <div className="panel-header">
        <Link2 size={16} className="panel-icon text-cyan-400" />
        <h2 className="panel-title">Blockchain Ledger</h2>
        <div className="chain-status">
          {valid === null ? (
            <span className="chain-badge chain-unknown">Checking…</span>
          ) : valid ? (
            <span className="chain-badge chain-valid">
              <CheckCircle size={12} /> VALID ({chainLen})
            </span>
          ) : (
            <span className="chain-badge chain-invalid">
              <XCircle size={12} /> TAMPERED
            </span>
          )}
        </div>
      </div>

      <div className="chain-list">
        {merged.length === 0 && (
          <div className="panel-empty">
            <Link2 size={28} className="empty-icon" />
            <p>No blocks yet — genesis pending</p>
          </div>
        )}
        {merged.map((blk, i) => (
          <div key={blk.block_hash || `${blk.index}-${i}`} className="chain-block">
            <div className="chain-block-header">
              <span className="chain-index">#{blk.index}</span>
              <span className="chain-type">{blk.event_type}</span>
              <span className="chain-time">{formatDateTime(blk.timestamp)}</span>
            </div>
            <div className="chain-hashes">
              <div className="hash-row">
                <span className="hash-label">Hash</span>
                <code className="hash-val">{shortHash(blk.block_hash)}</code>
              </div>
              <div className="hash-row">
                <span className="hash-label">Prev</span>
                <code className="hash-val prev">{shortHash(blk.prev_hash)}</code>
              </div>
            </div>
            {blk.data && (() => {
              const d = blk.data as { label?: string; confidence?: number; severity?: string }
              return (
                <div className="chain-data">
                  {d.label    && <span>🔥 {d.label}</span>}
                  {d.confidence != null && (
                    <span>Conf: {(d.confidence * 100).toFixed(0)}%</span>
                  )}
                  {d.severity && <span>{d.severity}</span>}
                </div>
              )
            })()}
          </div>
        ))}
      </div>
    </div>
  )
}
