const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Family {
  family_id: string
  family_name: string
  description?: string
  member_count: number
  created_at: string
}

export interface Prompt {
  prompt_id: string
  original_text: string
  normalized_text?: string
  family_id?: string
  created_at: string
  dna?: {
    structure: {
      system_message?: string
      user_message?: string
      total_tokens: number
    }
    variables: {
      detected: string[]
      slots: number
    }
    instructions: {
      tone: string[]
      format?: string
      constraints: string[]
    }
  }
  family?: {
    family_id: string
    family_name: string
  }
  lineage?: {
    has_lineage: boolean
    ancestors: number
    descendants: number
    total_links: number
  }
}

export interface Template {
  template_id: string
  template_text: string
  slots: {
    variables?: string[]
    example_values?: Record<string, string[]>
  }
  template_version: number
  quality_score?: number
  created_at: string
}

export interface Stats {
  prompts: {
    total: number
    pending: number
    processed: number
  }
  families: {
    total: number
    average_size: number
  }
  templates: {
    extracted: number
  }
  duplicates_detected?: string
  last_ingestion?: string
}

export interface LineageLink {
  prompt_id: string
  mutation_type: string
  confidence: number
  created_at?: string
  direction: 'ancestor' | 'descendant' | 'current'
  path: string[]
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }

  return response.json()
}

export const api = {
  health: () => fetchAPI<{ status: string; service: string }>('/health'),

  stats: () => fetchAPI<Stats>('/stats'),

  families: (params?: { limit?: number; offset?: number; sort?: string }) => {
    const searchParams = new URLSearchParams()
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    if (params?.offset) searchParams.set('offset', params.offset.toString())
    if (params?.sort) searchParams.set('sort', params.sort)
    return fetchAPI<{ families: Family[]; total: number; limit: number; offset: number }>(
      `/families?${searchParams.toString()}`
    )
  },

  family: (familyId: string) =>
    fetchAPI<{
      family_id: string
      family_name: string
      description?: string
      member_count: number
      created_at: string
      members: Prompt[]
      template?: Template
    }>(`/families/${familyId}`),

  prompts: (params?: { limit?: number; offset?: number; family_id?: string }) => {
    const searchParams = new URLSearchParams()
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    if (params?.offset) searchParams.set('offset', params.offset.toString())
    if (params?.family_id) searchParams.set('family_id', params.family_id)
    return fetchAPI<{ prompts: Prompt[]; total: number; limit: number; offset: number }>(
      `/prompts?${searchParams.toString()}`
    )
  },

  prompt: (promptId: string) => fetchAPI<Prompt>(`/prompts/${promptId}`),

  lineage: (promptId: string) =>
    fetchAPI<{
      prompt_id: string
      lineage: LineageLink[]
      total_links: number
    }>(`/prompts/${promptId}/lineage`),

  process: (limit?: number) => {
    const searchParams = new URLSearchParams()
    if (limit) searchParams.set('limit', limit.toString())
    return fetchAPI<{
      status: string
      processed: number
      families_created: number
      families_updated: number
    }>(`/process?${searchParams.toString()}`, { method: 'POST' })
  },

  processStatus: () =>
    fetchAPI<{
      pending_count: number
      last_processed_at?: string
    }>('/process/status'),
}
