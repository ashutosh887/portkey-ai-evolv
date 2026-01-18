'use client'

import { useState, useRef } from 'react'
import { generateLog, generateRandomPrompt } from '@/lib/portkey'
import { LogEntry } from '@/types/log'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import ErrorDisplay from './ErrorDisplay'
import config from '@/config'

interface LogGeneratorProps {
  onLogGenerated: (log: LogEntry) => void
  isGenerating: boolean
  setIsGenerating: (value: boolean) => void
}

// Diverse prompts organized by semantic clusters for testing classification
const SAMPLE_PROMPTS = [
  // === SUMMARIZATION CLUSTER ===
  'Summarize this article in 3 bullet points',
  'Give me a brief summary of the document',
  'TL;DR this content for me',
  'Provide a concise overview of the main points',
  'Summarize the key takeaways',

  // === CODE GENERATION CLUSTER ===
  'Write a Python function to sort a list',
  'Generate code to read a CSV file in Python',
  'Create a JavaScript function for form validation',
  'Write a SQL query to get top 10 customers',
  'Implement a binary search algorithm',

  // === TRANSLATION CLUSTER ===
  'Translate this text to French',
  'Convert this paragraph to Spanish',
  'Translate the following to German',
  'Help me translate this to Japanese',
  'Convert this English text to Portuguese',

  // === EXPLANATION CLUSTER ===
  'Explain machine learning to a 5 year old',
  'What is quantum computing in simple terms?',
  'Explain how neural networks work',
  'Describe the concept of blockchain simply',
  'What is API and how does it work?',

  // === CREATIVE WRITING CLUSTER ===
  'Write a short poem about technology',
  'Create a haiku about artificial intelligence',
  'Write a tagline for a tech startup',
  'Generate a creative product description',
  'Write a catchy headline for this news',

  // === DATA ANALYSIS CLUSTER ===
  'Analyze this sales data and find trends',
  'What insights can you find in this dataset?',
  'Identify patterns in this user behavior data',
  'Find anomalies in the following metrics',
  'Generate a statistical summary of this data',

  // === EMAIL/COMMUNICATION CLUSTER ===
  'Write a professional email to a client',
  'Draft a follow-up email after a meeting',
  'Compose a thank you note for an interview',
  'Write an apology email for delayed delivery',
  'Create a meeting invitation email',

  // === QUESTION ANSWERING CLUSTER ===
  'What is the capital of France?',
  'Who invented the telephone?',
  'When was the first iPhone released?',
  'How many planets are in our solar system?',
  'What causes climate change?',

  // === DEBUGGING/TROUBLESHOOTING CLUSTER ===
  'Why is my Python code throwing a NameError?',
  'Debug this JavaScript async function',
  'Fix the memory leak in this code',
  'Why is my SQL query running slow?',
  'Help me fix this null pointer exception',

  // === FORMATTING/CONVERSION CLUSTER ===
  'Convert this JSON to YAML format',
  'Reformat this data as a markdown table',
  'Convert these bullet points to numbered list',
  'Transform this CSV data to JSON',
  'Format this text as HTML',
]


export default function LogGenerator({
  onLogGenerated,
  isGenerating,
  setIsGenerating,
}: LogGeneratorProps) {
  const [prompt, setPrompt] = useState('')
  const [model, setModel] = useState(config.portkey.defaultModel)
  const [isAutoGenerating, setIsAutoGenerating] = useState(false)
  const [generationRate, setGenerationRate] = useState(config.logs.defaultAutoGenerationRate)
  const [useMock, setUseMock] = useState(config.portkey.mockMode)
  const [useLLMPrompts, setUseLLMPrompts] = useState(true) // Use LLM to generate diverse prompts
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
        // Get prompt: either LLM-generated or from static list
        let randomPrompt: string
        if (useLLMPrompts) {
          randomPrompt = await generateRandomPrompt(useMock)
        } else {
          const randomIndex = Math.floor(Math.random() * SAMPLE_PROMPTS.length)
          randomPrompt = SAMPLE_PROMPTS[randomIndex]
        }
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
      autoGenRef.current = false
      setIsAutoGenerating(false)
    })
  }

  const handleSamplePrompt = () => {
    const randomPrompt = config.samplePrompts[Math.floor(Math.random() * config.samplePrompts.length)]
    setPrompt(randomPrompt)
  }

  return (
    <Card className="h-fit sticky top-4">
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
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Prompt</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter a short prompt..."
              className="w-full px-3 sm:px-4 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:ring-offset-2 resize-none transition-colors"
              rows={3}
            />
            <Button
              onClick={handleSamplePrompt}
              variant="ghost"
              size="sm"
              className="mt-2 text-xs h-7"
            >
              Use Sample Prompt
            </Button>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Model</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full px-3 sm:px-4 py-2 border border-input bg-background rounded-md focus:ring-2 focus:ring-ring focus:ring-offset-2 text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={useMock}
              >
                {config.portkey.models.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Mode</label>
              <div className="flex items-center h-10">
                <label className="flex items-center cursor-pointer gap-2">
                  <input
                    type="checkbox"
                    checked={useMock}
                    onChange={(e) => setUseMock(e.target.checked)}
                    className="h-4 w-4 cursor-pointer"
                  />
                  <span className="text-sm">Mock Mode</span>
                </label>
              </div>
              {useMock && (
                <Badge variant="secondary" className="mt-1.5 text-xs">
                  Mock Mode
                </Badge>
              )}
            </div>
          </div>
          {/* LLM Prompts Toggle */}
          <div className="flex items-center gap-2 py-2 px-3 bg-slate-50 rounded-md">
            <label className="flex items-center cursor-pointer gap-2 flex-1">
              <input
                type="checkbox"
                checked={useLLMPrompts}
                onChange={(e) => setUseLLMPrompts(e.target.checked)}
                className="h-4 w-4 cursor-pointer accent-blue-600"
              />
              <span className="text-sm font-medium">Use LLM-Generated Prompts</span>
            </label>
            {useLLMPrompts && (
              <Badge variant="default" className="text-xs bg-blue-600">
                75+ Dynamic Prompts
              </Badge>
            )}
          </div>

          <Button
            onClick={handleGenerate}
            disabled={isGenerating || !prompt.trim()}
            className="w-full transition-all"
          >
            {isGenerating ? 'Generating...' : 'Generate Log'}
          </Button>

          <div className="border-t pt-4 mt-4">
            <h3 className="text-base sm:text-lg font-semibold mb-3">Auto Generation</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Rate: <span className="font-semibold text-blue-600">{generationRate.toFixed(1)}</span> log{generationRate !== 1 ? 's' : ''} per second
                  {useMock && (
                    <span className="ml-2 text-xs text-green-600 font-normal">
                      (up to 30+ in mock)
                    </span>
                  )}
                </label>
                <input
                  type="range"
                  min="0.1"
                  max={useMock ? config.logs.maxAutoGenerationRate.toString() : "10"}
                  step="0.1"
                  value={generationRate}
                  onChange={(e) => setGenerationRate(parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={isAutoGenerating}
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>0.1/s</span>
                  <span>{useMock ? `${config.logs.maxAutoGenerationRate}/s` : "10/s"}</span>
                </div>
              </div>
              <Button
                onClick={handleAutoGenerate}
                variant={isAutoGenerating ? 'destructive' : 'default'}
                className="w-full transition-all"
                disabled={isGenerating && !isAutoGenerating}
              >
                {isAutoGenerating ? 'Stop Auto Generation' : 'Start Auto Generation'}
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
