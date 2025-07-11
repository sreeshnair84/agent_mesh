'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Plus, Search, Edit2, Trash2, MessageSquare, Copy, 
  TestTube, Star, AlertCircle, Code, GitBranch 
} from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { PromptForm } from './prompt-form'
import { apiClient } from '@/lib/api-client'
import { toast } from 'react-hot-toast'

interface Prompt {
  id: string
  name: string
  content: string
  version: string
  description?: string
  tags: string[]
  type: 'system' | 'user' | 'assistant' | 'function'
  category: string
  variables: PromptVariable[]
  usageCount: number
  rating: number
  createdAt: string
  updatedAt: string
  status: 'active' | 'inactive' | 'draft'
  isTemplate: boolean
  testCases?: PromptTestCase[]
}

interface PromptVariable {
  name: string
  type: 'string' | 'number' | 'boolean' | 'array'
  description: string
  required: boolean
  defaultValue?: any
}

interface PromptTestCase {
  id: string
  name: string
  variables: Record<string, any>
  expectedOutput?: string
  result?: 'pass' | 'fail' | 'pending'
}

interface PromptsManagementProps {
  onPromptSelect?: (prompt: Prompt) => void
  selectionMode?: boolean
  selectedPrompts?: string[]
}

export function PromptsManagement({ 
  onPromptSelect, 
  selectionMode = false, 
  selectedPrompts = [] 
}: PromptsManagementProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [selectedType, setSelectedType] = useState('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingPrompt, setEditingPrompt] = useState<Prompt | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null)
  const [showTestModal, setShowTestModal] = useState<Prompt | null>(null)
  const [showVersionModal, setShowVersionModal] = useState<Prompt | null>(null)

  const queryClient = useQueryClient()

  const { data: promptsResponse, isLoading } = useQuery({
    queryKey: ['prompts'],
    queryFn: () => apiClient.get('/api/v1/prompts'),
  })

  const { data: categoriesResponse } = useQuery({
    queryKey: ['prompt-categories'],
    queryFn: () => apiClient.get('/api/v1/prompts/categories'),
  })

  const prompts = promptsResponse?.data || []
  const categories = categoriesResponse?.data || []

  const createMutation = useMutation({
    mutationFn: (data: Partial<Prompt>) => apiClient.post('/api/v1/prompts', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
      setShowCreateModal(false)
      toast.success('Prompt created successfully')
    },
    onError: (error) => {
      toast.error('Failed to create prompt')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Prompt> }) => 
      apiClient.put(`/api/v1/prompts/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
      setEditingPrompt(null)
      toast.success('Prompt updated successfully')
    },
    onError: (error) => {
      toast.error('Failed to update prompt')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/prompts/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
      setShowDeleteConfirm(null)
      toast.success('Prompt deleted successfully')
    },
    onError: (error) => {
      toast.error('Failed to delete prompt')
    },
  })

  const testMutation = useMutation({
    mutationFn: ({ id, testCase }: { id: string; testCase: PromptTestCase }) => 
      apiClient.post(`/api/v1/prompts/${id}/test`, testCase),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
      toast.success('Test executed successfully')
    },
    onError: (error) => {
      toast.error('Failed to run test')
    },
  })

  const filteredPrompts = Array.isArray(prompts) ? prompts.filter((prompt: Prompt) => {
    const matchesSearch = prompt.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         prompt.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         prompt.content.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || prompt.category === selectedCategory
    const matchesType = selectedType === 'all' || prompt.type === selectedType
    return matchesSearch && matchesCategory && matchesType
  }) : []

  const handleCreatePrompt = (data: Partial<Prompt>) => {
    createMutation.mutate(data)
  }

  const handleUpdatePrompt = (data: Partial<Prompt>) => {
    if (editingPrompt) {
      updateMutation.mutate({ id: editingPrompt.id, data })
    }
  }

  const handleDeletePrompt = (id: string) => {
    deleteMutation.mutate(id)
  }

  const handlePromptToggle = (prompt: Prompt) => {
    if (onPromptSelect) {
      onPromptSelect(prompt)
    }
  }

  const handleCopyPrompt = (prompt: Prompt) => {
    navigator.clipboard.writeText(prompt.content)
    toast.success('Prompt copied to clipboard')
  }

  const handleTestPrompt = (prompt: Prompt, testCase: PromptTestCase) => {
    testMutation.mutate({ id: prompt.id, testCase })
  }

  const promptTypes = [
    { value: 'all', label: 'All Types' },
    { value: 'system', label: 'System' },
    { value: 'user', label: 'User' },
    { value: 'assistant', label: 'Assistant' },
    { value: 'function', label: 'Function' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Prompts Management</h2>
          <p className="text-gray-600">Manage prompt library with versioning and A/B testing</p>
        </div>
        {!selectionMode && (
          <Button
            onClick={() => setShowCreateModal(true)}
            className="bg-purple-600 hover:bg-purple-700 text-white"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Prompt
          </Button>
        )}
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search prompts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="all">All Categories</option>
            {Array.isArray(categories) && categories.map((category: string) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>

          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            {promptTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Prompts Grid */}
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
          {filteredPrompts.map((prompt: Prompt) => (
            <PromptCard
              key={prompt.id}
              prompt={prompt}
              selectionMode={selectionMode}
              isSelected={selectedPrompts.includes(prompt.id)}
              onSelect={() => handlePromptToggle(prompt)}
              onEdit={() => setEditingPrompt(prompt)}
              onDelete={() => setShowDeleteConfirm(prompt.id)}
              onCopy={() => handleCopyPrompt(prompt)}
              onTest={() => setShowTestModal(prompt)}
              onVersion={() => setShowVersionModal(prompt)}
            />
          ))}
        </div>
      )}

      {filteredPrompts.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No prompts found</h3>
          <p className="text-gray-600">Create your first prompt to get started.</p>
        </div>
      )}

      {/* Create Prompt Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Prompt"
        size="xl"
      >
        <PromptForm
          onSubmit={handleCreatePrompt}
          onCancel={() => setShowCreateModal(false)}
          isLoading={createMutation.isPending}
        />
      </Modal>

      {/* Edit Prompt Modal */}
      <Modal
        isOpen={!!editingPrompt}
        onClose={() => setEditingPrompt(null)}
        title="Edit Prompt"
        size="xl"
      >
        {editingPrompt && (
          <PromptForm
            initialData={editingPrompt}
            onSubmit={handleUpdatePrompt}
            onCancel={() => setEditingPrompt(null)}
            isLoading={updateMutation.isPending}
          />
        )}
      </Modal>

      {/* Test Modal */}
      {showTestModal && (
        <Modal
          isOpen={!!showTestModal}
          onClose={() => setShowTestModal(null)}
          title="Test Prompt"
          size="lg"
        >
          <PromptTester
            prompt={showTestModal}
            onTest={handleTestPrompt}
            onClose={() => setShowTestModal(null)}
          />
        </Modal>
      )}

      {/* Version Modal */}
      {showVersionModal && (
        <Modal
          isOpen={!!showVersionModal}
          onClose={() => setShowVersionModal(null)}
          title="Prompt Versions"
          size="lg"
        >
          <PromptVersions
            prompt={showVersionModal}
            onClose={() => setShowVersionModal(null)}
          />
        </Modal>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(null)}
        title="Delete Prompt"
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
              onClick={() => showDeleteConfirm && handleDeletePrompt(showDeleteConfirm)}
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

function PromptCard({ 
  prompt, 
  selectionMode, 
  isSelected, 
  onSelect, 
  onEdit, 
  onDelete,
  onCopy,
  onTest,
  onVersion
}: {
  prompt: Prompt
  selectionMode: boolean
  isSelected: boolean
  onSelect: () => void
  onEdit: () => void
  onDelete: () => void
  onCopy: () => void
  onTest: () => void
  onVersion: () => void
}) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'inactive': return 'bg-gray-100 text-gray-800'
      case 'draft': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'system': return 'bg-blue-100 text-blue-800'
      case 'user': return 'bg-green-100 text-green-800'
      case 'assistant': return 'bg-purple-100 text-purple-800'
      case 'function': return 'bg-orange-100 text-orange-800'
      default: return 'bg-gray-100 text-gray-800'
    }
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
            <h3 className="text-lg font-semibold text-gray-900">{prompt.name}</h3>
            {prompt.isTemplate && (
              <Badge className="bg-blue-100 text-blue-800">Template</Badge>
            )}
            {selectionMode && isSelected && (
              <Badge className="bg-purple-100 text-purple-800">Selected</Badge>
            )}
          </div>
          <p className="text-gray-600 text-sm mb-3">{prompt.description}</p>
          
          <div className="flex items-center space-x-2 mb-3">
            <Badge className={getTypeColor(prompt.type)}>{prompt.type}</Badge>
            <Badge className={getStatusColor(prompt.status)}>{prompt.status}</Badge>
            <Badge className="bg-gray-100 text-gray-800">v{prompt.version}</Badge>
          </div>

          <div className="flex items-center space-x-2 mb-3">
            <span className="text-sm text-gray-500">
              {prompt.content.length > 100 ? `${prompt.content.substring(0, 100)}...` : prompt.content}
            </span>
          </div>

          {prompt.tags && prompt.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-3">
              {prompt.tags.map((tag) => (
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
            <MessageSquare className="w-4 h-4" />
            <span>{prompt.usageCount} uses</span>
          </div>
          <div className="flex items-center space-x-1">
            <Star className="w-4 h-4" />
            <span>{prompt.rating.toFixed(1)}</span>
          </div>
        </div>
        
        {!selectionMode && (
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onCopy}
              title="Copy prompt"
            >
              <Copy className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onTest}
              title="Test prompt"
            >
              <TestTube className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onVersion}
              title="Version history"
            >
              <GitBranch className="w-4 h-4" />
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

function PromptTester({ prompt, onTest, onClose }: {
  prompt: Prompt
  onTest: (prompt: Prompt, testCase: PromptTestCase) => void
  onClose: () => void
}) {
  const [variables, setVariables] = useState<Record<string, any>>({})
  const [testResult, setTestResult] = useState<string>('')

  const handleVariableChange = (name: string, value: any) => {
    setVariables(prev => ({ ...prev, [name]: value }))
  }

  const handleTest = () => {
    const testCase: PromptTestCase = {
      id: Date.now().toString(),
      name: 'Manual Test',
      variables,
      result: 'pending'
    }
    onTest(prompt, testCase)
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-4">Test Variables</h3>
        <div className="space-y-4">
          {prompt.variables.map((variable) => (
            <div key={variable.name}>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {variable.name}
                {variable.required && <span className="text-red-500 ml-1">*</span>}
              </label>
              <input
                type={variable.type === 'number' ? 'number' : 'text'}
                value={variables[variable.name] || variable.defaultValue || ''}
                onChange={(e) => handleVariableChange(variable.name, e.target.value)}
                placeholder={variable.description}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium mb-4">Preview</h3>
        <div className="bg-gray-50 p-4 rounded-lg">
          <pre className="text-sm text-gray-700 whitespace-pre-wrap">
            {prompt.content}
          </pre>
        </div>
      </div>

      {testResult && (
        <div>
          <h3 className="text-lg font-medium mb-4">Test Result</h3>
          <div className="bg-green-50 p-4 rounded-lg">
            <pre className="text-sm text-gray-700 whitespace-pre-wrap">
              {testResult}
            </pre>
          </div>
        </div>
      )}

      <div className="flex justify-end space-x-3">
        <Button variant="outline" onClick={onClose}>
          Close
        </Button>
        <Button onClick={handleTest}>
          Run Test
        </Button>
      </div>
    </div>
  )
}

function PromptVersions({ prompt, onClose }: {
  prompt: Prompt
  onClose: () => void
}) {
  // Mock version data - in real app, this would come from API
  const versions = [
    { version: '1.0', date: '2024-01-01', changes: 'Initial version' },
    { version: '1.1', date: '2024-01-15', changes: 'Added validation rules' },
    { version: '1.2', date: '2024-02-01', changes: 'Improved error handling' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-4">Version History</h3>
        <div className="space-y-3">
          {versions.map((version) => (
            <div key={version.version} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <Badge className="bg-blue-100 text-blue-800">v{version.version}</Badge>
                  <span className="text-sm text-gray-500">{version.date}</span>
                </div>
                <Button size="sm" variant="outline">
                  Restore
                </Button>
              </div>
              <p className="text-sm text-gray-700">{version.changes}</p>
            </div>
          ))}
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
