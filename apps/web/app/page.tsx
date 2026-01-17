'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Database, Zap, TrendingUp, BarChart3, GitBranch, FileCode } from 'lucide-react'
import Link from 'next/link'
import Logo from '@/components/Logo'
import config from '@/config'

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-16 lg:py-24">
        <div className="text-center mb-20 max-w-3xl mx-auto">
          <div className="inline-flex items-center justify-center mb-8">
            <div className="p-3 bg-blue-600 rounded-lg">
              <Logo className="h-8 w-8 text-white" />
            </div>
          </div>
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight mb-6 text-gray-900">
            {config.appName}
          </h1>
          <p className="text-xl sm:text-2xl text-gray-600 mb-6">
            {config.appDescription}
          </p>
          <p className="text-base sm:text-lg text-gray-500 mb-10 max-w-2xl mx-auto">
            {config.appFullDescription}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/dashboard">
              <Button size="lg" className="px-8">
                View Dashboard
              </Button>
            </Link>
            <Link href="/logs">
              <Button size="lg" variant="outline" className="px-8">
                Generate Logs
              </Button>
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto mb-20">
          <Card className="border hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="w-10 h-10 rounded bg-blue-50 flex items-center justify-center mb-3">
                <Database className="h-5 w-5 text-blue-600" />
              </div>
              <CardTitle className="text-lg mb-1">{config.features.promptGenome.title}</CardTitle>
              <CardDescription>
                {config.features.promptGenome.description}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-gray-600">
                {config.features.promptGenome.items.map((item, idx) => (
                  <li key={idx}>• {item}</li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card className="border hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="w-10 h-10 rounded bg-green-50 flex items-center justify-center mb-3">
                <Zap className="h-5 w-5 text-green-600" />
              </div>
              <CardTitle className="text-lg mb-1">{config.features.realtimeAnalysis.title}</CardTitle>
              <CardDescription>
                {config.features.realtimeAnalysis.description}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-gray-600">
                {config.features.realtimeAnalysis.items.map((item, idx) => (
                  <li key={idx}>• {item}</li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card className="border hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="w-10 h-10 rounded bg-purple-50 flex items-center justify-center mb-3">
                <GitBranch className="h-5 w-5 text-purple-600" />
              </div>
              <CardTitle className="text-lg mb-1">{config.features.evolutionTracking.title}</CardTitle>
              <CardDescription>
                {config.features.evolutionTracking.description}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-gray-600">
                {config.features.evolutionTracking.items.map((item, idx) => (
                  <li key={idx}>• {item}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>

        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3 text-gray-900">How It Works</h2>
            <p className="text-gray-600">Four steps to transform your prompts</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            <Card className="text-center border hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center mx-auto mb-3">
                  <span className="text-lg font-semibold text-blue-600">1</span>
                </div>
                <CardTitle className="text-base">Ingest</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  Collect prompts from Portkey logs, files, or repositories
                </p>
              </CardContent>
            </Card>
            <Card className="text-center border hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="w-12 h-12 rounded-full bg-green-50 flex items-center justify-center mx-auto mb-3">
                  <span className="text-lg font-semibold text-green-600">2</span>
                </div>
                <CardTitle className="text-base">Extract DNA</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  Parse structure, detect variables, extract instructions
                </p>
              </CardContent>
            </Card>
            <Card className="text-center border hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="w-12 h-12 rounded-full bg-purple-50 flex items-center justify-center mx-auto mb-3">
                  <span className="text-lg font-semibold text-purple-600">3</span>
                </div>
                <CardTitle className="text-base">Cluster</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  Group similar prompts into families using semantic clustering
                </p>
              </CardContent>
            </Card>
            <Card className="text-center border hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="w-12 h-12 rounded-full bg-orange-50 flex items-center justify-center mx-auto mb-3">
                  <span className="text-lg font-semibold text-orange-600">4</span>
                </div>
                <CardTitle className="text-base">Track</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  Monitor changes, detect mutations, maintain lineage
                </p>
              </CardContent>
            </Card>
          </div>

          <Card className="bg-gray-50 border">
            <CardHeader>
              <CardTitle className="text-xl mb-2 flex items-center gap-2">
                <FileCode className="h-5 w-5 text-gray-700" />
                Portkey Integration
              </CardTitle>
              <CardDescription>
                Deep integration with Portkey AI for observability and LLM orchestration
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="flex items-start gap-3">
                  <Database className="h-5 w-5 text-gray-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold mb-1 text-sm">Observability Logs</h4>
                    <p className="text-sm text-gray-600">
                      Ingest real production prompts from Portkey observability logs
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Zap className="h-5 w-5 text-gray-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold mb-1 text-sm">LLM Orchestration</h4>
                    <p className="text-sm text-gray-600">
                      Use Portkey for template extraction with fallbacks and caching
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <TrendingUp className="h-5 w-5 text-gray-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold mb-1 text-sm">Full Tracing</h4>
                    <p className="text-sm text-gray-600">
                      Every decision is traced and explainable through Portkey
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
