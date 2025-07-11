'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, Search, Settings, Database, Shield, MessageSquare, Brain, Key } from 'lucide-react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { Badge } from '@/components/ui/Badge'

const masterDataTypes = [
  { id: 'skills', name: 'Skills', icon: Brain, description: 'Agent capabilities and skill definitions' },
  { id: 'constraints', name: 'Constraints', icon: Shield, description: 'Agent behavior constraints and rules' },
  { id: 'prompts', name: 'Prompts', icon: MessageSquare, description: 'System and user prompt templates' },
  { id: 'models', name: 'BYOModel', icon: Database, description: 'Bring Your Own Model configurations' },
  { id: 'secrets', name: 'Env Secrets', icon: Key, description: 'Environment variables and secrets' },
]

export default function MasterDataPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedType, setSelectedType] = useState('skills')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  const { data: masterData, isLoading } = useQuery({
    queryKey: ['master-data', selectedType],
    queryFn: () => {
      switch (selectedType) {
        case 'skills': return api.masterData.skills.list()
        case 'constraints': return api.masterData.constraints.list()
        case 'prompts': return api.masterData.prompts.list()
        case 'secrets': return api.masterData.secrets.list()
        case 'models': return Promise.resolve([]) // TODO: Add models API
        default: return Promise.resolve([])
      }
    },
  })

  const filteredData = masterData?.filter((item: any) => {
    const matchesSearch = item.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.description?.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesSearch
  }) || []

  const selectedTypeConfig = masterDataTypes.find(type => type.id === selectedType)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Master Data</h1>
          <p className="text-gray-600">Manage shared configurations and resources</p>
        </div>
        <Link
          href={`/master-data/${selectedType}/create` as any}
          className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Create {selectedTypeConfig?.name}</span>
        </Link>
      </div>

      {/* Type Selection */}
      <div className="border-b">
        <nav className="flex space-x-8">
          {masterDataTypes.map((type) => (
            <button
              key={type.id}
              onClick={() => setSelectedType(type.id)}
              className={`flex items-center space-x-2 py-3 px-1 border-b-2 font-medium text-sm ${
                selectedType === type.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <type.icon className="w-4 h-4" />
              <span>{type.name}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder={`Search ${selectedTypeConfig?.name.toLowerCase()}...`}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex border border-gray-300 rounded-lg overflow-hidden">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-2 ${viewMode === 'grid' ? 'bg-primary-100 text-primary-600' : 'text-gray-600'}`}
            >
              Grid
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-2 ${viewMode === 'list' ? 'bg-primary-100 text-primary-600' : 'text-gray-600'}`}
            >
              List
            </button>
          </div>
        </div>
      </div>

      {/* Type Description */}
      {selectedTypeConfig && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <selectedTypeConfig.icon className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-medium text-blue-900">{selectedTypeConfig.name}</h3>
          </div>
          <p className="text-blue-700 mt-1">{selectedTypeConfig.description}</p>
        </div>
      )}

      {/* Data Grid/List */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg border p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-full mb-4"></div>
              <div className="flex space-x-2">
                <div className="h-6 bg-gray-200 rounded w-16"></div>
                <div className="h-6 bg-gray-200 rounded w-16"></div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'}>
          {filteredData.map((item: any) => (
            <MasterDataCard key={item.id} item={item} type={selectedType} viewMode={viewMode} />
          ))}
        </div>
      )}

      {filteredData.length === 0 && !isLoading && (
        <div className="text-center py-12">
          {selectedTypeConfig && <selectedTypeConfig.icon className="w-12 h-12 text-gray-400 mx-auto mb-4" />}
          <h3 className="text-lg font-medium text-gray-900 mb-2">No {selectedTypeConfig?.name.toLowerCase()} found</h3>
          <p className="text-gray-600">Create your first {selectedTypeConfig?.name.toLowerCase()} to get started.</p>
        </div>
      )}
    </div>
  )
}

function MasterDataCard({ item, type, viewMode }: { item: any; type: string; viewMode: 'grid' | 'list' }) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'inactive': return 'bg-gray-100 text-gray-800'
      case 'draft': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  if (viewMode === 'list') {
    return (
      <div className="bg-white rounded-lg border p-6 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3">
              <h3 className="text-lg font-semibold text-gray-900">{item.name}</h3>
              <Badge className={getStatusColor(item.status || 'active')}>{item.status || 'active'}</Badge>
              {item.version && <Badge className="bg-blue-100 text-blue-800">v{item.version}</Badge>}
            </div>
            <p className="text-gray-600 mt-1">{item.description}</p>
            <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
              <span>Created: {item.createdAt}</span>
              <span>Updated: {item.updatedAt}</span>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button className="p-2 hover:bg-gray-100 rounded-lg">
              <Settings className="w-4 h-4 text-gray-600" />
            </button>
            <Link
              href={`/master-data/${type}/${item.id}` as any}
              className="text-primary-600 hover:text-primary-700 text-sm font-medium"
            >
              Edit
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">{item.name}</h3>
          <p className="text-gray-600 text-sm">{item.description}</p>
        </div>
        <Badge className={getStatusColor(item.status || 'active')}>{item.status || 'active'}</Badge>
      </div>
      
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          {item.version && <Badge className="bg-blue-100 text-blue-800">v{item.version}</Badge>}
          {item.tags && item.tags.map((tag: string) => (
            <Badge key={tag} className="bg-gray-100 text-gray-800">{tag}</Badge>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-500">Updated {item.updatedAt}</span>
        <div className="flex items-center space-x-2">
          <button className="p-2 hover:bg-gray-100 rounded-lg">
            <Settings className="w-4 h-4 text-gray-600" />
          </button>
          <Link
            href={`/master-data/${type}/${item.id}` as any}
            className="text-primary-600 hover:text-primary-700 text-sm font-medium"
          >
            Edit
          </Link>
        </div>
      </div>
    </div>
  )
}
