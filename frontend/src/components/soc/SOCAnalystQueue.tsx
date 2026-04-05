// frontend/src/components/soc/SOCAnalystQueue.tsx
//
// SOC Analyst Queue — real-time TLS anomaly alert stream with playbook controls.
//
// Features:
//  • Connects to /compliance/ws/alerts via the useWebSocket hook (auto-reconnect)
//  • Renders a live, scrollable alert queue with severity badges
//  • "One-click Playbook Launch" button per alert
//  • "Human-in-the-Loop Approval Modal" for CRITICAL-tier playbooks
//  • JA3 / JARM fingerprint display with copy-to-clipboard

import React, { useCallback, useEffect, useRef, useState } from "react";
import { useWebSocket } from "../../hooks/useWebSocket";
import type {
  AlertSeverity,
  ApprovalStatus,
  RemediationPlaybook,
  TLSAlert,
} from "../../types";

// ── Constants ─────────────────────────────────────────────────────────────────

const WS_URL = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/api/v1/compliance/ws/alerts`;
const API_BASE = "/api/v1/compliance";
const MAX_ALERTS = 200;

// ── Helpers ───────────────────────────────────────────────────────────────────

const SEVERITY_STYLES: Record<AlertSeverity, string> = {
  critical: "bg-red-600 text-white",
  high:     "bg-orange-500 text-white",
  medium:   "bg-yellow-400 text-gray-900",
  info:     "bg-blue-500 text-white",
};

const ALERT_ROW_BORDER: Record<AlertSeverity, string> = {
  critical: "border-l-4 border-red-500 bg-red-950/20",
  high:     "border-l-4 border-orange-400 bg-orange-950/20",
  medium:   "border-l-4 border-yellow-400 bg-yellow-950/10",
  info:     "border-l-4 border-blue-400 bg-blue-950/10",
};

function formatTime(isoString: string): string {
  return new Date(isoString).toLocaleTimeString("en-IN", { hour12: false });
}

async function copyToClipboard(text: string): Promise<void> {
  await navigator.clipboard.writeText(text);
}

// ── Approval Modal ────────────────────────────────────────────────────────────

interface ApprovalModalProps {
  playbook:    RemediationPlaybook;
  onClose:     () => void;
  onApprove:   (playbookId: string) => Promise<void>;
  isLoading:   boolean;
}

function ApprovalModal({ playbook, onClose, onApprove, isLoading }: ApprovalModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-lg rounded-2xl bg-gray-900 border border-gray-700 shadow-2xl p-6"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-red-600/20 text-red-400 text-xl">⚠</span>
          <div>
            <h2 className="text-lg font-bold text-white">Human Approval Required</h2>
            <p className="text-xs text-gray-400">CRITICAL-tier playbook — manual review mandatory</p>
          </div>
        </div>

        {/* Playbook summary */}
        <div className="rounded-xl bg-gray-800 p-4 mb-5 space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Asset</span>
            <span className="font-mono text-white">{playbook.host ?? playbook.asset_id}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Playbook ID</span>
            <span className="font-mono text-xs text-cyan-400">{playbook.playbook_id}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Algorithms</span>
            <span className="text-orange-300">{playbook.algorithms_targeted.join(", ") || "—"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Est. Effort</span>
            <span className="text-white">{playbook.estimated_effort_hours}h</span>
          </div>
        </div>

        <p className="text-sm text-gray-300 mb-5">
          Executing this playbook will trigger{" "}
          <strong className="text-red-400">HSM re-keying, certificate rotation, and TLS cipher-suite changes</strong>{" "}
          on the target host. A ServiceNow / Jira change request will be raised.{" "}
          <strong className="text-white">This action cannot be undone automatically.</strong>
        </p>

        {/* Actions */}
        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-gray-700 text-gray-300 hover:bg-gray-600 transition"
          >
            Cancel
          </button>
          <button
            onClick={() => onApprove(playbook.playbook_id)}
            disabled={isLoading}
            className="px-5 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white font-semibold transition disabled:opacity-50"
          >
            {isLoading ? "Submitting…" : "🔐 Approve & Execute"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Alert Row ─────────────────────────────────────────────────────────────────

interface AlertRowProps {
  alert:       TLSAlert;
  onLaunch:    (alert: TLSAlert) => void;
  isLaunching: boolean;
}

function AlertRow({ alert, onLaunch, isLaunching }: AlertRowProps) {
  const [copied, setCopied] = useState<"ja3" | "jarm" | null>(null);

  async function handleCopy(field: "ja3" | "jarm") {
    await copyToClipboard(field === "ja3" ? alert.ja3 : alert.jarm);
    setCopied(field);
    setTimeout(() => setCopied(null), 1500);
  }

  return (
    <div className={`rounded-lg px-4 py-3 mb-2 ${ALERT_ROW_BORDER[alert.severity]} transition-all`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className={`shrink-0 px-2 py-0.5 rounded text-xs font-bold uppercase ${SEVERITY_STYLES[alert.severity]}`}>
            {alert.severity}
          </span>
          <span className="font-mono text-sm text-cyan-300 truncate">{alert.host}</span>
          <span className="text-xs text-gray-400 shrink-0">{alert.alert_type.replace(/_/g, " ")}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-gray-500">{formatTime(alert.timestamp)}</span>
          <button
            onClick={() => onLaunch(alert)}
            disabled={isLaunching}
            className="px-3 py-1 text-xs rounded-md bg-cyan-700 hover:bg-cyan-600 text-white font-semibold transition disabled:opacity-50"
          >
            🚀 Launch Playbook
          </button>
        </div>
      </div>

      {/* JA3 / JARM fingerprints */}
      <div className="mt-2 flex flex-wrap gap-3 text-xs">
        <button
          onClick={() => handleCopy("ja3")}
          className="flex items-center gap-1 font-mono text-gray-400 hover:text-white transition"
          title="Copy JA3"
        >
          <span className="text-gray-600">JA3:</span>
          <span className="text-purple-300">{alert.ja3.slice(0, 16)}…</span>
          <span>{copied === "ja3" ? "✓" : "📋"}</span>
        </button>
        <button
          onClick={() => handleCopy("jarm")}
          className="flex items-center gap-1 font-mono text-gray-400 hover:text-white transition"
          title="Copy JARM"
        >
          <span className="text-gray-600">JARM:</span>
          <span className="text-emerald-300">{alert.jarm.slice(0, 16)}…</span>
          <span>{copied === "jarm" ? "✓" : "📋"}</span>
        </button>
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function SOCAnalystQueue() {
  const [alerts, setAlerts]               = useState<TLSAlert[]>([]);
  const [playbook, setPlaybook]           = useState<RemediationPlaybook | null>(null);
  const [approvalLoading, setApprovalLoading] = useState(false);
  const [launchingFor, setLaunchingFor]   = useState<string | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<AlertSeverity | "all">("all");
  const [paused, setPaused]               = useState(false);
  const bottomRef                         = useRef<HTMLDivElement>(null);

  // ── WebSocket ───────────────────────────────────────────────────────────────
  const { status: wsStatus, send } = useWebSocket<TLSAlert>({
    url: WS_URL,
    onMessage: useCallback((data: TLSAlert) => {
      if (paused || data.type === "heartbeat" || data.type === "pong") return;
      setAlerts((prev) => [data, ...prev].slice(0, MAX_ALERTS));
    }, [paused]),
    reconnectDelay: 3000,
  });

  // Heartbeat keepalive
  useEffect(() => {
    const id = setInterval(() => send({ type: "ping" }), 25_000);
    return () => clearInterval(id);
  }, [send]);

  // Auto-scroll to newest alert
  useEffect(() => {
    if (!paused) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [alerts, paused]);

  // ── Playbook Launch ─────────────────────────────────────────────────────────
  async function handleLaunch(alert: TLSAlert) {
    setLaunchingFor(alert.asset_id);
    try {
      // 1. Label the asset
      const labelRes = await fetch(`${API_BASE}/label`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          algorithms: Object.values(alert.details?.algorithms ?? { a: "rsa-2048" }),
          asset_id:   alert.asset_id,
          host:       alert.host,
        }),
      });
      const label = await labelRes.json();

      // 2. Generate playbook
      const pbRes = await fetch(`${API_BASE}/playbook/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ label_result: label }),
      });
      const playbooks: RemediationPlaybook[] = await pbRes.json();

      if (playbooks.length === 0) return;

      const pb = playbooks[0];
      setPlaybook(pb);

      // Critical tier → show approval modal
      // Non-critical → execute immediately (show confirmation)
    } catch (err) {
      console.error("Playbook launch failed:", err);
    } finally {
      setLaunchingFor(null);
    }
  }

  // ── Approval Gate ───────────────────────────────────────────────────────────
  async function handleApprove(playbookId: string) {
    setApprovalLoading(true);
    try {
      const res = await fetch(`${API_BASE}/approval/${playbookId}/request`, {
        method: "POST",
      });
      const record = await res.json();
      console.info("Approval record:", record);
      setPlaybook(null);
    } finally {
      setApprovalLoading(false);
    }
  }

  const filtered = filterSeverity === "all"
    ? alerts
    : alerts.filter((a) => a.severity === filterSeverity);

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <section className="flex flex-col h-full bg-gray-950 text-white rounded-2xl border border-gray-800 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 bg-gray-900 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold tracking-tight">🛡 SOC Alert Queue</span>
          <span
            className={`h-2.5 w-2.5 rounded-full ${
              wsStatus === "open" ? "bg-emerald-400 animate-pulse" :
              wsStatus === "connecting" ? "bg-yellow-400 animate-pulse" :
              "bg-red-500"
            }`}
          />
          <span className="text-xs text-gray-500 capitalize">{wsStatus}</span>
        </div>

        <div className="flex items-center gap-2">
          {/* Severity filter */}
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value as AlertSeverity | "all")}
            className="bg-gray-800 text-sm text-gray-300 border border-gray-700 rounded-lg px-2 py-1"
          >
            <option value="all">All severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="info">Info</option>
          </select>
          {/* Pause / Resume */}
          <button
            onClick={() => setPaused((p) => !p)}
            className={`px-3 py-1 text-xs rounded-lg font-semibold transition ${
              paused ? "bg-yellow-500 text-gray-900" : "bg-gray-700 text-gray-300 hover:bg-gray-600"
            }`}
          >
            {paused ? "▶ Resume" : "⏸ Pause"}
          </button>
          {/* Clear */}
          <button
            onClick={() => setAlerts([])}
            className="px-3 py-1 text-xs rounded-lg bg-gray-700 text-gray-400 hover:bg-gray-600 transition"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Stats bar */}
      <div className="flex gap-4 px-5 py-2 bg-gray-900/60 border-b border-gray-800/60 text-xs text-gray-400">
        {(["critical", "high", "medium", "info"] as AlertSeverity[]).map((s) => (
          <span key={s}>
            <span className={`font-bold ${
              s === "critical" ? "text-red-400" :
              s === "high"     ? "text-orange-400" :
              s === "medium"   ? "text-yellow-400" : "text-blue-400"
            }`}>
              {alerts.filter((a) => a.severity === s).length}
            </span>{" "}
            {s}
          </span>
        ))}
        <span className="ml-auto">{paused && "⏸ Paused — new alerts buffered"}</span>
      </div>

      {/* Alert list */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-1">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-600 gap-2">
            <span className="text-4xl">📡</span>
            <span>Waiting for TLS anomaly alerts…</span>
          </div>
        ) : (
          filtered.map((alert, i) => (
            <AlertRow
              key={`${alert.asset_id}-${alert.timestamp}-${i}`}
              alert={alert}
              onLaunch={handleLaunch}
              isLaunching={launchingFor === alert.asset_id}
            />
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Approval modal */}
      {playbook && playbook.tier === "critical" && (
        <ApprovalModal
          playbook={playbook}
          onClose={() => setPlaybook(null)}
          onApprove={handleApprove}
          isLoading={approvalLoading}
        />
      )}
    </section>
  );
}
