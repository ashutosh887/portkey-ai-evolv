'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import { generateLog } from '@/lib/portkey'

export default function ConnectionTest() {
  const [testing, setTesting] = useState(false)
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null)

  const handleTest = async () => {
    setTesting(true)
    setResult(null)

    try {
      const portkeyApiKey = process.env.NEXT_PUBLIC_PORTKEY_API_KEY
      
      if (!portkeyApiKey) {
        setResult({
          success: false,
          message: 'NEXT_PUBLIC_PORTKEY_API_KEY is not set in environment variables',
        })
        return
      }

      const testResult = await generateLog('Test', 'gpt-4o-mini', false)

      if (testResult.success) {
        setResult({
          success: true,
          message: `Connection successful! Generated ${testResult.tokens} tokens. Log sent to Portkey.`,
        })
      } else {
        setResult({
          success: false,
          message: testResult.error || 'Connection failed',
        })
      }
    } catch (error: any) {
      setResult({
        success: false,
        message: error.message || 'Connection test failed',
      })
    } finally {
      setTesting(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Connection Test</CardTitle>
        <CardDescription>
          Test your Portkey API connection
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4">
          <div className="flex-1 space-y-1.5">
            <p className="text-sm text-muted-foreground">
              Portkey API Key: <span className={process.env.NEXT_PUBLIC_PORTKEY_API_KEY ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>{process.env.NEXT_PUBLIC_PORTKEY_API_KEY ? '✓ Set' : '✗ Not set'}</span>
            </p>
            <p className="text-xs text-muted-foreground">
              Virtual Key: <span className={process.env.NEXT_PUBLIC_PORTKEY_VIRTUAL_KEY ? 'text-green-600' : 'text-muted-foreground'}>{process.env.NEXT_PUBLIC_PORTKEY_VIRTUAL_KEY ? '✓ Set' : 'Not set'}</span>
            </p>
            <p className="text-xs text-muted-foreground">
              Config ID: <span className={process.env.NEXT_PUBLIC_PORTKEY_CONFIG_ID ? 'text-green-600' : 'text-muted-foreground'}>{process.env.NEXT_PUBLIC_PORTKEY_CONFIG_ID ? '✓ Set' : 'Not set'}</span>
            </p>
            {!process.env.NEXT_PUBLIC_PORTKEY_API_KEY && (
              <p className="text-xs text-red-600 mt-1 font-medium">
                Add NEXT_PUBLIC_PORTKEY_API_KEY to .env.local
              </p>
            )}
          </div>
          <Button onClick={handleTest} disabled={testing} className="w-full sm:w-auto">
            {testing ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Testing...
              </>
            ) : (
              'Test Connection'
            )}
          </Button>
        </div>

        {result && (
          <div
            className={`p-4 rounded-lg border ${
              result.success
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            }`}
          >
            <div className="flex items-start gap-2">
              {result.success ? (
                <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
              ) : (
                <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
              )}
              <div className="flex-1">
                <p
                  className={`text-sm ${
                    result.success ? 'text-green-800' : 'text-red-800'
                  }`}
                >
                  {result.message}
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="text-xs text-muted-foreground space-y-2 pt-2 border-t">
          <p className="font-medium">Make sure:</p>
          <ul className="list-disc list-inside ml-2 space-y-1.5">
            <li>Portkey API key has LOGS and COMPLETIONS permissions</li>
            <li>Virtual Key or Config ID configured in Portkey dashboard (optional)</li>
            <li>Environment variables are in .env.local</li>
            <li>Dev server was restarted after adding env vars</li>
            <li>Check Portkey dashboard Logs section to see generated logs</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  )
}
