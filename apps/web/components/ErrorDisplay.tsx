'use client'

import { AlertCircle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface ErrorDisplayProps {
  error: string
}

export default function ErrorDisplay({ error }: ErrorDisplayProps) {
  const isApiKeyError = error.includes('API_KEY') || error.includes('api key')
  const isProviderError = error.includes('provider') || error.includes('PROVIDER')

  return (
    <Card className="border-red-200 bg-red-50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-red-800">
          <AlertCircle className="h-5 w-5" />
          Error
        </CardTitle>
        <CardDescription className="text-red-700">
          {isApiKeyError && 'API key configuration issue'}
          {isProviderError && 'Provider configuration issue'}
          {!isApiKeyError && !isProviderError && 'Request failed'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <p className="text-sm text-red-800 font-mono bg-red-100 p-3 rounded border border-red-200">
            {error}
          </p>
          {isApiKeyError && (
            <div className="text-xs text-red-700 space-y-1">
              <p>Make sure you have:</p>
              <ul className="list-disc list-inside ml-2 space-y-1">
                <li>Set NEXT_PUBLIC_PORTKEY_API_KEY in .env.local</li>
                <li>API key has LOGS permissions enabled</li>
                <li>Restarted the dev server after adding env vars</li>
              </ul>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
