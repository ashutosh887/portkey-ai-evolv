'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Sparkles, Database, Zap, TrendingUp, ArrowRight, BarChart3, GitBranch, FileCode } from 'lucide-react'
import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <div className="container mx-auto px-4 py-12 sm:py-16 lg:py-20">
        <div className="text-center mb-16 sm:mb-20 max-w-4xl mx-auto">
          <div className="inline-flex items-center justify-center mb-6">
            <div className="p-3 bg-blue-600 rounded-2xl shadow-lg">
              <Sparkles className="h-8 w-8 text-white" />
            </div>
          </div>
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Evolv
          </h1>
          <p className="text-xl sm:text-2xl text-muted-foreground mb-6 font-medium">
            Your prompts, but smarter every week
          </p>
          <p className="text-base sm:text-lg text-muted-foreground mb-8 px-4 max-w-2xl mx-auto">
            Extract DNA from prompts, track mutations, understand lineage. Transform prompt sprawl into organized, versioned templates with automatic family detection.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link href="/dashboard">
              <Button size="lg" className="gap-2 text-base px-8 py-6">
                <BarChart3 className="h-5 w-5" />
                View Dashboard
              </Button>
            </Link>
            <Link href="/logs">
              <Button size="lg" variant="outline" className="gap-2 text-base px-8 py-6">
                <Zap className="h-5 w-5" />
                Generate Logs
              </Button>
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto mb-16">
          <Card className="border-2 hover:shadow-xl transition-all duration-300 hover:border-blue-200">
            <CardHeader>
              <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center mb-4">
                <Database className="h-6 w-6 text-blue-600" />
              </div>
              <CardTitle className="text-xl mb-2">Prompt Genome</CardTitle>
              <CardDescription className="text-base">
                Extract DNA, track mutations, understand lineage
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 mt-1">•</span>
                  <span>Structural parsing (system/user/assistant)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 mt-1">•</span>
                  <span>Variable detection ({{name}}, {input}, etc.)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 mt-1">•</span>
                  <span>Instruction extraction (tone, format, constraints)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 mt-1">•</span>
                  <span>Semantic embeddings (384-dim vectors)</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          <Card className="border-2 hover:shadow-xl transition-all duration-300 hover:border-green-200">
            <CardHeader>
              <div className="w-12 h-12 rounded-lg bg-green-100 flex items-center justify-center mb-4">
                <Zap className="h-6 w-6 text-green-600" />
              </div>
              <CardTitle className="text-xl mb-2">Real-time Analysis</CardTitle>
              <CardDescription className="text-base">
                Continuous processing and family detection
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-green-600 mt-1">•</span>
                  <span>Automatic clustering (HDBSCAN)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-600 mt-1">•</span>
                  <span>Family detection with confidence scores</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-600 mt-1">•</span>
                  <span>LLM-powered template synthesis</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-600 mt-1">•</span>
                  <span>Incremental processing (no full reprocessing)</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          <Card className="border-2 hover:shadow-xl transition-all duration-300 hover:border-purple-200">
            <CardHeader>
              <div className="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center mb-4">
                <GitBranch className="h-6 w-6 text-purple-600" />
              </div>
              <CardTitle className="text-xl mb-2">Evolution Tracking</CardTitle>
              <CardDescription className="text-base">
                Monitor prompt changes and drift detection
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-purple-600 mt-1">•</span>
                  <span>Mutation detection (variable, structure, semantic)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-600 mt-1">•</span>
                  <span>Lineage graphs (ancestors & descendants)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-600 mt-1">•</span>
                  <span>Drift alerts and divergence detection</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-600 mt-1">•</span>
                  <span>Version control for prompt families</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>

        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">How It Works</h2>
            <p className="text-muted-foreground text-lg">Four simple steps to transform your prompts</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            <Card className="text-center border-2 hover:shadow-lg transition-all">
              <CardHeader>
                <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-blue-600">1</span>
                </div>
                <CardTitle className="text-lg">Ingest</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Collect prompts from Portkey logs, files, or repositories
                </p>
              </CardContent>
            </Card>
            <Card className="text-center border-2 hover:shadow-lg transition-all">
              <CardHeader>
                <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-green-600">2</span>
                </div>
                <CardTitle className="text-lg">Extract DNA</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Parse structure, detect variables, extract instructions and generate embeddings
                </p>
              </CardContent>
            </Card>
            <Card className="text-center border-2 hover:shadow-lg transition-all">
              <CardHeader>
                <div className="w-16 h-16 rounded-full bg-purple-100 flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-purple-600">3</span>
                </div>
                <CardTitle className="text-lg">Cluster</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Group similar prompts into families using semantic clustering
                </p>
              </CardContent>
            </Card>
            <Card className="text-center border-2 hover:shadow-lg transition-all">
              <CardHeader>
                <div className="w-16 h-16 rounded-full bg-orange-100 flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-orange-600">4</span>
                </div>
                <CardTitle className="text-lg">Track</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Monitor changes, detect mutations, and maintain lineage history
                </p>
              </CardContent>
            </Card>
          </div>

          <Card className="bg-gradient-to-br from-blue-50 to-purple-50 border-2 border-blue-200">
            <CardHeader>
              <CardTitle className="text-2xl mb-2 flex items-center gap-3">
                <FileCode className="h-6 w-6 text-blue-600" />
                Portkey Integration
              </CardTitle>
              <CardDescription className="text-base">
                Deep integration with Portkey AI for observability and LLM orchestration
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="flex items-start gap-3">
                  <Database className="h-6 w-6 text-blue-600 mt-1 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold mb-1">Observability Logs</h4>
                    <p className="text-sm text-muted-foreground">
                      Ingest real production prompts from Portkey observability logs
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Zap className="h-6 w-6 text-green-600 mt-1 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold mb-1">LLM Orchestration</h4>
                    <p className="text-sm text-muted-foreground">
                      Use Portkey for template extraction with fallbacks and caching
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <TrendingUp className="h-6 w-6 text-purple-600 mt-1 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold mb-1">Full Tracing</h4>
                    <p className="text-sm text-muted-foreground">
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
