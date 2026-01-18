'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { api, Prompt } from '@/lib/api'
import { Database, RefreshCw, AlertCircle, Link as LinkIcon } from 'lucide-react'
import Link from 'next/link'
import toast from 'react-hot-toast'
import config from '@/config'

export default function PromptsPage() {
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const limit = config.pagination.listPages.default

  const loadPrompts = useCallback(async () => {
    try {
      setError(null)
      const offset = (page - 1) * limit
      const data = await api.prompts({ limit, offset })
      setPrompts(data.prompts)
      setTotal(data.total)
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load prompts'
      setError(errorMessage)
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [page, limit])

  useEffect(() => {
    loadPrompts()
  }, [loadPrompts])

  if (loading && prompts.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-muted-foreground">Loading prompts...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold tracking-tight mb-2">Prompts</h1>
            <p className="text-muted-foreground">
              {total} {total === 1 ? 'prompt' : 'prompts'} found
            </p>
          </div>
          <Button onClick={loadPrompts} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
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

        {prompts.length === 0 ? (
          <Card>
            <CardContent className="pt-12 pb-12">
              <div className="text-center">
                <Database className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                <h3 className="text-lg font-semibold mb-2">No prompts yet</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Ingest prompts to get started
                </p>
                <Link href="/logs">
                  <Button>Generate Logs</Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        ) : (
          <>
            <div className="space-y-3 mb-6">
              {prompts.map((prompt) => (
                <Link key={prompt.prompt_id} href={`/prompts/${prompt.prompt_id}`}>
                  <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
                    <CardContent className="pt-6">
                      <p className="text-sm mb-3 line-clamp-2">{prompt.original_text}</p>
                      <div className="flex items-center gap-2 flex-wrap">
                        {prompt.family_id && (
                          <Badge variant="secondary">
                            Family
                          </Badge>
                        )}
                        {prompt.lineage?.has_lineage && (
                          <Badge variant="outline">
                            <LinkIcon className="h-3 w-3 mr-1" />
                            Lineage ({prompt.lineage.total_links} links)
                          </Badge>
                        )}
                        {(prompt.dna?.variables?.detected?.length ?? 0) > 0 && (
                          <Badge variant="outline">
                            {prompt.dna?.variables?.detected?.length} variables
                          </Badge>
                        )}
                        <span className="text-xs text-muted-foreground ml-auto">
                          {new Date(prompt.created_at).toLocaleString()}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>

            <div className="flex items-center justify-center gap-4">
              <Button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                variant="outline"
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {Math.ceil(total / limit)}
              </span>
              <Button
                onClick={() => setPage((p) => p + 1)}
                disabled={page * limit >= total}
                variant="outline"
              >
                Next
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
