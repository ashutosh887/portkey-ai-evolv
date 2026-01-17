'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Sparkles, Database, Zap, TrendingUp, ArrowRight } from 'lucide-react'
import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto px-4 py-8 sm:py-12 lg:py-16">
        <div className="text-center mb-12 sm:mb-16 max-w-3xl mx-auto">
          <div className="flex flex-col items-center justify-center mb-4 sm:mb-6">
            <div className="space-y-2">
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight">Evolv</h1>
              <p className="text-lg sm:text-xl text-muted-foreground">Your prompts, but smarter every week</p>
            </div>
          </div>

          <p className="text-base sm:text-lg text-muted-foreground mb-6 sm:mb-8 px-4">
            Extract DNA from prompts, track mutations, understand lineage. Transform prompt sprawl into organized, versioned templates.
          </p>

          <Link href="/logs">
            <Button size="lg" className="gap-2">
              Generate Logs
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6 max-w-5xl mx-auto mb-8 sm:mb-12">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5 text-blue-600" />
                Prompt Genome
              </CardTitle>
              <CardDescription>
                Extract DNA, track mutations, understand lineage
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• Structural parsing</li>
                <li>• Variable detection</li>
                <li>• Instruction extraction</li>
                <li>• Semantic embeddings</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-green-600" />
                Real-time Analysis
              </CardTitle>
              <CardDescription>
                Continuous processing and family detection
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• Automatic clustering</li>
                <li>• Family detection</li>
                <li>• Template synthesis</li>
                <li>• Confidence scoring</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-purple-600" />
                Evolution Tracking
              </CardTitle>
              <CardDescription>
                Monitor prompt changes and drift detection
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• Mutation detection</li>
                <li>• Drift alerts</li>
                <li>• Lineage graphs</li>
                <li>• Version control</li>
              </ul>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8 max-w-4xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle>How It Works</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-semibold">
                  1
                </div>
                <div>
                  <h4 className="font-semibold mb-1">Ingest Prompts</h4>
                  <p className="text-sm text-muted-foreground">
                    Collect prompts from Portkey logs, files, or git repositories
                  </p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-semibold">
                  2
                </div>
                <div>
                  <h4 className="font-semibold mb-1">Extract DNA</h4>
                  <p className="text-sm text-muted-foreground">
                    Parse structure, detect variables, extract instructions and generate embeddings
                  </p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-semibold">
                  3
                </div>
                <div>
                  <h4 className="font-semibold mb-1">Cluster & Analyze</h4>
                  <p className="text-sm text-muted-foreground">
                    Group similar prompts into families using semantic clustering
                  </p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-semibold">
                  4
                </div>
                <div>
                  <h4 className="font-semibold mb-1">Track Evolution</h4>
                  <p className="text-sm text-muted-foreground">
                    Monitor changes, detect mutations, and maintain lineage history
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Portkey Integration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-3">
                <Database className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div>
                  <h4 className="font-semibold mb-1">Observability Logs</h4>
                  <p className="text-sm text-muted-foreground">
                    Ingest real production prompts from Portkey observability logs
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Zap className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div>
                  <h4 className="font-semibold mb-1">LLM Orchestration</h4>
                  <p className="text-sm text-muted-foreground">
                    Use Portkey for template extraction with fallbacks and caching
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <TrendingUp className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div>
                  <h4 className="font-semibold mb-1">Full Tracing</h4>
                  <p className="text-sm text-muted-foreground">
                    Every decision is traced and explainable through Portkey
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
