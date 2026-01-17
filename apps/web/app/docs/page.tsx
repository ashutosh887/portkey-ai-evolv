'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Book, Code, Settings } from 'lucide-react'
import Link from 'next/link'

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto px-4 py-16 max-w-4xl">
        <Link href="/">
          <Button variant="ghost" className="mb-8">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Home
          </Button>
        </Link>

        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-4">Documentation</h1>
          <p className="text-lg text-muted-foreground">
            Learn how to use Evolv to manage and analyze your prompts
          </p>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Setup
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Environment Variables</h3>
                <p className="text-sm text-muted-foreground mb-2">
                  Create a <code className="bg-muted px-1 py-0.5 rounded">.env.local</code> file in <code className="bg-muted px-1 py-0.5 rounded">apps/web</code>:
                </p>
                <pre className="bg-slate-950 text-slate-50 p-4 rounded-lg text-xs overflow-x-auto">
{`NEXT_PUBLIC_PORTKEY_API_KEY=your_portkey_api_key_here
NEXT_PUBLIC_PORTKEY_PROVIDER=your_provider_id_here
NEXT_PUBLIC_MOCK_MODE=false`}
                </pre>
                <p className="text-xs text-muted-foreground mt-2">
                  Note: Provider is optional. If you have a provider configured in Portkey dashboard, 
                  you can reference it here. Otherwise, Portkey will use your default gateway configuration.
                </p>
              </div>
              <div>
                <h3 className="font-semibold mb-2">API Key Permissions</h3>
                <p className="text-sm text-muted-foreground">
                  Your Portkey API key needs the following permissions:
                </p>
                <ul className="list-disc list-inside mt-2 text-sm text-muted-foreground space-y-1">
                  <li>Portkey API key: LOGS and COMPLETIONS permissions</li>
                  <li>Provider: Optional - use if you have a provider configured in Portkey dashboard</li>
                  <li>Portkey gateway handles all provider authentication</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5" />
                API Integration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Direct HTTP Calls</h3>
                <p className="text-sm text-muted-foreground mb-2">
                  Evolv uses direct HTTP calls to Portkey API (no SDK required):
                </p>
                <pre className="bg-slate-950 text-slate-50 p-4 rounded-lg text-xs overflow-x-auto">
{`fetch('https://api.portkey.ai/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-portkey-api-key': 'YOUR_PORTKEY_API_KEY',
    'x-portkey-provider': 'YOUR_PROVIDER_ID',
    'x-portkey-debug': 'true'
  },
  body: JSON.stringify({
    model: 'gpt-3.5-turbo',
    messages: [{ role: 'user', content: 'Your prompt' }]
  })
})`}
                </pre>
                <p className="text-xs text-muted-foreground mt-2">
                  Note: x-portkey-provider is optional if you have a default provider configured in Portkey.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Book className="h-5 w-5" />
                Usage
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Generating Logs</h3>
                <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
                  <li>Navigate to <Link href="/logs" className="text-blue-600 hover:underline">/logs</Link></li>
                  <li>Enter a prompt or use a sample prompt</li>
                  <li>Select a model (GPT-3.5 Turbo recommended for speed)</li>
                  <li>Click "Generate Log" or enable auto-generation</li>
                  <li>Logs appear in real-time and are sent to Portkey</li>
                </ol>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Viewing Logs</h3>
                <p className="text-sm text-muted-foreground">
                  All generated logs are automatically sent to Portkey observability.
                  You can view them in the Portkey dashboard or use the Evolv API to ingest them.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
