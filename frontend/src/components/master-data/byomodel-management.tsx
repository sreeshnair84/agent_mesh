'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Plus, Search, Edit2, Trash2, Database, Settings, 
  Activity, DollarSign, AlertCircle, BarChart3
} from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { ModelForm } from './model-form'
import { apiClient } from '@/lib/api-client'
import { toast } from 'react-hot-toast'

interface Model {
  id: string
  name: string
  provider: string
  modelType: 'llm' | 'embedding' | 'vision' | 'audio' | 'custom'
  config: ModelConfig
  performance: ModelPerformance
  costs: ModelCosts
  usageCount: number
  createdAt: string
  updatedAt: string
  status: 'active' | 'inactive' | 'testing' | 'deprecated'
  tags: string[]
  description?: string
}

interface ModelConfig {
  endpoint: string
  apiKey: string
  maxTokens: number
  temperature: number
  topP?: number
  frequencyPenalty?: number
  presencePenalty?: number
  headers?: Record<string, string>
  timeout?: number
  retries?: number
}

interface ModelPerformance {
  averageLatency: number
  successRate: number
  tokensPerSecond: number
  lastTested: string
  healthScore: number
}

interface ModelCosts {
  inputCostPer1kTokens: number
  outputCostPer1kTokens: number
  totalCost: number
  totalTokens: number
  avgCostPerRequest: number
}

interface BYOModelManagementProps {
  onModelSelect?: (model: Model) => void
  selectionMode?: boolean
  selectedModels?: string[]
}

