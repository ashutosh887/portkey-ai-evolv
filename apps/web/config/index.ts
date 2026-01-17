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
