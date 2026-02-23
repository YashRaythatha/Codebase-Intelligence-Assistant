/**
 * Shared types for trace viewer and API responses.
 */

export interface TraceStep {
  step_type: string
  payload?: Record<string, unknown>
}

export interface TraceUsage {
  total_tokens?: number
  prompt_tokens?: number
  completion_tokens?: number
}

export interface TraceData {
  trace_id: string
  run_id?: string
  started_at?: string
  ended_at?: string
  endpoint_name?: string
  usage?: TraceUsage
  steps?: TraceStep[]
  [key: string]: unknown
}
