import config from '@/config'

const PORTKEY_GATEWAY_URL = config.portkey.gatewayUrl

const getPortkeyHeaders = () => {
  if (typeof window === 'undefined') {
    throw new Error('Portkey client can only be used on the client side')
  }

  const portkeyApiKey = process.env.NEXT_PUBLIC_PORTKEY_API_KEY

  if (!portkeyApiKey) {
    throw new Error('NEXT_PUBLIC_PORTKEY_API_KEY is not set')
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'x-portkey-api-key': portkeyApiKey,
    'x-portkey-provider': config.portkey.defaultProvider,
    'x-portkey-debug': 'true',
  }

  const virtualKey = process.env.NEXT_PUBLIC_PORTKEY_VIRTUAL_KEY
  if (virtualKey) {
    headers['x-portkey-virtual-key'] = virtualKey
  }

  const configId = process.env.NEXT_PUBLIC_PORTKEY_CONFIG_ID
  if (configId) {
    headers['x-portkey-config'] = configId
  }

  return headers
}

const MOCK_MODE = config.portkey.mockMode

const generateMockResponse = (prompt: string) => {
  return config.mockResponses[Math.floor(Math.random() * config.mockResponses.length)]
}

export interface GenerateLogResult {
  success: boolean
  content?: string
  error?: string
  tokens?: number
  promptTokens?: number
  completionTokens?: number
  thinkingTokens?: number
  cost?: number
  latency?: number
  cache?: 'disabled' | 'miss' | 'hit' | 'refreshed' | 'semantic_hit'
  retry?: 'not_triggered' | { success: boolean; tries: number }
  fallback?: 'disabled' | 'active'
  loadbalance?: 'disabled' | 'active'
  isMock: boolean
}

