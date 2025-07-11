'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, Search, Filter, Settings, Plug, Code, Shield, CheckCircle, XCircle } from 'lucide-react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { Badge } from '@/components/ui/Badge'

export default function ToolsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState<string>('all')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  const { data: tools, isLoading } = useQuery({
    queryKey: ['tools', searchQuery, filterType, filterStatus],
    queryFn: () => api.tools.list(),
  })

  const filteredTools = tools?.filter((tool: any) => {
    const matchesSearch = tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         tool.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesType = filterType === 'all' || tool.type === filterType
    const matchesStatus = filterStatus === 'all' || tool.status === filterStatus
    return matchesSearch && matchesType && matchesStatus
  }) || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tools</h1>
          <p className="text-gray-600">Manage MCP tools and custom integrations</p>
        </div>
        <Link
          href={"/tools/create" as any}
          className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Create Tool</span>
        </Link>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search tools..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="all">All Types</option>
            <option value="mcp">MCP Tools</option>
            <option value="custom">Custom Tools</option>
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="pending">Pending</option>
          </select>

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

      {/* Tools Grid/List */}
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
          {filteredTools.map((tool: any) => (
            <ToolCard key={tool.id} tool={tool} viewMode={viewMode} />
          ))}
        </div>
      )}

      {filteredTools.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <Plug className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No tools found</h3>
          <p className="text-gray-600">Create your first tool to get started.</p>
        </div>
      )}
    </div>
  )
}

function ToolCard({ tool, viewMode }: { tool: any; viewMode: 'grid' | 'list' }) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'inactive': return 'bg-gray-100 text-gray-800'
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'mcp': return <Plug className="w-5 h-5 text-blue-600" />
      case 'custom': return <Code className="w-5 h-5 text-purple-600" />
      default: return <Settings className="w-5 h-5 text-gray-600" />
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'inactive': return <XCircle className="w-4 h-4 text-gray-600" />
      case 'pending': return <Shield className="w-4 h-4 text-yellow-600" />
      default: return <XCircle className="w-4 h-4 text-gray-600" />
    }
  }

  if (viewMode === 'list') {
    return (
      <div className="bg-white rounded-lg border p-6 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4 flex-1">
            <div className="flex-shrink-0">
              {getTypeIcon(tool.type)}
            </div>
            <div className="flex-1">
              <div className="flex items-center space-x-3">
                <h3 className="text-lg font-semibold text-gray-900">{tool.name}</h3>
                <Badge className={getStatusColor(tool.status)}>
                  <div className="flex items-center space-x-1">
                    {getStatusIcon(tool.status)}
                    <span>{tool.status}</span>
                  </div>
                </Badge>
                <Badge className="bg-blue-100 text-blue-800">{tool.type}</Badge>
              </div>
              <p className="text-gray-600 mt-1">{tool.description}</p>
              <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                <span>Version: {tool.version}</span>
                <span>Updated: {tool.updatedAt}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button className="p-2 hover:bg-gray-100 rounded-lg">
              <Settings className="w-4 h-4 text-gray-600" />
            </button>
            <Link
              href={`/tools/${tool.id}` as any}
              className="text-primary-600 hover:text-primary-700 text-sm font-medium"
            >
              Configure
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          {getTypeIcon(tool.type)}
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{tool.name}</h3>
            <p className="text-gray-600 text-sm mt-1">{tool.description}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusIcon(tool.status)}
        </div>
      </div>
      
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Badge className={getStatusColor(tool.status)}>{tool.status}</Badge>
          <Badge className="bg-blue-100 text-blue-800">{tool.type}</Badge>
        </div>
        <span className="text-sm text-gray-500">v{tool.version}</span>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-500">Updated {tool.updatedAt}</span>
        <div className="flex items-center space-x-2">
          <button className="p-2 hover:bg-gray-100 rounded-lg">
            <Settings className="w-4 h-4 text-gray-600" />
          </button>
          <Link
            href={`/tools/${tool.id}` as any}
            className="text-primary-600 hover:text-primary-700 text-sm font-medium"
          >
            Configure
          </Link>
        </div>
      </div>
    </div>
  )
}
