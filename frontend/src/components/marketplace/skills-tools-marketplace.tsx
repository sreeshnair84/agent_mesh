'use client'

import { useState, useEffect } from 'react'
import { 
  Search, 
  Filter, 
  Grid, 
  List, 
  Plus, 
  Download,
  Upload,
  Star,
  Users,
  Activity,
  Settings,
  TrendingUp,
  Award,
  CheckCircle,
  AlertCircle,
  Clock,
  Zap,
  Code,
  Database,
  Globe,
  Cpu
} from 'lucide-react'
import Link from 'next/link'

// API Client
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = {
  async get(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`)
    }
    return response.json()
  },
  
  async post(endpoint: string, data: any, options: RequestInit = {}) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`)
    }
    return response.json()
  }
}

interface Skill {
  id: string
  name: string
  description: string
  category: string
  input_types: string[]
  output_types: string[]
  prerequisites: string[]
  examples: Array<{
    input: any
    output: any
    description: string
  }>
  usage_count: number
  success_rate: number
  rating: number
  created_at: string
  updated_at: string
  performance_score: number
}

interface Tool {
  id: string
  name: string
  description: string
  type: 'REST' | 'GraphQL' | 'gRPC' | 'WebSocket' | 'Database' | 'Custom'
  category: string
  capabilities: string[]
  endpoint?: string
  auth_type: 'none' | 'api_key' | 'oauth2' | 'bearer'
  status: 'active' | 'inactive' | 'testing' | 'deprecated'
  total_invocations: number
  successful_invocations: number
  failed_invocations: number
  success_rate?: number
  average_response_time?: number
  rating?: number
  integration_effort?: 'low' | 'medium' | 'high'
  documentation_score?: number
  created_at: string
  updated_at: string
}

interface ToolsResponse {
  tools: Tool[]
  total: number
}

interface ToolCategory {
  name: string
  count: number
}

interface ToolAnalytics {
  total_tools: number
  active_tools: number
  total_invocations: number
  average_success_rate: number
  top_categories: Array<{
    name: string
    usage: number
  }>
}

interface SkillCombination {
  skills: string[]
  combination_name: string
  description: string
  synergy_score: number
  expected_performance: {
    efficiency: number
    accuracy: number
  }
  use_cases: string[]
  prerequisites: string[]
}

interface CapabilityRecommendation {
  capability: string
  missing_skills: string[]
  available_alternatives: string[]
  priority: 'high' | 'medium' | 'low'
  recommendations: string[]
}

const mockSkills: Skill[] = [
  {
    id: '1',
    name: 'natural-language-processing',
    description: 'Advanced text analysis and understanding capabilities',
    category: 'language',
    input_types: ['text', 'document'],
    output_types: ['analysis', 'sentiment', 'entities'],
    prerequisites: ['text-processing'],
    examples: [
      {
        input: { text: 'The customer is unhappy with the service' },
        output: { sentiment: 'negative', entities: ['customer', 'service'] },
        description: 'Sentiment analysis example'
      }
    ],
    usage_count: 1250,
    success_rate: 0.94,
    rating: 4.8,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-20T15:30:00Z',
    performance_score: 0.92
  },
  {
    id: '2',
    name: 'code-generation',
    description: 'Generate high-quality code in multiple programming languages',
    category: 'development',
    input_types: ['requirements', 'specification'],
    output_types: ['code', 'documentation'],
    prerequisites: ['programming-fundamentals'],
    examples: [
      {
        input: { requirement: 'Create a REST API endpoint' },
        output: { code: 'def create_endpoint()...', documentation: 'API docs' },
        description: 'REST API generation'
      }
    ],
    usage_count: 890,
    success_rate: 0.87,
    rating: 4.6,
    created_at: '2024-01-10T09:00:00Z',
    updated_at: '2024-01-19T14:20:00Z',
    performance_score: 0.85
  },
  {
    id: '3',
    name: 'data-visualization',
    description: 'Create compelling visualizations from data',
    category: 'data',
    input_types: ['data', 'metrics'],
    output_types: ['charts', 'graphs', 'dashboards'],
    prerequisites: ['data-analysis'],
    examples: [
      {
        input: { data: [1, 2, 3, 4, 5] },
        output: { chart: 'line_chart.png' },
        description: 'Simple line chart'
      }
    ],
    usage_count: 567,
    success_rate: 0.91,
    rating: 4.7,
    created_at: '2024-01-12T11:00:00Z',
    updated_at: '2024-01-18T16:45:00Z',
    performance_score: 0.88
  }
]

