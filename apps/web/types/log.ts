export interface LogEntry {
  id: string
  timestamp: string
  prompt: string
  response: string
  model: string
  tokens?: number
  promptTokens?: number
  completionTokens?: number
  thinkingTokens?: number
  cost?: number
  status: 'success' | 'error'
  error?: string
  cache?: 'disabled' | 'miss' | 'hit' | 'refreshed' | 'semantic_hit'
  retry?: 'not_triggered' | { success: boolean; tries: number }
  fallback?: 'disabled' | 'active'
  loadbalance?: 'disabled' | 'active'
  latency?: number
  configId?: string
  promptId?: string
}
