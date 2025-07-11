'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Edit2, Trash2, Shield, Code, AlertCircle, Settings } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { ConstraintForm } from './constraint-form'
import { apiClient } from '@/lib/api-client'
import { toast } from 'react-hot-toast'

interface Constraint {
  id: string
  name: string
  description: string
  type: 'validation' | 'security' | 'performance' | 'custom'
  config: Record<string, any>
  template: string
  rules: ConstraintRule[]
  usageCount: number
  createdAt: string
  updatedAt: string
  status: 'active' | 'inactive' | 'draft'
}

interface ConstraintRule {
  field: string
  operator: 'equals' | 'contains' | 'regex' | 'range' | 'custom'
  value: any
  message: string
}

interface ConstraintsManagementProps {
  onConstraintSelect?: (constraint: Constraint) => void
  selectionMode?: boolean
  selectedConstraints?: string[]
}

export function ConstraintsManagement({ 
  onConstraintSelect, 
  selectionMode = false, 
  selectedConstraints = [] 
}: ConstraintsManagementProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedType, setSelectedType] = useState('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingConstraint, setEditingConstraint] = useState<Constraint | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null)
  const [showTemplateModal, setShowTemplateModal] = useState(false)

  const queryClient = useQueryClient()

  const { data: constraintsResponse, isLoading } = useQuery({
    queryKey: ['constraints'],
    queryFn: () => apiClient.get('/api/v1/constraints'),
  })

  const { data: templatesResponse } = useQuery({
    queryKey: ['constraint-templates'],
    queryFn: () => apiClient.get('/api/v1/constraints/templates'),
  })

  const constraints = constraintsResponse?.data || []
  const templates = templatesResponse?.data || []

  const createMutation = useMutation({
    mutationFn: (data: Partial<Constraint>) => apiClient.post('/api/v1/constraints', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['constraints'] })
      setShowCreateModal(false)
      toast.success('Constraint created successfully')
    },
    onError: (error) => {
      toast.error('Failed to create constraint')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Constraint> }) => 
      apiClient.put(`/api/v1/constraints/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['constraints'] })
      setEditingConstraint(null)
      toast.success('Constraint updated successfully')
    },
    onError: (error) => {
      toast.error('Failed to update constraint')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/constraints/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['constraints'] })
      setShowDeleteConfirm(null)
      toast.success('Constraint deleted successfully')
    },
    onError: (error) => {
      toast.error('Failed to delete constraint')
    },
  })

  const filteredConstraints = Array.isArray(constraints) ? constraints.filter((constraint: Constraint) => {
    const matchesSearch = constraint.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         constraint.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesType = selectedType === 'all' || constraint.type === selectedType
    return matchesSearch && matchesType
  }) : []

  const handleCreateConstraint = (data: Partial<Constraint>) => {
    createMutation.mutate(data)
  }

  const handleUpdateConstraint = (data: Partial<Constraint>) => {
    if (editingConstraint) {
      updateMutation.mutate({ id: editingConstraint.id, data })
    }
  }

  const handleDeleteConstraint = (id: string) => {
    deleteMutation.mutate(id)
  }

  const handleConstraintToggle = (constraint: Constraint) => {
    if (onConstraintSelect) {
      onConstraintSelect(constraint)
    }
  }

  const constraintTypes = [
    { value: 'all', label: 'All Types' },
    { value: 'validation', label: 'Validation' },
    { value: 'security', label: 'Security' },
    { value: 'performance', label: 'Performance' },
    { value: 'custom', label: 'Custom' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Constraints Management</h2>
          <p className="text-gray-600">Define agent constraints and validation rules</p>
        </div>
        <div className="flex items-center space-x-3">
          {!selectionMode && (
            <>
              <Button
                variant="outline"
                onClick={() => setShowTemplateModal(true)}
              >
                <Code className="w-4 h-4 mr-2" />
                Templates
              </Button>
              <Button
                onClick={() => setShowCreateModal(true)}
                className="bg-purple-600 hover:bg-purple-700 text-white"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Constraint
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search constraints..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            {constraintTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Constraints Grid */}
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
          {filteredConstraints.map((constraint: Constraint) => (
            <ConstraintCard
              key={constraint.id}
              constraint={constraint}
              selectionMode={selectionMode}
              isSelected={selectedConstraints.includes(constraint.id)}
              onSelect={() => handleConstraintToggle(constraint)}
              onEdit={() => setEditingConstraint(constraint)}
              onDelete={() => setShowDeleteConfirm(constraint.id)}
            />
          ))}
        </div>
      )}

      {filteredConstraints.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <Shield className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No constraints found</h3>
          <p className="text-gray-600">Create your first constraint to get started.</p>
        </div>
      )}

      {/* Create Constraint Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Constraint"
        size="lg"
      >
        <ConstraintForm
          templates={Array.isArray(templates) ? templates : []}
          onSubmit={handleCreateConstraint}
          onCancel={() => setShowCreateModal(false)}
          isLoading={createMutation.isPending}
        />
      </Modal>

      {/* Edit Constraint Modal */}
      <Modal
        isOpen={!!editingConstraint}
        onClose={() => setEditingConstraint(null)}
        title="Edit Constraint"
        size="lg"
      >
        {editingConstraint && (
          <ConstraintForm
            initialData={editingConstraint}
            templates={Array.isArray(templates) ? templates : []}
            onSubmit={handleUpdateConstraint}
            onCancel={() => setEditingConstraint(null)}
            isLoading={updateMutation.isPending}
          />
        )}
      </Modal>

      {/* Templates Modal */}
      <Modal
        isOpen={showTemplateModal}
        onClose={() => setShowTemplateModal(false)}
        title="Constraint Templates"
        size="xl"
      >
        <ConstraintTemplatesView
          templates={Array.isArray(templates) ? templates : []}
          onSelectTemplate={(template) => {
            setShowTemplateModal(false)
            setShowCreateModal(true)
            // Pre-populate form with template data
          }}
        />
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(null)}
        title="Delete Constraint"
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
              onClick={() => showDeleteConfirm && handleDeleteConstraint(showDeleteConfirm)}
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

function ConstraintCard({ 
  constraint, 
  selectionMode, 
  isSelected, 
  onSelect, 
  onEdit, 
  onDelete 
}: {
  constraint: Constraint
  selectionMode: boolean
  isSelected: boolean
  onSelect: () => void
  onEdit: () => void
  onDelete: () => void
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
      case 'validation': return 'bg-blue-100 text-blue-800'
      case 'security': return 'bg-red-100 text-red-800'
      case 'performance': return 'bg-green-100 text-green-800'
      case 'custom': return 'bg-purple-100 text-purple-800'
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
            <h3 className="text-lg font-semibold text-gray-900">{constraint.name}</h3>
            {selectionMode && isSelected && (
              <Badge className="bg-purple-100 text-purple-800">Selected</Badge>
            )}
          </div>
          <p className="text-gray-600 text-sm mb-3">{constraint.description}</p>
          
          <div className="flex items-center space-x-2 mb-3">
            <Badge className={getTypeColor(constraint.type)}>{constraint.type}</Badge>
            <Badge className={getStatusColor(constraint.status)}>{constraint.status}</Badge>
          </div>

          {constraint.rules && constraint.rules.length > 0 && (
            <div className="mb-3">
              <p className="text-sm text-gray-500 mb-1">Rules:</p>
              <div className="space-y-1">
                {constraint.rules.slice(0, 2).map((rule, index) => (
                  <div key={index} className="text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded">
                    {rule.field} {rule.operator} {String(rule.value)}
                  </div>
                ))}
                {constraint.rules.length > 2 && (
                  <div className="text-xs text-gray-500">
                    +{constraint.rules.length - 2} more rules
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4 text-sm text-gray-500">
          <div className="flex items-center space-x-1">
            <Shield className="w-4 h-4" />
            <span>{constraint.usageCount} uses</span>
          </div>
        </div>
        
        {!selectionMode && (
          <div className="flex items-center space-x-2">
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

function ConstraintTemplatesView({ 
  templates, 
  onSelectTemplate 
}: {
  templates: any[]
  onSelectTemplate: (template: any) => void
}) {
  return (
    <div className="space-y-4">
      <p className="text-gray-600">Choose from pre-built constraint templates:</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {templates.map((template) => (
          <div
            key={template.id}
            className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => onSelectTemplate(template)}
          >
            <div className="flex items-center space-x-2 mb-2">
              <h3 className="font-medium">{template.name}</h3>
              <Badge className="bg-blue-100 text-blue-800">{template.type}</Badge>
            </div>
            <p className="text-sm text-gray-600 mb-3">{template.description}</p>
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-500">
                {template.rulesCount} rules
              </span>
              <Button size="sm" variant="outline">
                Use Template
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
