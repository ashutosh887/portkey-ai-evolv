'use client'

import { LogEntry } from '@/types/log'

interface JsonViewerProps {
  log: LogEntry
}

export default function JsonViewer({ log }: JsonViewerProps) {
  const jsonData = {
    id: log.id,
    timestamp: log.timestamp,
    prompt: log.prompt,
    response: log.response,
    model: log.model,
    tokens: log.tokens,
    promptTokens: log.promptTokens,
    completionTokens: log.completionTokens,
    thinkingTokens: log.thinkingTokens,
    cost: log.cost,
    latency: log.latency,
    cache: log.cache,
    retry: log.retry,
    fallback: log.fallback,
    loadbalance: log.loadbalance,
    status: log.status,
    error: log.error,
    configId: log.configId,
    promptId: log.promptId,
  }

  const jsonString = JSON.stringify(jsonData, null, 2)

  return (
    <div className="relative">
      <pre className="bg-slate-950 text-slate-50 p-4 rounded-lg overflow-x-auto text-xs font-mono">
        <code>{jsonString}</code>
      </pre>
    </div>
  )
}
