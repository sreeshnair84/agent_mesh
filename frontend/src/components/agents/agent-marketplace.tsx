'use client'

import { useState } from 'react'
import { 
  Search, 
  Filter, 
  Grid, 
  List, 
  Plus, 
  Eye, 
  Edit, 
  Trash2, 
  Play,
  Heart,
  Star,
  Users,
  Activity
} from 'lucide-react'
import Link from 'next/link'

interface Agent {
  id: string
  name: string
  description: string
  tags: string[]
  owner: string
  type: 'template' | 'custom'
  status: 'active' | 'inactive' | 'deploying' | 'error'
  healthStatus: 'healthy' | 'degraded' | 'unhealthy'
  created: Date
  lastUsed: Date
  usageCount: number
  rating: number
  favorites: number
}

const mockAgents: Agent[] = [
  {
    id: '1',
    name: 'Customer Support Agent',
    description: 'Handles customer inquiries and provides support across multiple channels.',
    tags: ['customer-service', 'support', 'chat'],
    owner: 'John Doe',
    type: 'template',
    status: 'active',
    healthStatus: 'healthy',
    created: new Date('2024-01-15'),
    lastUsed: new Date('2024-01-20'),
    usageCount: 1245,
    rating: 4.8,
    favorites: 89
  },
  {
    id: '2',
    name: 'Data Analyst Assistant',
    description: 'Analyzes data patterns and generates insights from complex datasets.',
    tags: ['data-analysis', 'insights', 'reporting'],
    owner: 'Jane Smith',
    type: 'custom',
    status: 'active',
    healthStatus: 'healthy',
    created: new Date('2024-01-10'),
    lastUsed: new Date('2024-01-19'),
    usageCount: 867,
    rating: 4.6,
    favorites: 67
  },
  {
    id: '3',
    name: 'Code Review Agent',
    description: 'Reviews code for best practices, security issues, and optimization opportunities.',
    tags: ['code-review', 'development', 'security'],
    owner: 'Mike Johnson',
    type: 'template',
    status: 'deploying',
    healthStatus: 'degraded',
    created: new Date('2024-01-08'),
    lastUsed: new Date('2024-01-18'),
    usageCount: 432,
    rating: 4.9,
    favorites: 123
  }
]

export function AgentMarketplace() {
  const [agents, setAgents] = useState<Agent[]>(mockAgents)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [selectedType, setSelectedType] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [sortBy, setSortBy] = useState('created')

  const availableTags = Array.from(new Set(mockAgents.flatMap(agent => agent.tags)))

  const filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         agent.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesTags = selectedTags.length === 0 || selectedTags.some(tag => agent.tags.includes(tag))
    const matchesType = selectedType === 'all' || agent.type === selectedType
    const matchesStatus = selectedStatus === 'all' || agent.status === selectedStatus

    return matchesSearch && matchesTags && matchesType && matchesStatus
  })

  const toggleTag = (tag: string) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    )
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'status-active'
      case 'inactive': return 'status-inactive'
      case 'deploying': return 'status-deploying'
      case 'error': return 'status-error'
      default: return 'status-inactive'
    }
  }

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy': return 'bg-green-500'
      case 'degraded': return 'bg-yellow-500'
      case 'unhealthy': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const AgentCard = ({ agent }: { agent: Agent }) => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
              <span className={`status-badge ${getStatusColor(agent.status)}`}>
                {agent.status}
              </span>
              <div className={`w-2 h-2 rounded-full ${getHealthColor(agent.healthStatus)}`} />
            </div>
            <p className="text-gray-600 text-sm mb-3">{agent.description}</p>
            <div className="flex flex-wrap gap-1 mb-3">
              {agent.tags.map(tag => (
                <span key={tag} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                  {tag}
                </span>
              ))}
            </div>
            <div className="flex items-center justify-between text-sm text-gray-500">
              <span>by {agent.owner}</span>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-1">
                  <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                  <span>{agent.rating}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Heart className="h-4 w-4" />
                  <span>{agent.favorites}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Activity className="h-4 w-4" />
                  <span>{agent.usageCount}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
          <div className="flex space-x-2">
            <button className="btn-primary flex items-center space-x-1">
              <Play className="h-4 w-4" />
              <span>Deploy</span>
            </button>
            <Link href={`/agents/${agent.id}` as any} className="btn-secondary flex items-center space-x-1">
              <Eye className="h-4 w-4" />
              <span>View</span>
            </Link>
          </div>
          <div className="flex space-x-2">
            <button className="p-2 text-gray-400 hover:text-gray-600">
              <Edit className="h-4 w-4" />
            </button>
            <button className="p-2 text-gray-400 hover:text-red-600">
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )

  const AgentListItem = ({ agent }: { agent: Agent }) => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4 flex-1">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-1">
              <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
              <span className={`status-badge ${getStatusColor(agent.status)}`}>
                {agent.status}
              </span>
              <div className={`w-2 h-2 rounded-full ${getHealthColor(agent.healthStatus)}`} />
            </div>
            <p className="text-gray-600 text-sm mb-2">{agent.description}</p>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>by {agent.owner}</span>
              <div className="flex items-center space-x-1">
                <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                <span>{agent.rating}</span>
              </div>
              <div className="flex items-center space-x-1">
                <Users className="h-4 w-4" />
                <span>{agent.usageCount} uses</span>
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button className="btn-primary">Deploy</button>
          <Link href={`/agents/${agent.id}` as any} className="btn-secondary">
            View
          </Link>
        </div>
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agent Marketplace</h1>
          <p className="text-gray-600">Discover and deploy intelligent agents</p>
        </div>
        <Link href={"/agents/create" as any} className="btn-primary flex items-center space-x-2">
          <Plus className="h-4 w-4" />
          <span>Create Agent</span>
        </Link>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center space-x-4 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search agents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input pl-10"
            />
          </div>
          <div className="flex items-center space-x-2">
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

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Type:</span>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="all">All Types</option>
              <option value="template">Template</option>
              <option value="custom">Custom</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Status:</span>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="deploying">Deploying</option>
              <option value="error">Error</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="created">Created Date</option>
              <option value="name">Name</option>
              <option value="rating">Rating</option>
              <option value="usage">Usage Count</option>
            </select>
          </div>
        </div>

        {/* Tags */}
        <div className="mt-4">
          <span className="text-sm font-medium text-gray-700 mb-2 block">Tags:</span>
          <div className="flex flex-wrap gap-2">
            {availableTags.map(tag => (
              <button
                key={tag}
                onClick={() => toggleTag(tag)}
                className={`filter-chip ${selectedTags.includes(tag) ? 'active' : ''}`}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-700">
          {filteredAgents.length} agent{filteredAgents.length !== 1 ? 's' : ''} found
        </p>
      </div>

      {/* Agent Grid/List */}
      <div className={viewMode === 'grid' 
        ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' 
        : 'space-y-4'
      }>
        {filteredAgents.map(agent => viewMode === 'grid' 
          ? <AgentCard key={agent.id} agent={agent} />
          : <AgentListItem key={agent.id} agent={agent} />
        )}
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-center space-x-2 mt-8">
        <button className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700">
          Previous
        </button>
        <button className="px-3 py-2 text-sm font-medium bg-purple-600 text-white rounded-md">
          1
        </button>
        <button className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700">
          2
        </button>
        <button className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700">
          3
        </button>
        <button className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700">
          Next
        </button>
      </div>
    </div>
  )
}