export function BYOModelManagement({ 
  onModelSelect, 
  selectionMode = false, 
  selectedModels = [] 
}: BYOModelManagementProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedProvider, setSelectedProvider] = useState('all')
  const [selectedType, setSelectedType] = useState('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingModel, setEditingModel] = useState<Model | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null)
  const [showPerformanceModal, setShowPerformanceModal] = useState<Model | null>(null)
  const [showCostsModal, setShowCostsModal] = useState<Model | null>(null)

  const queryClient = useQueryClient()

  const { data: modelsResponse, isLoading } = useQuery({
    queryKey: ['models'],
    queryFn: () => apiClient.get('/api/v1/models'),
  })

  const { data: providersResponse } = useQuery({
    queryKey: ['model-providers'],
    queryFn: () => apiClient.get('/api/v1/models/providers'),
  })

  const models = modelsResponse?.data || []
  const providers = providersResponse?.data || []

  const createMutation = useMutation({
    mutationFn: (data: Partial<Model>) => apiClient.post('/api/v1/models', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] })
      setShowCreateModal(false)
      toast.success('Model created successfully')
    },
    onError: (error) => {
      toast.error('Failed to create model')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Model> }) => 
      apiClient.put(`/api/v1/models/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] })
      setEditingModel(null)
      toast.success('Model updated successfully')
    },
    onError: (error) => {
      toast.error('Failed to update model')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/models/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] })
      setShowDeleteConfirm(null)
      toast.success('Model deleted successfully')
    },
    onError: (error) => {
      toast.error('Failed to delete model')
    },
  })

  const testMutation = useMutation({
    mutationFn: (id: string) => apiClient.post(`/api/v1/models/${id}/test`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] })
      toast.success('Model test completed')
    },
    onError: (error) => {
      toast.error('Failed to test model')
    },
  })

  const filteredModels = Array.isArray(models) ? models.filter((model: Model) => {
    const matchesSearch = model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         model.provider.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         model.description?.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesProvider = selectedProvider === 'all' || model.provider === selectedProvider
    const matchesType = selectedType === 'all' || model.modelType === selectedType
    return matchesSearch && matchesProvider && matchesType
  }) : []

  const handleCreateModel = (data: Partial<Model>) => {
    createMutation.mutate(data)
  }

  const handleUpdateModel = (data: Partial<Model>) => {
    if (editingModel) {
      updateMutation.mutate({ id: editingModel.id, data })
    }
  }

  const handleDeleteModel = (id: string) => {
    deleteMutation.mutate(id)
  }

  const handleModelToggle = (model: Model) => {
    if (onModelSelect) {
      onModelSelect(model)
    }
  }

  const handleTestModel = (id: string) => {
    testMutation.mutate(id)
  }

  const modelTypes = [
    { value: 'all', label: 'All Types' },
    { value: 'llm', label: 'LLM' },
    { value: 'embedding', label: 'Embedding' },
    { value: 'vision', label: 'Vision' },
    { value: 'audio', label: 'Audio' },
    { value: 'custom', label: 'Custom' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">BYOModel Management</h2>
          <p className="text-gray-600">Manage your own model configurations with performance monitoring</p>
        </div>
        {!selectionMode && (
          <Button
            onClick={() => setShowCreateModal(true)}
            className="bg-purple-600 hover:bg-purple-700 text-white"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Model
          </Button>
        )}
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search models..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="all">All Providers</option>
            {Array.isArray(providers) && providers.map((provider: string) => (
              <option key={provider} value={provider}>
                {provider}
              </option>
            ))}
          </select>

          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            {modelTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Models Grid */}
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredModels.map((model: Model) => (
            <ModelCard
              key={model.id}
              model={model}
              selectionMode={selectionMode}
              isSelected={selectedModels.includes(model.id)}
              onSelect={() => handleModelToggle(model)}
              onEdit={() => setEditingModel(model)}
              onDelete={() => setShowDeleteConfirm(model.id)}
              onTest={() => handleTestModel(model.id)}
              onViewPerformance={() => setShowPerformanceModal(model)}
              onViewCosts={() => setShowCostsModal(model)}
            />
          ))}
        </div>
      )}

      {filteredModels.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No models found</h3>
          <p className="text-gray-600">Add your first model to get started.</p>
        </div>
      )}

      {/* Create Model Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Add New Model"
        size="lg"
      >
        <ModelForm
          onSubmit={handleCreateModel}
          onCancel={() => setShowCreateModal(false)}
          isLoading={createMutation.isPending}
        />
      </Modal>

      {/* Edit Model Modal */}
      <Modal
        isOpen={!!editingModel}
        onClose={() => setEditingModel(null)}
        title="Edit Model"
        size="lg"
      >
        {editingModel && (
          <ModelForm
            initialData={editingModel}
            onSubmit={handleUpdateModel}
            onCancel={() => setEditingModel(null)}
            isLoading={updateMutation.isPending}
          />
        )}
      </Modal>

      {/* Performance Modal */}
      {showPerformanceModal && (
        <Modal
          isOpen={!!showPerformanceModal}
          onClose={() => setShowPerformanceModal(null)}
          title="Model Performance"
          size="lg"
        >
          <ModelPerformanceView
            model={showPerformanceModal}
            onClose={() => setShowPerformanceModal(null)}
          />
        </Modal>
      )}

      {/* Costs Modal */}
      {showCostsModal && (
        <Modal
          isOpen={!!showCostsModal}
          onClose={() => setShowCostsModal(null)}
          title="Model Costs"
          size="lg"
        >
          <ModelCostsView
            model={showCostsModal}
            onClose={() => setShowCostsModal(null)}
          />
        </Modal>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(null)}
        title="Delete Model"
      >
        <div className="space-y-4">
          <div className="flex items-center space-x-3">
            <AlertCircle className="w-6 h-6 text-red-500" />
            <div>
              <h3 className="text-lg font-medium text-gray-900">Are you sure?</h3>
              <p className="text-gray-600">This action cannot be undone.</p>
            </div>
          </div>
          <div className="flex justify-end space-x-3">
            <Button
              variant="outline"
              onClick={() => setShowDeleteConfirm(null)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => showDeleteConfirm && handleDeleteModel(showDeleteConfirm)}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

function ModelCard({ 
  model, 
  selectionMode, 
  isSelected, 
  onSelect, 
  onEdit, 
  onDelete,
  onTest,
  onViewPerformance,
  onViewCosts
}: {
  model: Model
  selectionMode: boolean
  isSelected: boolean
  onSelect: () => void
  onEdit: () => void
  onDelete: () => void
  onTest: () => void
  onViewPerformance: () => void
  onViewCosts: () => void
}) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'inactive': return 'bg-gray-100 text-gray-800'
      case 'testing': return 'bg-yellow-100 text-yellow-800'
      case 'deprecated': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'llm': return 'bg-blue-100 text-blue-800'
      case 'embedding': return 'bg-green-100 text-green-800'
      case 'vision': return 'bg-purple-100 text-purple-800'
      case 'audio': return 'bg-orange-100 text-orange-800'
      case 'custom': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className={`bg-white rounded-lg border p-6 hover:shadow-md transition-all ${
      selectionMode ? 'cursor-pointer' : ''
    } ${isSelected ? 'border-purple-500 bg-purple-50' : ''}`}
    onClick={selectionMode ? onSelect : undefined}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">{model.name}</h3>
            {selectionMode && isSelected && (
              <Badge className="bg-purple-100 text-purple-800">Selected</Badge>
            )}
          </div>
          <p className="text-gray-600 text-sm mb-3">{model.description}</p>
          
          <div className="flex items-center space-x-2 mb-3">
            <Badge className={getTypeColor(model.modelType)}>{model.modelType}</Badge>
            <Badge className={getStatusColor(model.status)}>{model.status}</Badge>
            <Badge className="bg-gray-100 text-gray-800">{model.provider}</Badge>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-3">
            <div>
              <p className="text-xs text-gray-500">Health Score</p>
              <p className={`text-sm font-medium ${getHealthColor(model.performance.healthScore)}`}>
                {model.performance.healthScore}%
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Success Rate</p>
              <p className="text-sm font-medium text-gray-900">
                {model.performance.successRate}%
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Avg Latency</p>
              <p className="text-sm font-medium text-gray-900">
                {model.performance.averageLatency}ms
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Total Cost</p>
              <p className="text-sm font-medium text-gray-900">
                ${model.costs.totalCost.toFixed(2)}
              </p>
            </div>
          </div>

          {model.tags && model.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-3">
              {model.tags.map((tag) => (
                <Badge key={tag} className="bg-gray-100 text-gray-600 text-xs">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4 text-sm text-gray-500">
          <div className="flex items-center space-x-1">
            <Database className="w-4 h-4" />
            <span>{model.usageCount} uses</span>
          </div>
        </div>
        
        {!selectionMode && (
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onViewPerformance}
              title="View performance"
            >
              <Activity className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onViewCosts}
              title="View costs"
            >
              <DollarSign className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onTest}
              title="Test model"
            >
              <Settings className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onEdit}
            >
              <Edit2 className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onDelete}
              className="text-red-600 hover:text-red-700"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

function ModelPerformanceView({ model, onClose }: {
  model: Model
  onClose: () => void
}) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <Activity className="w-5 h-5 text-green-600" />
            <h3 className="font-medium text-green-900">Health Score</h3>
          </div>
          <p className="text-2xl font-bold text-green-600">{model.performance.healthScore}%</p>
        </div>
        
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <BarChart3 className="w-5 h-5 text-blue-600" />
            <h3 className="font-medium text-blue-900">Success Rate</h3>
          </div>
          <p className="text-2xl font-bold text-blue-600">{model.performance.successRate}%</p>
        </div>
        
        <div className="bg-purple-50 p-4 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <Activity className="w-5 h-5 text-purple-600" />
            <h3 className="font-medium text-purple-900">Avg Latency</h3>
          </div>
          <p className="text-2xl font-bold text-purple-600">{model.performance.averageLatency}ms</p>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium mb-4">Performance Metrics</h3>
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-gray-600">Tokens per second</span>
            <span className="font-medium">{model.performance.tokensPerSecond}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Last tested</span>
            <span className="font-medium">{model.performance.lastTested}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Total usage</span>
            <span className="font-medium">{model.usageCount} requests</span>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <Button onClick={onClose}>
          Close
        </Button>
      </div>
    </div>
  )
}

function ModelCostsView({ model, onClose }: {
  model: Model
  onClose: () => void
}) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <DollarSign className="w-5 h-5 text-green-600" />
            <h3 className="font-medium text-green-900">Total Cost</h3>
          </div>
          <p className="text-2xl font-bold text-green-600">${model.costs.totalCost.toFixed(2)}</p>
        </div>
        
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <BarChart3 className="w-5 h-5 text-blue-600" />
            <h3 className="font-medium text-blue-900">Avg Cost/Request</h3>
          </div>
          <p className="text-2xl font-bold text-blue-600">${model.costs.avgCostPerRequest.toFixed(4)}</p>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium mb-4">Cost Breakdown</h3>
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-gray-600">Input cost per 1K tokens</span>
            <span className="font-medium">${model.costs.inputCostPer1kTokens.toFixed(4)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Output cost per 1K tokens</span>
            <span className="font-medium">${model.costs.outputCostPer1kTokens.toFixed(4)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Total tokens processed</span>
            <span className="font-medium">{model.costs.totalTokens.toLocaleString()}</span>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <Button onClick={onClose}>
          Close
        </Button>
      </div>
    </div>
  )
}