const mockTools: Tool[] = [
  {
    id: '1',
    name: 'OpenAI GPT API',
    description: 'Access to OpenAI language models for text generation',
    type: 'REST',
    category: 'ai',
    capabilities: ['text-generation', 'completion', 'chat'],
    endpoint: 'https://api.openai.com/v1',
    auth_type: 'api_key',
    status: 'active',
    total_invocations: 5000,
    successful_invocations: 4900,
    failed_invocations: 100,
    success_rate: 0.98,
    average_response_time: 1200,
    integration_effort: 'low',
    documentation_score: 0.95,
    rating: 4.8,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-20T12:00:00Z'
  },
  {
    id: '2',
    name: 'PostgreSQL Database',
    description: 'Relational database for structured data storage',
    type: 'Database',
    category: 'database',
    capabilities: ['data-storage', 'querying', 'transactions'],
    auth_type: 'none',
    status: 'active',
    total_invocations: 2500,
    successful_invocations: 2475,
    failed_invocations: 25,
    success_rate: 0.99,
    average_response_time: 50,
    integration_effort: 'medium',
    documentation_score: 0.90,
    rating: 4.6,
    created_at: '2024-01-05T10:00:00Z',
    updated_at: '2024-01-19T09:30:00Z'
  },
  {
    id: '3',
    name: 'Stripe Payment API',
    description: 'Process payments and handle financial transactions',
    type: 'REST',
    category: 'payment',
    capabilities: ['payments', 'subscriptions', 'webhooks'],
    endpoint: 'https://api.stripe.com',
    auth_type: 'api_key',
    status: 'active',
    total_invocations: 1800,
    successful_invocations: 1764,
    failed_invocations: 36,
    success_rate: 0.98,
    average_response_time: 800,
    integration_effort: 'low',
    documentation_score: 0.98,
    rating: 4.9,
    created_at: '2024-01-08T14:00:00Z',
    updated_at: '2024-01-18T11:15:00Z'
  }
]

const mockSkillCombinations: SkillCombination[] = [
  {
    skills: ['natural-language-processing', 'data-visualization'],
    combination_name: 'Text Analytics Dashboard',
    description: 'Combine NLP with visualization for text analytics',
    synergy_score: 0.89,
    expected_performance: { efficiency: 0.85, accuracy: 0.92 },
    use_cases: ['Customer feedback analysis', 'Social media monitoring'],
    prerequisites: ['text-processing', 'data-analysis']
  },
  {
    skills: ['code-generation', 'natural-language-processing'],
    combination_name: 'Code Assistant',
    description: 'Natural language to code generation',
    synergy_score: 0.82,
    expected_performance: { efficiency: 0.78, accuracy: 0.85 },
    use_cases: ['Development assistance', 'Code documentation'],
    prerequisites: ['programming-fundamentals']
  }
]

