'use client'

import { useState, useRef } from 'react'
import { generateLog } from '@/lib/portkey'
import { LogEntry } from '@/types/log'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import ErrorDisplay from './ErrorDisplay'

interface LogGeneratorProps {
  onLogGenerated: (log: LogEntry) => void
  isGenerating: boolean
  setIsGenerating: (value: boolean) => void
}

const SAMPLE_PROMPTS = [
  'What is AI?',
  'Explain ML briefly',
  'Define API',
  'What is a prompt?',
  'How does caching work?',
  'What is observability?',
  'Explain tokens',
  'What is Portkey?',
  'Define embedding',
  'What is clustering?',
  'Explain DNA extraction',
  'What is lineage?',
  'Define mutation',
  'What is a template?',
  'Explain evolution',
  'What is a family?',
  'Define similarity',
  'What is drift?',
  'Explain tracking',
  'What is analysis?',
]

export default function LogGenerator({
  onLogGenerated,
  isGenerating,
  setIsGenerating,
}: LogGeneratorProps) {
  const [prompt, setPrompt] = useState('')
  const [model, setModel] = useState('gpt-4o-mini')
  const [isAutoGenerating, setIsAutoGenerating] = useState(false)
  const [generationRate, setGenerationRate] = useState(2)
  const [useMock, setUseMock] = useState(process.env.NEXT_PUBLIC_MOCK_MODE === 'true')
  const [error, setError] = useState<string | null>(null)
  const autoGenRef = useRef(false)

  const handleGenerate = async () => {
    if (!prompt.trim()) return

    setIsGenerating(true)
    setError(null)
    try {
      const result = await generateLog(prompt, model, useMock)

      if (!result.success && result.error) {
        throw new Error(result.error)
      }

      const logEntry: LogEntry = {
        id: `log-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date().toISOString(),
        prompt,
        response: result.content || '',
        model: result.isMock ? `${model} (mock)` : model,
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
        status: result.success ? 'success' : 'error',
        error: result.success ? undefined : result.error,
      }

      onLogGenerated(logEntry)
      if (!isAutoGenerating) {
        setPrompt('')
      }
    } catch (error: any) {
      const errorMessage = error.message || 'Unknown error'
      setError(errorMessage)
      const logEntry: LogEntry = {
        id: `log-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date().toISOString(),
        prompt,
        response: '',
        model,
        status: 'error',
        error: errorMessage,
      }
      onLogGenerated(logEntry)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleAutoGenerate = async () => {
    if (autoGenRef.current) {
      autoGenRef.current = false
      setIsAutoGenerating(false)
      return
    }

    autoGenRef.current = true
    setIsAutoGenerating(true)
    const delay = Math.max(50, 1000 / generationRate)

    const generateLoop = async () => {
      while (autoGenRef.current) {
        const randomIndex = Math.floor(Math.random() * SAMPLE_PROMPTS.length)
        const randomPrompt = SAMPLE_PROMPTS[randomIndex]
        setPrompt(randomPrompt)
        
        setIsGenerating(true)
        try {
          const result = await generateLog(randomPrompt, model, useMock)

          const logEntry: LogEntry = {
            id: `log-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            timestamp: new Date().toISOString(),
            prompt: randomPrompt,
            response: result.success ? (result.content || '') : (result.error || 'Error'),
            model: result.isMock ? `${model} (mock)` : model,
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
            status: result.success ? 'success' : 'error',
            error: result.success ? undefined : result.error,
          }
          onLogGenerated(logEntry)
        } catch (error: any) {
          const logEntry: LogEntry = {
            id: `log-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            timestamp: new Date().toISOString(),
            prompt: randomPrompt,
            response: '',
            model,
            status: 'error',
            error: error.message || 'Unknown error',
          }
          onLogGenerated(logEntry)
        } finally {
          setIsGenerating(false)
        }
        
        if (autoGenRef.current) {
          await new Promise((resolve) => setTimeout(resolve, delay))
        }
      }
      autoGenRef.current = false
      setIsAutoGenerating(false)
    }

    generateLoop().catch((error) => {
      console.error('Auto generation error:', error)
      autoGenRef.current = false
      setIsAutoGenerating(false)
    })
  }

  const handleSamplePrompt = () => {
    const randomPrompt = SAMPLE_PROMPTS[Math.floor(Math.random() * SAMPLE_PROMPTS.length)]
    setPrompt(randomPrompt)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generate Logs</CardTitle>
        <CardDescription>
          Create prompt logs for Portkey observability
        </CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4">
            <ErrorDisplay error={error} />
          </div>
        )}
        <div className="space-y-5">
        <div>
          <label className="block text-sm font-semibold mb-2">Prompt</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter a short prompt..."
            className="w-full px-4 py-3 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring focus:ring-offset-2"
            rows={3}
          />
          <Button
            onClick={handleSamplePrompt}
            variant="ghost"
            size="sm"
            className="mt-2 text-xs"
          >
            Use Sample Prompt
          </Button>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold mb-2">Model</label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full px-4 py-2 border border-input bg-background rounded-lg focus:ring-2 focus:ring-ring focus:ring-offset-2"
              disabled={useMock}
            >
              <option value="gpt-4o-mini">GPT-4o Mini</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-semibold mb-2">Mode</label>
            <div className="flex items-center h-10">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={useMock}
                  onChange={(e) => setUseMock(e.target.checked)}
                  className="mr-2 h-4 w-4"
                />
                <span className="text-sm">Mock Mode</span>
              </label>
            </div>
            {useMock && (
              <Badge variant="secondary" className="mt-1 text-xs">
                Mock Mode
              </Badge>
            )}
          </div>
        </div>

        <Button
          onClick={handleGenerate}
          disabled={isGenerating || !prompt.trim()}
          className="w-full font-semibold h-11"
          size="lg"
        >
          {isGenerating ? (
            <>
              <span className="animate-spin mr-2">?</span>
              Generating...
            </>
          ) : (
            'Generate Log'
          )}
        </Button>

        <div className="border-t pt-4 mt-4">
          <h3 className="text-lg font-semibold mb-4">Auto Generation</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold mb-3">
                Rate: <span className="text-blue-600 font-bold">{generationRate.toFixed(1)}</span> log{generationRate !== 1 ? 's' : ''} per second
                {useMock && (
                  <span className="ml-2 text-xs text-green-600 font-normal">
                    (Can go up to 30+ in mock mode)
                  </span>
                )}
              </label>
              <input
                type="range"
                min="0.1"
                max={useMock ? "30" : "10"}
                step="0.1"
                value={generationRate}
                onChange={(e) => setGenerationRate(parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                disabled={isAutoGenerating}
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>0.1/s</span>
                <span>{useMock ? "30/s" : "10/s"}</span>
              </div>
            </div>
            <Button
              onClick={handleAutoGenerate}
              variant={isAutoGenerating ? 'destructive' : 'default'}
              className="w-full font-semibold h-11"
              size="lg"
              disabled={isGenerating && !isAutoGenerating}
            >
              {isAutoGenerating ? (
                <>
                  <span className="animate-pulse mr-2">?</span>
                  Stop Auto Generation
                </>
              ) : (
                'Start Auto Generation'
              )}
            </Button>
            {isAutoGenerating && (
              <p className="text-xs text-center text-muted-foreground animate-pulse">
                Generating logs automatically...
              </p>
            )}
          </div>
        </div>
        </div>
      </CardContent>
    </Card>
  )
}