export const generateLog = async (
  prompt: string,
  model: string = config.portkey.defaultModel,
  useMock: boolean = false
): Promise<GenerateLogResult> => {
  const startTime = Date.now()

  if (useMock || MOCK_MODE) {
    await new Promise((resolve) => setTimeout(resolve, 20 + Math.random() * 30))
    const mockResponse = generateMockResponse(prompt)
    const estimatedTokens = Math.floor(prompt.length / 4) + Math.floor(mockResponse.length / 4)
    const latency = Date.now() - startTime

    const mockCache = Math.random() > 0.7 ? 'hit' : 'miss'
    const mockRetry = Math.random() > 0.9 ? { success: true, tries: 2 } : 'not_triggered'

    return {
      success: true,
      content: mockResponse,
      tokens: estimatedTokens,
      promptTokens: Math.floor(prompt.length / 4),
      completionTokens: Math.floor(mockResponse.length / 4),
      thinkingTokens: 0,
      cost: estimatedTokens * 0.000002,
      latency,
      cache: mockCache,
      retry: mockRetry,
      fallback: 'disabled' as const,
      loadbalance: 'disabled' as const,
      isMock: true,
    }
  }

  const fastModel = config.portkey.fastModel
  const headers = getPortkeyHeaders()

  console.log('[Portkey] Request Details:', {
    url: `${PORTKEY_GATEWAY_URL}/chat/completions`,
    provider: headers['x-portkey-provider'],
    model: fastModel,
    promptLength: prompt.length,
    hasApiKey: !!headers['x-portkey-api-key'],
    hasVirtualKey: !!headers['x-portkey-virtual-key'],
    hasConfig: !!headers['x-portkey-config'],
  })

  try {
    const requestBody = {
      model: fastModel,
      messages: [
        {
          role: 'user' as const,
          content: prompt,
        },
      ],
      max_tokens: 30,
      temperature: 0.5,
    }

    console.log('[Portkey] Sending request:', {
      model: fastModel,
      messagesCount: requestBody.messages.length,
      maxTokens: requestBody.max_tokens,
      promptLength: prompt.length,
    })

    const response = await fetch(`${PORTKEY_GATEWAY_URL}/chat/completions`, {
      method: 'POST',
      headers,
      body: JSON.stringify(requestBody),
    })

    const latency = Date.now() - startTime

    console.log('[Portkey] Response Status:', {
      status: response.status,
      statusText: response.statusText,
      latency: `${latency}ms`,
      headers: Object.fromEntries(response.headers.entries()),
    })

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`
      try {
        const errorData = await response.json()
        console.error('[Portkey] Error Response:', errorData)
        if (errorData.error) {
          errorMessage = errorData.error.message || errorData.error || errorMessage
        } else if (errorData.message) {
          errorMessage = errorData.message
        }
      } catch {
        const text = await response.text().catch(() => '')
        if (text) {
          try {
            const parsed = JSON.parse(text)
            errorMessage = parsed.error?.message || parsed.message || text
          } catch {
            errorMessage = text || errorMessage
          }
        }
      }
      throw new Error(errorMessage)
    }

    const data = await response.json()
    console.log('[Portkey] Success Response:', {
      model: data.model,
      hasChoices: !!data.choices,
      choicesLength: data.choices?.length,
      usage: data.usage,
      serviceTier: data.service_tier,
    })

    const content = data.choices?.[0]?.message?.content || ''
    const usage = data.usage

    if (!content) {
      console.warn('[Portkey] No content in response:', data)
    }

    const estimatedCost = (usage?.total_tokens || 0) * 0.000002

    const cacheStatus = response.headers.get('x-portkey-cache') || response.headers.get('x-portkey-cache-status') || 'miss'
    const retryCount = response.headers.get('x-portkey-retry-count') || response.headers.get('x-portkey-retries')
    const fallbackActive = response.headers.get('x-portkey-fallback-active') === 'true' || response.headers.get('x-portkey-fallback') === 'active'
    const loadbalanceActive = response.headers.get('x-portkey-loadbalance-active') === 'true' || response.headers.get('x-portkey-loadbalance') === 'active'

    let retry: 'not_triggered' | { success: boolean; tries: number } = 'not_triggered'
    if (retryCount && parseInt(retryCount) > 0) {
      retry = { success: true, tries: parseInt(retryCount) }
    }

    console.log('[Portkey] Log Metadata:', {
      tokens: usage?.total_tokens,
      cost: estimatedCost,
      cache: cacheStatus,
      retry,
      fallback: fallbackActive ? 'active' : 'disabled',
      loadbalance: loadbalanceActive ? 'active' : 'disabled',
    })

    console.log('[Portkey] ✅ Log sent to Portkey dashboard')

    return {
      success: true,
      content,
      tokens: usage?.total_tokens,
      promptTokens: usage?.prompt_tokens,
      completionTokens: usage?.completion_tokens,
      thinkingTokens: usage?.thinking_tokens || 0,
      cost: estimatedCost,
      latency,
      cache: (cacheStatus.toLowerCase() as any) || 'miss',
      retry,
      fallback: fallbackActive ? 'active' : 'disabled',
      loadbalance: loadbalanceActive ? 'active' : 'disabled',
      isMock: false,
    }
  } catch (error: any) {
    console.error('[Portkey] Request Failed:', {
      error: error.message,
      stack: error.stack,
    })
    return {
      success: false,
      error: error.message || 'Unknown error',
      isMock: false,
    }
  }
}

export const generateBatchLogs = async (
  prompts: string[],
  model: string = config.portkey.defaultModel,
  delay: number = 1000,
  useMock: boolean = false
) => {
  const results = []

  for (const prompt of prompts) {
    const result = await generateLog(prompt, model, useMock)
    results.push(result)
    if (delay > 0) {
      await new Promise((resolve) => setTimeout(resolve, delay))
    }
  }

  return results
}

// Prompt categories for LLM-based generation
const PROMPT_CATEGORIES = [
  'summarization',
  'code generation',
  'translation',
  'explanation',
  'creative writing',
  'data analysis',
  'email drafting',
  'question answering',
  'debugging',
  'format conversion',
  'brainstorming',
  'comparison',
  'recommendation',
  'research',
  'review writing',
]

// Generate a random prompt using LLM
export const generateRandomPrompt = async (useMock: boolean = false): Promise<string> => {
  const category = PROMPT_CATEGORIES[Math.floor(Math.random() * PROMPT_CATEGORIES.length)]

  if (useMock) {
    // Mock mode: generate from predefined dynamic templates
    const mockPrompts: Record<string, string[]> = {
      summarization: [
        'Summarize the quarterly earnings report',
        'Give me a TL;DR of the meeting notes',
        'Summarize this research paper abstract',
        'Condense this blog post into 3 key points',
        'Brief summary of the product launch announcement',
      ],
      'code generation': [
        'Write a React hook for infinite scroll',
        'Create a Python decorator for rate limiting',
        'Implement a debounce function in TypeScript',
        'Write a SQL query for user segmentation',
        'Generate a REST API endpoint for user auth',
      ],
      translation: [
        'Translate this marketing copy to Spanish',
        'Convert this technical doc to French',
        'Translate the error messages to German',
        'Help translate UI text to Japanese',
        'Translate the privacy policy to Portuguese',
      ],
      explanation: [
        'Explain microservices architecture simply',
        'What is event-driven programming?',
        'Explain OAuth 2.0 to a beginner',
        'How does garbage collection work?',
        'Describe containerization in simple terms',
      ],
      'creative writing': [
        'Write a product tagline for a fitness app',
        'Create a social media post about AI',
        'Write copy for a landing page hero section',
        'Generate a newsletter intro paragraph',
        'Write a press release headline',
      ],
      'data analysis': [
        'Analyze the website traffic patterns',
        'Find correlations in customer churn data',
        'Identify seasonality in sales data',
        'Summarize the A/B test results',
        'Extract insights from survey responses',
      ],
      'email drafting': [
        'Write a cold outreach email for sales',
        'Draft a project status update email',
        'Compose a partnership proposal email',
        'Write a customer feedback request email',
        'Create an event invitation email',
      ],
      'question answering': [
        'What are the benefits of TypeScript over JavaScript?',
        'How does caching improve API performance?',
        'What is the difference between SQL and NoSQL?',
        'When should I use WebSockets vs REST?',
        'What are best practices for API versioning?',
      ],
      debugging: [
        'Why am I getting CORS errors in my React app?',
        'Debug this Promise rejection issue',
        'Fix the race condition in this async code',
        'Help troubleshoot the memory leak',
        'Why is my GraphQL query returning null?',
      ],
      'format conversion': [
        'Convert this XML configuration to JSON',
        'Transform the API response to TypeScript types',
        'Convert these requirements to user stories',
        'Transform the data model to Prisma schema',
        'Convert the SQL query to MongoDB aggregation',
      ],
      brainstorming: [
        'Generate 5 feature ideas for a productivity app',
        'Brainstorm names for a developer tool',
        'Suggest improvements for the onboarding flow',
        'List ways to improve API documentation',
        'Ideas for reducing deployment time',
      ],
      comparison: [
        'Compare React vs Vue for a new project',
        'PostgreSQL vs MongoDB for this use case',
        'REST vs GraphQL for our API',
        'Kubernetes vs Docker Swarm comparison',
        'Compare serverless vs containers',
      ],
      recommendation: [
        'Recommend a state management library for React',
        'Suggest the best testing framework for Node.js',
        'What CI/CD tool should we use?',
        'Recommend a monitoring solution for microservices',
        'Best practices for database indexing',
      ],
      research: [
        'Research current trends in AI observability',
        'Find information about vector databases',
        'Research best practices for prompt engineering',
        'Look up LLM cost optimization techniques',
        'Research semantic search implementations',
      ],
      'review writing': [
        'Write a code review comment for this PR',
        'Draft a technical design review feedback',
        'Create a security review checklist',
        'Write performance review notes',
        'Generate documentation review comments',
      ],
    }

    const prompts = mockPrompts[category] || mockPrompts['question answering']
    return prompts[Math.floor(Math.random() * prompts.length)]
  }

  // Real mode: Use LLM to generate a prompt
  try {
    const headers = getPortkeyHeaders()
    const systemPrompt = `You are a prompt generator. Generate ONE short, realistic prompt that a user might send to an AI assistant.
The prompt should be in the category: ${category}
Requirements:
- Keep it under 50 words
- Make it specific and actionable
- No meta-commentary, just the prompt itself
- Vary the style and topic`

    const response = await fetch(`${PORTKEY_GATEWAY_URL}/chat/completions`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: `Generate a ${category} prompt:` }
        ],
        max_tokens: 100,
        temperature: 1.0,
      }),
    })

    if (!response.ok) {
      throw new Error('Failed to generate prompt')
    }

    const data = await response.json()
    return data.choices?.[0]?.message?.content?.trim() || 'What is the best approach for this task?'
  } catch (error) {
    console.error('Error generating prompt:', error)
    // Fallback to a generic prompt
    return `Can you help me with ${category}?`
  }
}
