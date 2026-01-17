'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { api, Stats, Family, Prompt } from '@/lib/api'
import { Database, Users, FileText, TrendingUp, RefreshCw, Zap, AlertCircle } from 'lucide-react'
import Link from 'next/link'

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [families, setFamilies] = useState<Family[]>([])
  const [recentPrompts, setRecentPrompts] = useState<Prompt[]>([])
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadData = async () => {
    try {
      setError(null)
      const [statsData, familiesData, promptsData] = await Promise.all([
        api.stats(),
        api.families({ limit: 5, sort: 'created_at' }),
        api.prompts({ limit: 5 }),
      ])
      setStats(statsData)
      setFamilies(familiesData.families)
      setRecentPrompts(promptsData.prompts)
    } catch (err: any) {
      setError(err.message || 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handleProcess = async () => {
    setProcessing(true)
    try {
      await api.process(100)
      await loadData()
    } catch (err: any) {
      setError(err.message || 'Failed to process prompts')
    } finally {
      setProcessing(false)
    }
  }

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold tracking-tight mb-2">Dashboard</h1>
            <p className="text-muted-foreground">Overview of your prompt genome</p>
          </div>
          <div className="flex gap-3">
            <Button onClick={loadData} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button onClick={handleProcess} disabled={processing} size="sm">
              {processing ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4 mr-2" />
                  Process Pending
                </>
              )}
            </Button>
          </div>
        </div>

        {error && (
          <Card className="mb-6 border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-red-800">
                <AlertCircle className="h-5 w-5" />
                <p>{error}</p>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Prompts</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats?.prompts.total || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {stats?.prompts.pending || 0} pending
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Families</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats?.families.total || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Avg {stats?.families.average_size?.toFixed(1) || 0} members
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Templates</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats?.templates.extracted || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Extracted templates
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Processed</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats?.prompts.processed || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {stats?.prompts.total ? Math.round((stats.prompts.processed / stats.prompts.total) * 100) : 0}% complete
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Recent Families</CardTitle>
                  <CardDescription>Latest prompt families</CardDescription>
                </div>
                <Link href="/families">
                  <Button variant="ghost" size="sm">View All</Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              {families.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Users className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No families yet</p>
                  <p className="text-xs mt-1">Process prompts to create families</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {families.map((family) => (
                    <Link
                      key={family.family_id}
                      href={`/families/${family.family_id}`}
                      className="block p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h4 className="font-semibold text-sm">{family.family_name}</h4>
                          <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
                            {family.description || 'No description'}
                          </p>
                        </div>
                        <Badge variant="secondary" className="ml-3">
                          {family.member_count} members
                        </Badge>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Recent Prompts</CardTitle>
                  <CardDescription>Latest ingested prompts</CardDescription>
                </div>
                <Link href="/prompts">
                  <Button variant="ghost" size="sm">View All</Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              {recentPrompts.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Database className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No prompts yet</p>
                  <p className="text-xs mt-1">Ingest prompts to get started</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {recentPrompts.map((prompt) => (
                    <Link
                      key={prompt.prompt_id}
                      href={`/prompts/${prompt.prompt_id}`}
                      className="block p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                    >
                      <p className="text-sm line-clamp-2 mb-2">{prompt.original_text}</p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        {prompt.family_id && (
                          <Badge variant="outline" className="text-xs">
                            Family
                          </Badge>
                        )}
                        {prompt.lineage?.has_lineage && (
                          <Badge variant="outline" className="text-xs">
                            Lineage
                          </Badge>
                        )}
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
