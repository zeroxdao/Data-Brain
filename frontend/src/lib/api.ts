/**
 * API client — thin wrapper over fetch that points to the FastAPI backend.
 * Base URL is configurable via NEXT_PUBLIC_API_URL env var (defaults to localhost:8000).
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${path} → ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── Types (mirrors backend Pydantic schemas) ─────────────────────────────────

export interface AccountInfo {
  account_id: string;
  broker: string | null;
  currency: string;
  balance: number;
  equity: number;
  leverage: number;
}

export interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface RegimeSnapshot {
  time: string;
  symbol: string;
  adx: number;
  atr: number;
  realized_vol: number;
  session: string;
  trend_label: string;
  vol_label: string;
  labels: string[];
}

export interface EARegimePerformance {
  ea_name: string;
  regime: string;
  trades: number;
  win_rate: number;
  total_profit: number;
  avg_profit: number;
  profit_factor: number;
}

export interface EAReport {
  ea_name: string;
  total_trades: number;
  total_profit: number;
  overall_win_rate: number;
  by_regime: EARegimePerformance[];
  best_regimes: string[];
  worst_regimes: string[];
  insight: string;
}

export interface AnalysisResponse {
  account_id: string;
  symbol: string;
  analyzed_deals: number;
  reports: EAReport[];
}

export interface EADecision {
  ea_name: string;
  enabled: boolean;
  weight: number;
  reason: string;
}

export interface OrchestratorStatus {
  account_id: string;
  symbol: string;
  scheduler_status: "running" | "stopped";
  circuit_status: string;
  circuit_trip_reason: string;
  last_updated: string | null;
  current_regime: {
    labels: string[];
    adx: number;
    atr: number;
    session: string;
  } | null;
  active_decisions: EADecision[];
}

export interface DecisionLogEntry {
  timestamp: string;
  regime_labels: string[];
  circuit_status: string;
  decisions: EADecision[];
}

export interface DecisionLog {
  account_id: string;
  entries: DecisionLogEntry[];
}

export interface StartOrchestratorRequest {
  symbol?: string;
  timeframe?: string;
  max_drawdown_pct?: number;
  max_daily_loss_pct?: number;
  max_active_eas?: number;
  interval_seconds?: number;
}

// ── API functions ─────────────────────────────────────────────────────────────

export const api = {
  health: () => request<{ status: string; bridge: string }>("/api/health"),

  account: (id: string) => request<AccountInfo>(`/api/accounts/${id}`),

  candles: (symbol: string, days = 30) =>
    request<Candle[]>(`/api/candles?symbol=${symbol}&days=${days}`),

  regime: (symbol: string, days = 30, limit = 200) =>
    request<RegimeSnapshot[]>(
      `/api/regime?symbol=${symbol}&days=${days}&limit=${limit}`
    ),

  analysis: (accountId: string, symbol: string, days = 60) =>
    request<AnalysisResponse>(
      `/api/analysis/${accountId}?symbol=${symbol}&days=${days}`
    ),

  orchestratorStatus: (accountId: string) =>
    request<OrchestratorStatus>(`/api/orchestrator/${accountId}/status`),

  orchestratorLog: (accountId: string, limit = 20) =>
    request<DecisionLog>(
      `/api/orchestrator/${accountId}/log?limit=${limit}`
    ),

  startOrchestrator: (accountId: string, body: StartOrchestratorRequest) =>
    request<{ message: string }>(`/api/orchestrator/${accountId}/start`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  stopOrchestrator: (accountId: string) =>
    request<{ message: string }>(`/api/orchestrator/${accountId}/stop`, {
      method: "POST",
    }),

  resetCircuit: (accountId: string) =>
    request<{ message: string }>(`/api/orchestrator/${accountId}/reset`, {
      method: "POST",
    }),
};
