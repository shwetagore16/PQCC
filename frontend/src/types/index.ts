// frontend/src/types/index.ts — Shared TypeScript types for the PQSS dashboard.

export type QuantumLabel = "fully_quantum_safe" | "pqc_ready" | "quantum_vulnerable";
export type RiskBand     = "critical" | "high" | "medium" | "low";
export type AlertSeverity = "critical" | "high" | "medium" | "info";
export type PlaybookTier = "critical" | "high" | "medium" | "low";
export type ApprovalStatus = "pending" | "approved" | "rejected" | "timeout" | "no_gate";

// ── Asset ─────────────────────────────────────────────────────────────────────
export interface Asset {
  id:            string;
  asset_type:    "domain" | "ip_address" | "url" | "certificate" | "api_endpoint" | "load_balancer";
  asset_value:   string;
  organization:  string | null;
  seed_domain:   string | null;
  status:        "pending" | "scanning" | "scanned" | "error" | "excluded";
  risk_score:    number | null;   // [0–10]
  hndl_score:    number | null;
  quantum_label: QuantumLabel | null;
  tags:          string[] | null;
  first_seen:    string;
  last_scanned:  string | null;
}

// ── TLS Anomaly Alert ─────────────────────────────────────────────────────────
export interface TLSAlert {
  type:       "tls_anomaly" | "heartbeat" | "pong";
  asset_id:   string;
  host:       string;
  alert_type: "ja3_fingerprint_mismatch" | "jarm_change" | "new_cipher_suite" | "cert_expiry" | "downgrade_detected";
  ja3:        string;
  jarm:       string;
  severity:   AlertSeverity;
  details:    Record<string, unknown>;
  timestamp:  string;
}

// ── Compliance ────────────────────────────────────────────────────────────────
export interface AlgorithmFinding {
  algorithm:           string;
  key_bits:            number | null;
  is_approved:         boolean;
  is_hybrid:           boolean;
  is_deprecated:       boolean;
  applicable_standards: string[];
  violations:          string[];
  notes:               string;
}

export interface ComplianceLabelResult {
  asset_id:          string | null;
  host:              string | null;
  quantum_label:     QuantumLabel;
  overall_compliant: boolean;
  cnsa2_compliant:   boolean;
  findings:          AlgorithmFinding[];
  approved_count:    number;
  hybrid_count:      number;
  vulnerable_count:  number;
  deprecated_count:  number;
  summary:           string;
  remediation_priority: "immediate" | "planned" | "none";
  labeled_at:        string;
}

// ── Playbook ──────────────────────────────────────────────────────────────────
export interface RemediationPlaybook {
  playbook_id:             string;
  asset_id:                string | null;
  host:                    string | null;
  tier:                    PlaybookTier;
  title:                   string;
  description:             string;
  algorithms_targeted:     string[];
  approval_status:         ApprovalStatus;
  approval_ticket:         string | null;
  estimated_effort_hours:  number;
  generated_at:            string;
}

// ── HNDL Forecast ─────────────────────────────────────────────────────────────
export interface ForecastBand {
  date: string;
  p10:  number;
  p50:  number;
  p90:  number;
}

export interface ForecastScenario {
  label:   string;   // "Do Nothing" | "Phased Migration" | "Emergency Migration"
  color:   string;   // hex
  bands:   ForecastBand[];
}

// ── Heatmap ───────────────────────────────────────────────────────────────────
export interface HeatmapNode {
  id:          string;
  host:        string;
  tier:        string;
  hndl_score:  number;
  risk_band:   RiskBand;
  quantum_label: QuantumLabel | null;
  children?:   HeatmapNode[];
  value?:      number;   // D3 treemap value (= hndl_score)
}
