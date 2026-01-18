'use client'

import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { api, Prompt, LineageLink } from '@/lib/api'
import { RefreshCw, ArrowLeft, AlertCircle, Link as LinkIcon, Users, Code2 } from 'lucide-react'
import Link from 'next/link'
import toast from 'react-hot-toast'

export default function PromptDetailPage() {
  const params = useParams()
  const promptId = params.id as string

  const [prompt, setPrompt] = useState<Prompt | null>(null)
  const [lineage, setLineage] = useState<LineageLink[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadPrompt = useCallback(async () => {
    try {
      setError(null)
      const [promptData, lineageData] = await Promise.all([
        api.prompt(promptId),
        api.lineage(promptId).catch(() => ({ lineage: [], total_links: 0 })),
      ])
      setPrompt(promptData)
      setLineage(lineageData.lineage || [])
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load prompt'
      setError(errorMessage)
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [promptId])

  useEffect(() => {
    if (promptId) {
      loadPrompt()
    }
  }, [promptId, loadPrompt])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-muted-foreground">Loading prompt...</p>
        </div>
      </div>
    )
  }

  if (error || !prompt) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8 max-w-7xl">
          <Link href="/prompts">
            <Button variant="ghost" className="mb-6">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Prompts
            </Button>
          </Link>
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-red-800">
                <AlertCircle className="h-5 w-5" />
                <p>{error || 'Prompt not found'}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  const ancestors = lineage.filter((l) => l.direction === 'ancestor')
  const descendants = lineage.filter((l) => l.direction === 'descendant')

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <Link href="/prompts">
          <Button variant="ghost" className="mb-6">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Prompts
          </Button>
        </Link>

        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex-1">
              <h1 className="text-3xl font-bold tracking-tight mb-2">Prompt Details</h1>
              <p className="text-muted-foreground">ID: {prompt.prompt_id}</p>
            </div>
            <div className="flex gap-2">
              {prompt.family_id && (
                <Link href={`/families/${prompt.family_id}`}>
                  <Badge variant="secondary" className="text-base px-4 py-2">
                    <Users className="h-4 w-4 mr-2" />
                    View Family
                  </Badge>
                </Link>
              )}
            </div>
          </div>
        </div>

        <Tabs defaultValue="overview" className="mb-6">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="dna">DNA Structure</TabsTrigger>
            <TabsTrigger value="lineage">Evolution Lineage</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Prompt Text</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="p-4 bg-slate-50 rounded-lg border">
                    <p className="text-sm whitespace-pre-wrap">{prompt.original_text}</p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Metadata</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground mb-1">Family</p>
                    {prompt.family ? (
                      <Link href={`/families/${prompt.family_id}`}>
                        <Badge variant="secondary" className="hover:bg-secondary/80">
                          {prompt.family.family_name}
                        </Badge>
                      </Link>
                    ) : (
                      <p className="text-sm">Not assigned</p>
                    )}
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground mb-1">Created</p>
                    <p className="text-sm">
                      {new Date(prompt.created_at).toLocaleString()}
                    </p>
                  </div>
                  {prompt.lineage && (
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground mb-1">Lineage</p>
                      <div className="flex gap-2">
                        <Badge variant="outline">
                          {prompt.lineage.ancestors} ancestors
                        </Badge>
                        <Badge variant="outline">
                          {prompt.lineage.descendants} descendants
                        </Badge>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="dna" className="mt-6">
            {prompt.dna ? (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Structure</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {prompt.dna.structure.system_message && (
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground mb-1">
                          System Message
                        </p>
                        <p className="text-sm bg-slate-50 p-2 rounded border">
                          {prompt.dna.structure.system_message}
                        </p>
                      </div>
                    )}
                    {prompt.dna.structure.user_message && (
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground mb-1">
                          User Message
                        </p>
                        <p className="text-sm bg-slate-50 p-2 rounded border">
                          {prompt.dna.structure.user_message}
                        </p>
                      </div>
                    )}
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground mb-1">
                        Total Tokens
                      </p>
                      <p className="text-sm">{prompt.dna.structure.total_tokens}</p>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Variables</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {prompt.dna.variables.detected.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {prompt.dna.variables.detected.map((varName) => (
                          <Badge key={varName} variant="secondary">
                            {varName}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">No variables detected</p>
                    )}
                    <p className="text-xs text-muted-foreground mt-3">
                      Slots: {prompt.dna.variables.slots}
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Instructions</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {prompt.dna.instructions.tone.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground mb-1">Tone</p>
                        <div className="flex flex-wrap gap-2">
                          {prompt.dna.instructions.tone.map((tone) => (
                            <Badge key={tone} variant="outline">
                              {tone}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    {prompt.dna.instructions.format && (
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground mb-1">Format</p>
                        <Badge variant="secondary">{prompt.dna.instructions.format}</Badge>
                      </div>
                    )}
                    {prompt.dna.instructions.constraints.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground mb-1">
                          Constraints
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {prompt.dna.instructions.constraints.map((constraint) => (
                            <Badge key={constraint} variant="outline">
                              {constraint}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card>
                <CardContent className="pt-12 pb-12">
                  <div className="text-center">
                    <Code2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                    <p className="text-sm text-muted-foreground">DNA not extracted yet</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="lineage" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <LinkIcon className="h-5 w-5" />
                  Evolution Lineage
                </CardTitle>
                <CardDescription>
                  Parent-child relationships showing prompt evolution
                </CardDescription>
              </CardHeader>
              <CardContent>
                {lineage.length <= 1 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <LinkIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p className="text-sm">No lineage links found</p>
                    <p className="text-xs mt-2">
                      This prompt has no ancestors or descendants
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {ancestors.length > 0 && (
                      <div>
                        <h3 className="text-sm font-semibold mb-4 text-muted-foreground uppercase tracking-wide">
                          Ancestors ({ancestors.length})
                        </h3>
                        <div className="space-y-3">
                          {ancestors.map((link, idx) => (
                            <Link key={idx} href={`/prompts/${link.prompt_id}`}>
                              <Card className="hover:bg-muted/50 transition-colors cursor-pointer border-l-4 border-l-blue-500">
                                <CardContent className="pt-4">
                                  <div className="flex items-center justify-between">
                                    <div className="flex-1">
                                      <p className="text-xs font-mono text-muted-foreground mb-2">
                                        {link.prompt_id.slice(0, 16)}...
                                      </p>
                                      <div className="flex items-center gap-2">
                                        <Badge variant="outline">{link.mutation_type}</Badge>
                                        <span className="text-xs text-muted-foreground">
                                          Confidence: {(link.confidence * 100).toFixed(1)}%
                                        </span>
                                      </div>
                                    </div>
                                    <ArrowLeft className="h-4 w-4 text-muted-foreground" />
                                  </div>
                                </CardContent>
                              </Card>
                            </Link>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="py-4 border-y">
                      <div className="flex items-center justify-center">
                        <Card className="border-2 border-blue-500 bg-blue-50">
                          <CardContent className="pt-4">
                            <p className="text-sm font-semibold mb-1">Current Prompt</p>
                            <p className="text-xs font-mono text-muted-foreground">
                              {prompt.prompt_id.slice(0, 16)}...
                            </p>
                          </CardContent>
                        </Card>
                      </div>
                    </div>

                    {descendants.length > 0 && (
                      <div>
                        <h3 className="text-sm font-semibold mb-4 text-muted-foreground uppercase tracking-wide">
                          Descendants ({descendants.length})
                        </h3>
                        <div className="space-y-3">
                          {descendants.map((link, idx) => (
                            <Link key={idx} href={`/prompts/${link.prompt_id}`}>
                              <Card className="hover:bg-muted/50 transition-colors cursor-pointer border-l-4 border-l-green-500">
                                <CardContent className="pt-4">
                                  <div className="flex items-center justify-between">
                                    <div className="flex-1">
                                      <p className="text-xs font-mono text-muted-foreground mb-2">
                                        {link.prompt_id.slice(0, 16)}...
                                      </p>
                                      <div className="flex items-center gap-2">
                                        <Badge variant="outline">{link.mutation_type}</Badge>
                                        <span className="text-xs text-muted-foreground">
                                          Confidence: {(link.confidence * 100).toFixed(1)}%
                                        </span>
                                      </div>
                                    </div>
                                    <ArrowLeft className="h-4 w-4 text-muted-foreground rotate-180" />
                                  </div>
                                </CardContent>
                              </Card>
                            </Link>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
