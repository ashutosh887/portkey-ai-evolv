'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { api, Family } from '@/lib/api'
import { Users, RefreshCw, Search, AlertCircle } from 'lucide-react'
import Link from 'next/link'

export default function FamiliesPage() {
  const [families, setFamilies] = useState<Family[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const limit = 20

  const loadFamilies = async () => {
    try {
      setError(null)
      const offset = (page - 1) * limit
      const data = await api.families({ limit, offset, sort: 'created_at' })
      setFamilies(data.families)
      setTotal(data.total)
    } catch (err: any) {
      setError(err.message || 'Failed to load families')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFamilies()
  }, [page])

  if (loading && families.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-muted-foreground">Loading families...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold tracking-tight mb-2">Prompt Families</h1>
            <p className="text-muted-foreground">
              {total} {total === 1 ? 'family' : 'families'} found
            </p>
          </div>
          <Button onClick={loadFamilies} variant="outline" size="sm">
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

        {families.length === 0 ? (
          <Card>
            <CardContent className="pt-12 pb-12">
              <div className="text-center">
                <Users className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                <h3 className="text-lg font-semibold mb-2">No families yet</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Process prompts to create families
                </p>
                <Link href="/dashboard">
                  <Button>Go to Dashboard</Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
              {families.map((family) => (
                <Link key={family.family_id} href={`/families/${family.family_id}`}>
                  <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <CardTitle className="text-lg">{family.family_name}</CardTitle>
                        <Badge variant="secondary">{family.member_count}</Badge>
                      </div>
                      <CardDescription className="line-clamp-2 mt-2">
                        {family.description || 'No description available'}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between text-sm text-muted-foreground">
                        <span>ID: {family.family_id.slice(0, 8)}...</span>
                        <span>
                          {new Date(family.created_at).toLocaleDateString()}
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
