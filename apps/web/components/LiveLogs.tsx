'use client'

import { useState, useMemo } from 'react'
import { LogEntry } from '@/types/log'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { format } from 'date-fns'
import JsonViewer from './JsonViewer'
import LogDetailDialog from './LogDetailDialog'
import { Activity, Database, Zap, DollarSign, Eye } from 'lucide-react'

interface LiveLogsProps {
  logs: LogEntry[]
  isGenerating: boolean
  totalGenerated: number
  onReplay?: (log: LogEntry) => void
}

export default function LiveLogs({ logs, isGenerating, totalGenerated, onReplay }: LiveLogsProps) {
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  
  const stats = useMemo(() => {
    const successCount = logs.filter((l) => l.status === 'success').length
    const errorCount = logs.filter((l) => l.status === 'error').length
    const totalTokens = logs.reduce((sum, log) => sum + (log.tokens || 0), 0)
    const totalCost = logs.reduce((sum, log) => sum + (log.cost || 0), 0)
    return { successCount, errorCount, totalTokens, totalCost }
  }, [logs])
  
  const handleLogClick = (log: LogEntry) => {
    setSelectedLog(log)
    setDialogOpen(true)
  }
  
  const handleReplay = (replayedLog: LogEntry) => {
    if (onReplay) {
      onReplay(replayedLog)
    }
    setSelectedLog(replayedLog)
  }

  return (
    <div className="flex flex-col h-full space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 flex-shrink-0">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs sm:text-sm font-medium">Total Logs</CardTitle>
            <Database className="h-3 w-3 sm:h-4 sm:w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl sm:text-2xl font-bold">{totalGenerated}</div>
            <p className="text-xs text-muted-foreground">
              {logs.length} in view
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs sm:text-sm font-medium">Success</CardTitle>
            <Zap className="h-3 w-3 sm:h-4 sm:w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-xl sm:text-2xl font-bold text-green-600">{stats.successCount}</div>
            <p className="text-xs text-muted-foreground">
              {logs.length > 0 ? Math.round((stats.successCount / logs.length) * 100) : 0}% success
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs sm:text-sm font-medium">Errors</CardTitle>
            <Activity className="h-3 w-3 sm:h-4 sm:w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-xl sm:text-2xl font-bold text-red-600">{stats.errorCount}</div>
            <p className="text-xs text-muted-foreground">
              {logs.length > 0 ? Math.round((stats.errorCount / logs.length) * 100) : 0}% error
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs sm:text-sm font-medium">Total Cost</CardTitle>
            <DollarSign className="h-3 w-3 sm:h-4 sm:w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl sm:text-2xl font-bold">${stats.totalCost.toFixed(4)}</div>
            <p className="text-xs text-muted-foreground">
              {stats.totalTokens.toLocaleString()} tokens
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="flex-1 flex flex-col min-h-0">
        <CardHeader className="flex-shrink-0">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4">
            <div>
              <CardTitle className="text-lg sm:text-xl">Live Log Stream</CardTitle>
              <CardDescription className="mt-1 text-sm">
                Real-time log generation and monitoring
              </CardDescription>
            </div>
            {isGenerating && (
              <div className="flex items-center gap-2">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                </span>
                <span className="text-xs sm:text-sm text-green-600 font-medium">Generating...</span>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col min-h-0">
          {logs.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground flex-1 flex items-center justify-center">
              <div>
                <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium">No logs generated yet</p>
                <p className="text-sm mt-2">Start generating logs to see them appear here</p>
              </div>
            </div>
          ) : (
            <Tabs defaultValue="list" className="w-full flex flex-col flex-1 min-h-0">
              <TabsList className="flex-shrink-0">
                <TabsTrigger value="list">List View</TabsTrigger>
                <TabsTrigger value="json">JSON View</TabsTrigger>
              </TabsList>
              <TabsContent value="list" className="space-y-2 mt-4 flex-1 overflow-y-auto min-h-0 pr-2">
                {logs.map((log) => (
                  <Card
                    key={log.id}
                    className="border-l-4 border-l-blue-500 cursor-pointer hover:bg-muted/50 transition-colors active:scale-[0.99]"
                    onClick={() => handleLogClick(log)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        handleLogClick(log)
                      }
                    }}
                    aria-label={`View log details for ${log.prompt.substring(0, 50)}...`}
                  >
                    <CardContent className="pt-3 pb-3">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div className="flex items-center gap-1.5 flex-wrap flex-1 min-w-0">
                          <Badge variant={log.status === 'success' ? 'default' : 'destructive'} className="text-xs font-semibold">
                            {log.status}
                          </Badge>
                          <Badge variant="outline" className="font-mono text-xs">{log.model}</Badge>
                          {log.tokens && (
                            <Badge variant="secondary" className="text-xs">{log.tokens}</Badge>
                          )}
                          {log.cost && (
                            <Badge variant="secondary" className="text-xs">${log.cost.toFixed(4)}</Badge>
                          )}
                          {log.cache && log.cache !== 'disabled' && (
                            <Badge variant={log.cache === 'hit' || log.cache === 'semantic_hit' ? 'default' : 'secondary'} className="text-xs">
                              {log.cache}
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-1.5 text-xs flex-shrink-0">
                          {log.latency && (
                            <span className="text-muted-foreground font-mono whitespace-nowrap text-xs">
                              {log.latency}ms
                            </span>
                          )}
                          <span className="text-muted-foreground font-mono whitespace-nowrap text-xs">
                            {format(new Date(log.timestamp), 'HH:mm:ss')}
                          </span>
                          <Eye className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                        </div>
                      </div>

                      <div className="space-y-1.5">
                        <div>
                          <p className="text-xs font-semibold text-muted-foreground mb-0.5 uppercase tracking-wide">Prompt</p>
                          <p className="text-xs bg-slate-50 p-1.5 rounded border font-mono line-clamp-1 break-words">
                            {log.prompt}
                          </p>
                        </div>

                        {log.status === 'success' ? (
                          <div>
                            <p className="text-xs font-semibold text-muted-foreground mb-0.5 uppercase tracking-wide">Response</p>
                            <p className="text-xs bg-slate-50 p-1.5 rounded border line-clamp-1 break-words">
                              {log.response}
                            </p>
                          </div>
                        ) : (
                          <div>
                            <p className="text-xs font-semibold text-red-600 mb-0.5 uppercase tracking-wide">Error</p>
                            <p className="text-xs bg-red-50 p-1.5 rounded border border-red-200 text-red-800 line-clamp-1 break-words">
                              {log.error}
                            </p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </TabsContent>
              <TabsContent value="json" className="space-y-2 mt-4 flex-1 overflow-y-auto min-h-0">
                {logs.map((log) => (
                  <Card key={log.id}>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-xs sm:text-sm font-mono break-all">{log.id}</CardTitle>
                      <CardDescription className="text-xs">
                        {format(new Date(log.timestamp), 'PPpp')}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <JsonViewer log={log} />
                    </CardContent>
                  </Card>
                ))}
              </TabsContent>
            </Tabs>
          )}
        </CardContent>
      </Card>

      <LogDetailDialog
        log={selectedLog}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onReplay={handleReplay}
      />
    </div>
  )
}