export function SkillsToolsMarketplace() {
  const [activeTab, setActiveTab] = useState<'skills' | 'tools' | 'combinations' | 'recommendations'>('skills')
  const [skills, setSkills] = useState<Skill[]>([])
  const [tools, setTools] = useState<Tool[]>([])
  const [combinations, setCombinations] = useState<SkillCombination[]>(mockSkillCombinations)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [toolCategories, setToolCategories] = useState<ToolCategory[]>([])
  const [analytics, setAnalytics] = useState<ToolAnalytics | null>(null)

  // API Functions
  const fetchSkills = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.get('/api/v1/skills/')
      setSkills(response || mockSkills)
    } catch (err) {
      console.error('Error fetching skills:', err)
      setError('Failed to fetch skills')
      setSkills(mockSkills) // Fallback to mock data
    } finally {
      setLoading(false)
    }
  }

  const fetchTools = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.get('/api/v1/tools/')
      setTools(response || mockTools)
    } catch (err) {
      console.error('Error fetching tools:', err)
      setError('Failed to fetch tools')
      setTools(mockTools) // Fallback to mock data
    } finally {
      setLoading(false)
    }
  }

  const fetchToolCategories = async () => {
    try {
      const response = await apiClient.get('/api/v1/tools/categories')
      setToolCategories(response || [])
    } catch (err) {
      console.error('Error fetching tool categories:', err)
      setToolCategories([])
    }
  }

  const fetchAnalytics = async () => {
    try {
      const response = await apiClient.get('/api/v1/tools/analytics/usage')
      setAnalytics(response)
    } catch (err) {
      console.error('Error fetching analytics:', err)
      setAnalytics(null)
    }
  }

  const searchSkills = async (query: string) => {
    if (!query.trim()) {
      fetchSkills()
      return
    }
    
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.get(`/api/v1/skills/search?query=${encodeURIComponent(query)}`)
      setSkills(response?.skills || [])
    } catch (err) {
      console.error('Error searching skills:', err)
      setError('Failed to search skills')
    } finally {
      setLoading(false)
    }
  }

  const searchTools = async (query: string) => {
    if (!query.trim()) {
      fetchTools()
      return
    }
    
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.get(`/api/v1/tools/?query=${encodeURIComponent(query)}`)
      setTools(response || [])
    } catch (err) {
      console.error('Error searching tools:', err)
      setError('Failed to search tools')
    } finally {
      setLoading(false)
    }
  }

  // Effect to fetch data on mount and tab change
  useEffect(() => {
    if (activeTab === 'skills') {
      fetchSkills()
    } else if (activeTab === 'tools') {
      fetchTools()
      fetchToolCategories()
      fetchAnalytics()
    }
  }, [activeTab])

  // Effect to handle search
  useEffect(() => {
    const delayedSearch = setTimeout(() => {
      if (activeTab === 'skills') {
        searchSkills(searchQuery)
      } else if (activeTab === 'tools') {
        searchTools(searchQuery)
      }
    }, 300) // Debounce search

    return () => clearTimeout(delayedSearch)
  }, [searchQuery, activeTab])

  const skillCategories = Array.from(new Set(skills.map(skill => skill.category)))
  const toolCategoryNames = toolCategories.map(cat => cat.name)

  // Tool interaction functions
  const testTool = async (toolId: string) => {
    try {
      setLoading(true)
      await apiClient.post(`/api/v1/tools/${toolId}/test`, {})
      // Show success message or refresh data
      fetchTools()
    } catch (err) {
      console.error('Error testing tool:', err)
      setError('Failed to test tool')
    } finally {
      setLoading(false)
    }
  }

  const testConnection = async (toolId: string) => {
    try {
      setLoading(true)
      const result = await apiClient.post(`/api/v1/tools/${toolId}/connection-test`, {})
      // Show connection test result
      alert(`Connection test: ${result.status} (${result.latency}ms)`)
    } catch (err) {
      console.error('Error testing connection:', err)
      setError('Failed to test connection')
    } finally {
      setLoading(false)
    }
  }

  const getToolMetrics = async (toolId: string) => {
    try {
      const metrics = await apiClient.get(`/api/v1/tools/${toolId}/metrics`)
      // Show metrics modal or navigate to metrics page
      console.log('Tool metrics:', metrics)
    } catch (err) {
      console.error('Error fetching tool metrics:', err)
      setError('Failed to fetch tool metrics')
    }
  }

  const fetchPopularTools = async () => {
    try {
      setLoading(true)
      const popular = await apiClient.get('/api/v1/tools/marketplace/popular')
      setTools(popular)
      setActiveTab('tools')
    } catch (err) {
      console.error('Error fetching popular tools:', err)
      setError('Failed to fetch popular tools')
    } finally {
      setLoading(false)
    }
  }

  const fetchTrendingTools = async () => {
    try {
      setLoading(true)
      const trending = await apiClient.get('/api/v1/tools/marketplace/trending')
      setTools(trending)
      setActiveTab('tools')
    } catch (err) {
      console.error('Error fetching trending tools:', err)
      setError('Failed to fetch trending tools')
    } finally {
      setLoading(false)
    }
  }

  const getCustomRecommendations = async () => {
    try {
      setLoading(true)
      const requirements = {
        category: selectedCategory !== 'all' ? selectedCategory : undefined,
        search_query: searchQuery || undefined
      }
      const recommendations = await apiClient.post('/api/v1/tools/recommend', requirements)
      setTools(recommendations)
      setActiveTab('tools')
    } catch (err) {
      console.error('Error fetching recommendations:', err)
      setError('Failed to fetch recommendations')
    } finally {
      setLoading(false)
    }
  }

  const getSuggestedCombinations = async () => {
    try {
      setLoading(true)
      const combinations = await apiClient.get('/api/v1/skills/combinations/suggestions')
      setCombinations(combinations)
      setActiveTab('combinations')
    } catch (err) {
      console.error('Error fetching skill combinations:', err)
      setError('Failed to fetch skill combinations')
    } finally {
      setLoading(false)
    }
  }

  const filteredSkills = skills.filter(skill => {
    const matchesSearch = skill.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         skill.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || skill.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const filteredTools = tools.filter(tool => {
    const matchesSearch = tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         tool.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || tool.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'inactive': return 'bg-gray-100 text-gray-800'
      case 'testing': return 'bg-yellow-100 text-yellow-800'
      case 'deprecated': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'REST': return <Globe className="h-4 w-4" />
      case 'GraphQL': return <Code className="h-4 w-4" />
      case 'Database': return <Database className="h-4 w-4" />
      case 'Custom': return <Cpu className="h-4 w-4" />
      default: return <Zap className="h-4 w-4" />
    }
  }

  const getIntegrationEffortColor = (effort: string) => {
    switch (effort) {
      case 'low': return 'bg-green-100 text-green-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'high': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const SkillCard = ({ skill }: { skill: Skill }) => (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">{skill.name}</h3>
          <p className="text-gray-600 text-sm mb-3">{skill.description}</p>
          <div className="flex items-center space-x-2 mb-3">
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
              {skill.category}
            </span>
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {skill.input_types.join(', ')}
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-1">
          <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
          <span className="text-sm text-gray-600">{skill.rating}</span>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">{skill.usage_count}</div>
          <div className="text-xs text-gray-500">Uses</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{(skill.success_rate * 100).toFixed(1)}%</div>
          <div className="text-xs text-gray-500">Success Rate</div>
        </div>
      </div>

      <div className="mb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm text-gray-600">Performance</span>
          <span className="text-sm font-medium text-gray-900">{(skill.performance_score * 100).toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-purple-600 h-2 rounded-full" 
            style={{ width: `${skill.performance_score * 100}%` }}
          />
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex space-x-2">
          <button className="btn-primary text-sm">
            <Download className="h-4 w-4 mr-1" />
            Install
          </button>
          <button className="btn-secondary text-sm">
            <Activity className="h-4 w-4 mr-1" />
            Analytics
          </button>
        </div>
        <div className="flex items-center space-x-2">
          <button className="text-gray-400 hover:text-gray-600">
            <Star className="h-4 w-4" />
          </button>
          <button className="text-gray-400 hover:text-gray-600">
            <Settings className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )

  const ToolCard = ({ tool }: { tool: Tool }) => (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            {getTypeIcon(tool.type)}
            <h3 className="text-lg font-semibold text-gray-900">{tool.name}</h3>
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(tool.status)}`}>
              {tool.status}
            </span>
          </div>
          <p className="text-gray-600 text-sm mb-3">{tool.description}</p>
          <div className="flex flex-wrap gap-1 mb-3">
            {tool.capabilities.map(capability => (
              <span key={capability} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {capability}
              </span>
            ))}
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <div className="text-lg font-bold text-gray-900">{tool.total_invocations}</div>
          <div className="text-xs text-gray-500">Invocations</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-green-600">{((tool.success_rate || 0) * 100).toFixed(1)}%</div>
          <div className="text-xs text-gray-500">Success</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-blue-600">{tool.average_response_time || 0}ms</div>
          <div className="text-xs text-gray-500">Response</div>
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Integration:</span>
          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getIntegrationEffortColor(tool.integration_effort || 'medium')}`}>
            {tool.integration_effort || 'medium'}
          </span>
        </div>
        <div className="flex items-center space-x-1">
          <CheckCircle className="h-4 w-4 text-green-500" />
          <span className="text-sm text-gray-600">Docs: {((tool.documentation_score || 0) * 100).toFixed(0)}%</span>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex space-x-2">
          <button 
            onClick={() => testConnection(tool.id)}
            disabled={loading}
            className="btn-primary text-sm disabled:opacity-50"
          >
            <Plus className="h-4 w-4 mr-1" />
            Integrate
          </button>
          <button 
            onClick={() => testTool(tool.id)}
            disabled={loading}
            className="btn-secondary text-sm disabled:opacity-50"
          >
            <Activity className="h-4 w-4 mr-1" />
            Test
          </button>
        </div>
        <div className="flex items-center space-x-2">
          <button 
            onClick={() => getToolMetrics(tool.id)}
            className="text-gray-400 hover:text-gray-600"
          >
            <Star className="h-4 w-4" />
          </button>
          <button className="text-gray-400 hover:text-gray-600">
            <Settings className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )

  const CombinationCard = ({ combination }: { combination: SkillCombination }) => (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">{combination.combination_name}</h3>
          <p className="text-gray-600 text-sm mb-3">{combination.description}</p>
          <div className="flex flex-wrap gap-1 mb-3">
            {combination.skills.map(skill => (
              <span key={skill} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                {skill}
              </span>
            ))}
          </div>
        </div>
        <div className="flex items-center space-x-1">
          <Award className="h-4 w-4 text-yellow-500" />
          <span className="text-sm text-gray-600">{(combination.synergy_score * 100).toFixed(0)}%</span>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="text-center">
          <div className="text-lg font-bold text-blue-600">{(combination.expected_performance.efficiency * 100).toFixed(0)}%</div>
          <div className="text-xs text-gray-500">Efficiency</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-green-600">{(combination.expected_performance.accuracy * 100).toFixed(0)}%</div>
          <div className="text-xs text-gray-500">Accuracy</div>
        </div>
      </div>

      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Use Cases:</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          {combination.use_cases.map((useCase, index) => (
            <li key={index} className="flex items-start">
              <span className="text-purple-500 mr-2">•</span>
              {useCase}
            </li>
          ))}
        </ul>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex space-x-2">
          <button className="btn-primary text-sm">
            <Download className="h-4 w-4 mr-1" />
            Apply
          </button>
          <button className="btn-secondary text-sm">
            <TrendingUp className="h-4 w-4 mr-1" />
            Analyze
          </button>
        </div>
        <div className="flex items-center space-x-2">
          <button className="text-gray-400 hover:text-gray-600">
            <Star className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Skills & Tools Marketplace</h1>
          <p className="text-gray-600">Discover, integrate, and optimize agent capabilities</p>
        </div>
        <div className="flex space-x-2">
          <button className="btn-secondary flex items-center space-x-2">
            <Upload className="h-4 w-4" />
            <span>Import</span>
          </button>
          <button className="btn-primary flex items-center space-x-2">
            <Plus className="h-4 w-4" />
            <span>Create</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'skills', label: 'Skills', count: skills.length },
            { id: 'tools', label: 'Tools', count: tools.length },
            { id: 'combinations', label: 'Combinations', count: combinations.length },
            { id: 'recommendations', label: 'Recommendations', count: 0 }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center space-x-4 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder={`Search ${activeTab}...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input pl-10"
            />
          </div>
          <div className="flex items-center space-x-2">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="all">All Categories</option>
              {(activeTab === 'skills' ? skillCategories : toolCategoryNames).map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-lg ${viewMode === 'grid' ? 'bg-purple-100 text-purple-700' : 'text-gray-400 hover:text-gray-600'}`}
            >
              <Grid className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-lg ${viewMode === 'list' ? 'bg-purple-100 text-purple-700' : 'text-gray-400 hover:text-gray-600'}`}
            >
              <List className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Analytics Dashboard */}
      {activeTab === 'tools' && analytics && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Tools Analytics</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{analytics.total_tools}</div>
              <div className="text-sm text-gray-500">Total Tools</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{analytics.active_tools}</div>
              <div className="text-sm text-gray-500">Active Tools</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{analytics.total_invocations.toLocaleString()}</div>
              <div className="text-sm text-gray-500">Total Invocations</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{(analytics.average_success_rate * 100).toFixed(1)}%</div>
              <div className="text-sm text-gray-500">Avg Success Rate</div>
            </div>
          </div>
          
          {analytics.top_categories.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Top Categories</h4>
              <div className="flex flex-wrap gap-2">
                {analytics.top_categories.map(cat => (
                  <span key={cat.name} className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-purple-100 text-purple-800">
                    {cat.name} ({cat.usage}%)
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-red-700">{error}</span>
          </div>
        </div>
      )}

      {/* Content */}
      <div className={viewMode === 'grid' 
        ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' 
        : 'space-y-4'
      }>
        {activeTab === 'skills' && filteredSkills.map(skill => (
          <SkillCard key={skill.id} skill={skill} />
        ))}
        
        {activeTab === 'tools' && filteredTools.map(tool => (
          <ToolCard key={tool.id} tool={tool} />
        ))}
        
        {activeTab === 'combinations' && combinations.map(combination => (
          <CombinationCard key={combination.combination_name} combination={combination} />
        ))}

        {/* Empty states */}
        {activeTab === 'skills' && filteredSkills.length === 0 && !loading && (
          <div className="col-span-full text-center py-12">
            <Code className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Skills Found</h3>
            <p className="text-gray-600 mb-4">
              {searchQuery ? 'Try adjusting your search criteria' : 'No skills available at the moment'}
            </p>
            {!searchQuery && (
              <button 
                onClick={() => fetchSkills()}
                className="btn-primary"
              >
                Refresh Skills
              </button>
            )}
          </div>
        )}

        {activeTab === 'tools' && filteredTools.length === 0 && !loading && (
          <div className="col-span-full text-center py-12">
            <Database className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Tools Found</h3>
            <p className="text-gray-600 mb-4">
              {searchQuery ? 'Try adjusting your search criteria' : 'No tools available at the moment'}
            </p>
            {!searchQuery && (
              <button 
                onClick={() => fetchTools()}
                className="btn-primary"
              >
                Refresh Tools
              </button>
            )}
          </div>
        )}

        {activeTab === 'combinations' && combinations.length === 0 && !loading && (
          <div className="col-span-full text-center py-12">
            <Award className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Combinations Found</h3>
            <p className="text-gray-600 mb-4">
              Skill combinations will appear here as they become available
            </p>
            <button 
              onClick={() => getSuggestedCombinations()}
              className="btn-primary"
            >
              Generate Combinations
            </button>
          </div>
        )}
        
        {activeTab === 'recommendations' && (
          <div className="col-span-full space-y-6">
            {/* Tool Recommendations */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Tool Recommendations</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-medium text-blue-900">Popular Tools</h4>
                    <p className="text-sm text-blue-700">Based on usage patterns</p>
                  </div>
                  <button 
                    onClick={() => fetchPopularTools()}
                    className="btn-primary text-sm"
                  >
                    View Popular
                  </button>
                </div>
                
                <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-medium text-green-900">Trending Tools</h4>
                    <p className="text-sm text-green-700">Fastest growing tools</p>
                  </div>
                  <button 
                    onClick={() => fetchTrendingTools()}
                    className="btn-primary text-sm"
                  >
                    View Trending
                  </button>
                </div>
                
                <div className="flex items-center justify-between p-4 bg-purple-50 rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-medium text-purple-900">Custom Recommendations</h4>
                    <p className="text-sm text-purple-700">Personalized for your needs</p>
                  </div>
                  <button 
                    onClick={() => getCustomRecommendations()}
                    className="btn-primary text-sm"
                  >
                    Get Recommendations
                  </button>
                </div>
              </div>
            </div>
            
            {/* Skill Combinations */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Skill Combinations</h3>
              <div className="text-center py-8">
                <Award className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h4 className="text-lg font-medium text-gray-900 mb-2">Discover Powerful Combinations</h4>
                <p className="text-gray-600 mb-4">
                  Find skill combinations that work well together to enhance agent capabilities.
                </p>
                <button 
                  onClick={() => getSuggestedCombinations()}
                  className="btn-primary"
                >
                  Explore Combinations
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
        </div>
      )}
    </div>
  )
}
