'use client'

import { useState, useCallback } from 'react'
import LogGenerator from '@/components/LogGenerator'
import LiveLogs from '@/components/LiveLogs'
import ConnectionTest from '@/components/ConnectionTest'
import { LogEntry } from '@/types/log'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export default function LogsPage() {
  const [recentLogs, setRecentLogs] = useState<LogEntry[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [totalGenerated, setTotalGenerated] = useState(0)

  const handleLogGenerated = useCallback((log: LogEntry) => {
    setRecentLogs((prev) => [log, ...prev].slice(0, 50))
    setTotalGenerated((prev) => prev + 1)
  }, [])
  
  const handleReplay = useCallback((replayedLog: LogEntry) => {
    setRecentLogs((prev) => [replayedLog, ...prev].slice(0, 50))
    setTotalGenerated((prev) => prev + 1)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto px-4 py-6 max-w-[1800px]">
        <div className="mb-6">
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight mb-2">Log Generator</h1>
          <p className="text-muted-foreground text-base sm:text-lg">
            Generate prompt logs for Portkey observability and Evolv analysis
          </p>
        </div>

        <Tabs defaultValue="generator" className="w-full">
          <TabsList className="grid w-full max-w-md grid-cols-2 mb-6">
            <TabsTrigger value="generator">Generator</TabsTrigger>
            <TabsTrigger value="test">Connection Test</TabsTrigger>
          </TabsList>
          <TabsContent value="test" className="mt-0">
            <ConnectionTest />
          </TabsContent>
          <TabsContent value="generator" className="mt-0">
            <div className="grid grid-cols-1 xl:grid-cols-[400px_1fr] gap-6 h-[calc(100vh-200px)]">
              <div className="xl:h-full overflow-y-auto">
                <LogGenerator
                  onLogGenerated={handleLogGenerated}
                  isGenerating={isGenerating}
                  setIsGenerating={setIsGenerating}
                />
              </div>
              <div className="xl:h-full overflow-hidden flex flex-col">
                <LiveLogs
                  logs={recentLogs}
                  isGenerating={isGenerating}
                  totalGenerated={totalGenerated}
                  onReplay={handleReplay}
                />
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
