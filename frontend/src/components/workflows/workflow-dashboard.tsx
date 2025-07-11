'use client'

import { useState } from 'react'
import { 
  Search, 
  Plus, 
  Play, 
  Pause, 
  Edit, 
  Trash2, 
  Eye,
  GitBranch,
  Clock,
  Users,
  Activity,
  TrendingUp
} from 'lucide-react'
import Link from 'next/link'

interface Workflow {
  id: string
  name: string
  description: string
  agents: number
  status: 'active' | 'inactive' | 'error'
  created: Date
  lastUsed: Date
  executions: number
  successRate: number
  avgDuration: number
  owner: string
}

const mockWorkflows: Workflow[] = [
  {
    id: '1',
    name: 'Customer Support Pipeline',
    description: 'Automated customer support workflow with sentiment analysis and escalation',
    agents: 4,
    status: 'active',
    created: new Date('2024-01-15'),
    lastUsed: new Date('2024-01-20'),
    executions: 1245,
    successRate: 94.2,
    avgDuration: 45000, // in ms
    owner: 'Support Team'
  },
  {
    id: '2',
    name: 'Data Analysis Pipeline',
    description: 'Multi-step data processing and insight generation workflow',
    agents: 3,
    status: 'active',
    created: new Date('2024-01-10'),
    lastUsed: new Date('2024-01-19'),
    executions: 567,
    successRate: 98.1,
    avgDuration: 120000,
    owner: 'Data Team'
  },
  {
    id: '3',
    name: 'Content Moderation',
    description: 'Automated content review and moderation workflow',
    agents: 2,
    status: 'inactive',
    created: new Date('2024-01-08'),
    lastUsed: new Date('2024-01-15'),
    executions: 2340,
    successRate: 89.7,
    avgDuration: 15000,
    owner: 'Content Team'
  }
]

export function WorkflowDashboard() {
  const [workflows, setWorkflows] = useState<Workflow[]>(mockWorkflows)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  const filteredWorkflows = workflows.filter(workflow => {
    const matchesSearch = workflow.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         workflow.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = selectedStatus === 'all' || workflow.status === selectedStatus
    return matchesSearch && matchesStatus
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'status-active'
      case 'inactive': return 'status-inactive'
      case 'error': return 'status-error'
      default: return 'status-inactive'
    }
  }

  const formatDuration = (ms: number) => {
    const seconds = Math.floor(ms / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)

    if (hours > 0) return `${hours}h ${minutes % 60}m`
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`
    return `${seconds}s`
  }

  const WorkflowCard = ({ workflow }: { workflow: Workflow }) => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <h3 className="text-lg font-semibold text-gray-900">{workflow.name}</h3>
              <span className={`status-badge ${getStatusColor(workflow.status)}`}>
                {workflow.status}
              </span>
            </div>
            <p className="text-gray-600 text-sm mb-3">{workflow.description}</p>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <div className="flex items-center space-x-1">
                <GitBranch className="h-4 w-4" />
                <span>{workflow.agents} agents</span>
              </div>
              <div className="flex items-center space-x-1">
                <Activity className="h-4 w-4" />
                <span>{workflow.executions} runs</span>
              </div>
              <div className="flex items-center space-x-1">
                <TrendingUp className="h-4 w-4" />
                <span>{workflow.successRate}% success</span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{workflow.executions}</div>
            <div className="text-xs text-gray-500">Total Runs</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{workflow.successRate}%</div>
            <div className="text-xs text-gray-500">Success Rate</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{formatDuration(workflow.avgDuration)}</div>
            <div className="text-xs text-gray-500">Avg Duration</div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <Users className="h-4 w-4" />
            <span>by {workflow.owner}</span>
          </div>
          <div className="flex space-x-2">
            <button className="btn-primary flex items-center space-x-1">
              <Play className="h-4 w-4" />
              <span>Execute</span>
            </button>
            <Link href={`/workflows/${workflow.id}` as any} className="btn-secondary flex items-center space-x-1">
              <Eye className="h-4 w-4" />
              <span>View</span>
            </Link>
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

  // Summary stats
  const totalWorkflows = workflows.length
  const activeWorkflows = workflows.filter(w => w.status === 'active').length
  const totalExecutions = workflows.reduce((sum, w) => sum + w.executions, 0)
  const avgSuccessRate = workflows.reduce((sum, w) => sum + w.successRate, 0) / workflows.length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agentic Workflows</h1>
          <p className="text-gray-600">Orchestrate multi-agent processes</p>
        </div>
        <Link href={"/workflows/create" as any} className="btn-primary flex items-center space-x-2">
          <Plus className="h-4 w-4" />
          <span>Create Workflow</span>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <GitBranch className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">{totalWorkflows}</div>
              <div className="text-sm text-gray-500">Total Workflows</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <Activity className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">{activeWorkflows}</div>
              <div className="text-sm text-gray-500">Active Workflows</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Play className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">{totalExecutions.toLocaleString()}</div>
              <div className="text-sm text-gray-500">Total Executions</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <TrendingUp className="h-6 w-6 text-yellow-600" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">{avgSuccessRate.toFixed(1)}%</div>
              <div className="text-sm text-gray-500">Avg Success Rate</div>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search workflows..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input pl-10"
            />
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Status:</span>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="error">Error</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-700">
          {filteredWorkflows.length} workflow{filteredWorkflows.length !== 1 ? 's' : ''} found
        </p>
      </div>

      {/* Workflow Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredWorkflows.map(workflow => (
          <WorkflowCard key={workflow.id} workflow={workflow} />
        ))}
      </div>

      {/* Empty State */}
      {filteredWorkflows.length === 0 && (
        <div className="text-center py-12">
          <GitBranch className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No workflows found</h3>
          <p className="text-gray-600 mb-4">Get started by creating your first workflow</p>
          <Link href={"/workflows/create" as any} className="btn-primary">
            Create Workflow
          </Link>
        </div>
      )}
    </div>
  )
}
