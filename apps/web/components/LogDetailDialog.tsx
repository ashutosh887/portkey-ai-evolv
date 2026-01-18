'use client'

import { LogEntry } from '@/types/log'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import JsonViewer from './JsonViewer'
import { format } from 'date-fns'
import { Play, Copy, CheckCircle2, XCircle, Zap, Clock, DollarSign } from 'lucide-react'
import { useState } from 'react'
import { generateLog } from '@/lib/portkey'

interface LogDetailDialogProps {
  log: LogEntry | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onReplay: (log: LogEntry) => void
}

export default function LogDetailDialog({
  log,
  open,
  onOpenChange,
  onReplay,
}: LogDetailDialogProps) {
  const [isReplaying, setIsReplaying] = useState(false)
  const [copied, setCopied] = useState(false)

  if (!log) return null

  const handleReplay = async () => {
    if (!log) return
    setIsReplaying(true)
    try {
      const cleanModel = log.model.replace(' (mock)', '')
      const result = await generateLog(log.prompt, cleanModel, false)
      if (result.success && onReplay) {
        const replayedLog: LogEntry = {
          ...log,
          id: `log-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
          timestamp: new Date().toISOString(),
          response: result.content || '',
          model: cleanModel,
          tokens: result.tokens,
          promptTokens: result.promptTokens,
          completionTokens: result.completionTokens,
          thinkingTokens: result.thinkingTokens,
          cost: result.cost,
          latency: result.latency,
          cache: result.cache,
          retry: result.retry,
          fallback: result.fallback,
          loadbalance: result.loadbalance,
          status: 'success',
        }
        onReplay(replayedLog)
        onOpenChange(false)
      }
    } catch (error) {
      console.error('Replay failed:', error)
    } finally {
      setIsReplaying(false)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(log, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const getCacheBadge = () => {
    if (log.cache === 'hit') return <Badge variant="success">Cache Hit</Badge>
    if (log.cache === 'semantic_hit') return <Badge variant="success">Semantic Hit</Badge>
    if (log.cache === 'miss') return <Badge variant="secondary">Cache Miss</Badge>
    if (log.cache === 'refreshed') return <Badge variant="secondary">Cache Refreshed</Badge>
    return <Badge variant="outline">Cache Disabled</Badge>
  }

  const getRetryBadge = () => {
    if (log.retry === 'not_triggered') {
      return <Badge variant="outline">Retry Not Triggered</Badge>
    }
    if (typeof log.retry === 'object') {
      return (
        <Badge variant={log.retry.success ? 'success' : 'error'}>
          Retry {log.retry.success ? 'Success' : 'Failed'} ({log.retry.tries} tries)
        </Badge>
      )
    }
    return <Badge variant="outline">Retry Not Triggered</Badge>
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle>Log Details</DialogTitle>
              <DialogDescription>
                {format(new Date(log.timestamp), 'PPpp')}
              </DialogDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopy}
                aria-label={copied ? 'Copied to clipboard' : 'Copy log to clipboard'}
              >
                {copied ? <CheckCircle2 className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleReplay}
                disabled={isReplaying || log.model.includes('mock')}
                aria-label="Replay this log"
              >
                <Play className="h-4 w-4 mr-2" />
                {isReplaying ? 'Replaying...' : 'Replay'}
              </Button>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant={log.status === 'success' ? 'success' : 'error'}>
              {log.status === 'success' ? (
                <CheckCircle2 className="h-3 w-3 mr-1" />
              ) : (
                <XCircle className="h-3 w-3 mr-1" />
              )}
              {log.status}
            </Badge>
            <Badge variant="outline">{log.model}</Badge>
            {log.tokens && (
              <Badge variant="secondary">
                <Zap className="h-3 w-3 mr-1" />
                {log.tokens} tokens
              </Badge>
            )}
            {log.cost && (
              <Badge variant="secondary">
                <DollarSign className="h-3 w-3 mr-1" />
                ${log.cost.toFixed(6)}
              </Badge>
            )}
            {log.latency && (
              <Badge variant="secondary">
                <Clock className="h-3 w-3 mr-1" />
                {log.latency}ms
              </Badge>
            )}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground">Cache</p>
              {getCacheBadge()}
            </div>
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground">Retry</p>
              {getRetryBadge()}
            </div>
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground">Fallback</p>
              <Badge variant={log.fallback === 'active' ? 'success' : 'outline'}>
                {log.fallback === 'active' ? 'Active' : 'Disabled'}
              </Badge>
            </div>
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground">Loadbalance</p>
              <Badge variant={log.loadbalance === 'active' ? 'success' : 'outline'}>
                {log.loadbalance === 'active' ? 'Active' : 'Disabled'}
              </Badge>
            </div>
          </div>

          {log.promptTokens && log.completionTokens && (
            <div className="grid grid-cols-3 gap-4 p-4 bg-muted rounded-lg">
              <div>
                <p className="text-xs text-muted-foreground">Prompt Tokens</p>
                <p className="text-lg font-semibold">{log.promptTokens}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Completion Tokens</p>
                <p className="text-lg font-semibold">{log.completionTokens}</p>
              </div>
              {log.thinkingTokens && log.thinkingTokens > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground">Thinking Tokens</p>
                  <p className="text-lg font-semibold">{log.thinkingTokens}</p>
                </div>
              )}
            </div>
          )}

          <Tabs defaultValue="details" className="w-full">
            <TabsList>
              <TabsTrigger value="details">Details</TabsTrigger>
              <TabsTrigger value="json">JSON</TabsTrigger>
            </TabsList>
            <TabsContent value="details" className="space-y-4 mt-4">
              <div>
                <p className="text-sm font-semibold mb-2">Prompt</p>
                <div className="bg-muted p-4 rounded-lg border font-mono text-sm">
                  {log.prompt}
                </div>
              </div>
              {log.status === 'success' ? (
                <div>
                  <p className="text-sm font-semibold mb-2">Response</p>
                  <div className="bg-muted p-4 rounded-lg border text-sm">
                    {log.response}
                  </div>
                </div>
              ) : (
                <div>
                  <p className="text-sm font-semibold mb-2 text-red-600">Error</p>
                  <div className="bg-red-50 p-4 rounded-lg border border-red-200 text-sm text-red-800">
                    {log.error}
                  </div>
                </div>
              )}
            </TabsContent>
            <TabsContent value="json" className="mt-4">
              <JsonViewer log={log} />
            </TabsContent>
          </Tabs>
        </div>
      </DialogContent>
    </Dialog>
  )
}
