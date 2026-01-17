'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { api, Template } from '@/lib/api'
import { Users, FileText, RefreshCw, ArrowLeft, AlertCircle, Link as LinkIcon } from 'lucide-react'
import Link from 'next/link'

export default function FamilyDetailPage() {
  const params = useParams()
  const familyId = params.id as string

  const [family, setFamily] = useState<any>(null)
  const [members, setMembers] = useState<any[]>([])
  const [template, setTemplate] = useState<Template | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadFamily = async () => {
    try {
      setError(null)
      const data = await api.family(familyId)
      setFamily(data)
      setMembers(data.members || [])
      setTemplate(data.template || null)
    } catch (err: any) {
      setError(err.message || 'Failed to load family')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (familyId) {
      loadFamily()
    }
  }, [familyId])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-muted-foreground">Loading family...</p>
        </div>
      </div>
    )
  }

  if (error || !family) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8 max-w-7xl">
          <Link href="/families">
            <Button variant="ghost" className="mb-6">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Families
            </Button>
          </Link>
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-red-800">
                <AlertCircle className="h-5 w-5" />
                <p>{error || 'Family not found'}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <Link href="/families">
          <Button variant="ghost" className="mb-6">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Families
          </Button>
        </Link>

        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold tracking-tight mb-2">{family.family_name}</h1>
              <p className="text-muted-foreground">{family.description || 'No description'}</p>
            </div>
            <Badge variant="secondary" className="text-lg px-4 py-2">
              <Users className="h-4 w-4 mr-2" />
              {family.member_count} members
            </Badge>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Members ({members.length})
              </CardTitle>
              <CardDescription>Prompts in this family</CardDescription>
            </CardHeader>
            <CardContent>
              {members.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <p className="text-sm">No members yet</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {members.map((member) => (
                    <Link key={member.prompt_id} href={`/prompts/${member.prompt_id}`}>
                      <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
                        <CardContent className="pt-4">
                          <p className="text-sm mb-2 line-clamp-2">{member.original_text}</p>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span>ID: {member.prompt_id.slice(0, 8)}...</span>
                            {member.lineage?.has_lineage && (
                              <Badge variant="outline" className="text-xs">
                                <LinkIcon className="h-3 w-3 mr-1" />
                                Lineage
                              </Badge>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Template
              </CardTitle>
              <CardDescription>Canonical template for this family</CardDescription>
            </CardHeader>
            <CardContent>
              {template ? (
                <div className="space-y-4">
                  <div className="p-4 bg-slate-50 rounded-lg border">
                    <p className="text-sm whitespace-pre-wrap">{template.template_text}</p>
                  </div>
                  {template.slots?.variables && template.slots.variables.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase">
                        Variables
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {template.slots.variables.map((varName) => (
                          <Badge key={varName} variant="secondary">
                            {varName}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {template.quality_score !== undefined && (
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground mb-1">
                        Quality Score
                      </p>
                      <p className="text-sm font-semibold">
                        {(template.quality_score * 100).toFixed(1)}%
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No template extracted yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
