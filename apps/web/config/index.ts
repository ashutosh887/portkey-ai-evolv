export default {
  appName: 'Evolv',
  appDescription: 'Your prompts, but smarter every week',
  appTagline: 'Extract DNA from prompts, track mutations, understand lineage',
  appFullDescription: 'Extract DNA from prompts, track mutations, understand lineage. Transform prompt sprawl into organized, versioned templates.',
  
  metadata: {
    title: 'Evolv - Your prompts, but smarter every week',
    description: 'Extract DNA from prompts, track mutations, understand lineage',
  },
  
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  
  portkey: {
    gatewayUrl: 'https://api.portkey.ai/v1',
    defaultModel: 'gpt-4o-mini',
    fastModel: 'gpt-4o-mini',
    models: [
      { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
      { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
    ],
    defaultProvider: '@openai',
    mockMode: process.env.NEXT_PUBLIC_MOCK_MODE === 'true',
  },
  
  pagination: {
    dashboard: {
      recentFamilies: 5,
      recentPrompts: 5,
    },
    listPages: {
      default: 20,
      max: 100,
    },
  },
  
  processing: {
    batchSize: 100,
    autoRefreshInterval: 30000,
  },
  
  logs: {
    maxDisplayed: 50,
    maxAutoGenerationRate: 30,
    defaultAutoGenerationRate: 2,
  },
  
  samplePrompts: [
    'What is AI?',
    'Explain ML briefly',
    'Define API',
    'What is a prompt?',
    'How does caching work?',
    'What is observability?',
    'Explain tokens',
    'What is Portkey?',
    'Define embedding',
    'What is clustering?',
    'Explain DNA extraction',
    'What is lineage?',
    'Define mutation',
    'What is a template?',
    'Explain evolution',
    'What is a family?',
    'Define similarity',
    'What is drift?',
    'Explain tracking',
    'What is analysis?',
  ],
  
  mockResponses: [
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
    'A template is a reusable pattern.',
    'Evolution is gradual change over time.',
    'A family is a group of related items.',
    'Similarity measures how alike things are.',
    'Drift is gradual deviation from original.',
    'Tracking monitors changes and updates.',
    'Analysis examines data for insights.',
  ],
  
  features: {
    promptGenome: {
      title: 'Prompt Genome',
      description: 'Extract DNA, track mutations, understand lineage',
      items: [
        'Structural parsing',
        'Variable detection',
        'Instruction extraction',
        'Semantic embeddings',
      ],
    },
    realtimeAnalysis: {
      title: 'Real-time Analysis',
      description: 'Continuous processing and family detection',
      items: [
        'Automatic clustering',
        'Family detection',
        'Template synthesis',
        'Confidence scoring',
      ],
    },
    evolutionTracking: {
      title: 'Evolution Tracking',
      description: 'Monitor prompt changes and drift detection',
      items: [
        'Mutation detection',
        'Drift alerts',
        'Lineage graphs',
        'Version control',
      ],
    },
  },
  
  navLinks: [
    { href: '/dashboard', label: 'Dashboard' },
    { href: '/families', label: 'Families' },
    { href: '/prompts', label: 'Prompts' },
    { href: '/logs', label: 'Logs' },
  ],
}
