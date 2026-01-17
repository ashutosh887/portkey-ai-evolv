const PORTKEY_GATEWAY_URL = 'https://api.portkey.ai/v1'

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
    'x-portkey-provider': '@openai',
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

const MOCK_MODE = process.env.NEXT_PUBLIC_MOCK_MODE === 'true'

const generateMockResponse = (prompt: string) => {
  const shortResponses = [
    'AI is artificial intelligence.',
    'ML is machine learning.',
    'API is application programming interface.',
    'A prompt is an input instruction.',
    'Caching stores data for faster access.',
    'Observability is monitoring system behavior.',
    'Tokens are text units.',
    'Portkey is an AI gateway.',
    'Embedding is a vector representation.',
    'Clustering groups similar items.',
    'DNA extraction identifies core components.',
    'Lineage tracks evolution history.',
    'Mutation is a change or variation.',
    'Template is a reusable pattern.',
    'Evolution is gradual change over time.',
  ]
  return shortResponses[Math.floor(Math.random() * shortResponses.length)]
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
  model: string = 'gpt-3.5-turbo',
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

  const fastModel = 'gpt-4o-mini'
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
  model: string = 'gpt-3.5-turbo',
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
