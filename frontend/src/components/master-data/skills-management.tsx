'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Edit2, Trash2, Users, BarChart3, Tag, AlertCircle } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { SkillForm } from './skill-form'
import { apiClient } from '@/lib/api-client'
import { toast } from 'react-hot-toast'

interface Skill {
  id: string
  name: string
  description: string
  category: string
  tags: string[]
  usageCount: number
  createdAt: string
  updatedAt: string
  status: 'active' | 'inactive' | 'draft'
  dependencies?: string[]
  examples?: string[]
}

interface SkillsManagementProps {
  onSkillSelect?: (skill: Skill) => void
  selectionMode?: boolean
  selectedSkills?: string[]
}

export function SkillsManagement({ 
  onSkillSelect, 
  selectionMode = false, 
  selectedSkills = [] 
}: SkillsManagementProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null)

  const queryClient = useQueryClient()

  const { data: skillsResponse, isLoading } = useQuery({
    queryKey: ['skills'],
    queryFn: () => apiClient.get('/api/v1/skills'),
  })

  const { data: categoriesResponse } = useQuery({
    queryKey: ['skill-categories'],
    queryFn: () => apiClient.get('/api/v1/skills/categories'),
  })

  const skills = skillsResponse?.data || []
  const categories = categoriesResponse?.data || []

  const createMutation = useMutation({
    mutationFn: (data: Partial<Skill>) => apiClient.post('/api/v1/skills', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] })
      setShowCreateModal(false)
      toast.success('Skill created successfully')
    },
    onError: (error) => {
      toast.error('Failed to create skill')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Skill> }) => 
      apiClient.put(`/api/v1/skills/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] })
      setEditingSkill(null)
      toast.success('Skill updated successfully')
    },
    onError: (error) => {
      toast.error('Failed to update skill')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/skills/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] })
      setShowDeleteConfirm(null)
      toast.success('Skill deleted successfully')
    },
    onError: (error) => {
      toast.error('Failed to delete skill')
    },
  })

  const filteredSkills = Array.isArray(skills) ? skills.filter((skill: Skill) => {
    const matchesSearch = skill.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         skill.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || skill.category === selectedCategory
    return matchesSearch && matchesCategory
  }) : []

  const handleCreateSkill = (data: Partial<Skill>) => {
    createMutation.mutate(data)
  }

  const handleUpdateSkill = (data: Partial<Skill>) => {
    if (editingSkill) {
      updateMutation.mutate({ id: editingSkill.id, data })
    }
  }

  const handleDeleteSkill = (id: string) => {
    deleteMutation.mutate(id)
  }

  const handleSkillToggle = (skill: Skill) => {
    if (onSkillSelect) {
      onSkillSelect(skill)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Skills Management</h2>
          <p className="text-gray-600">Manage agent capabilities and skill definitions</p>
        </div>
        {!selectionMode && (
          <Button
            onClick={() => setShowCreateModal(true)}
            className="bg-purple-600 hover:bg-purple-700 text-white"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Skill
          </Button>
        )}
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search skills..."
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
        </div>
      </div>

      {/* Skills Grid */}
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
          {filteredSkills.map((skill: Skill) => (
            <SkillCard
              key={skill.id}
              skill={skill}
              selectionMode={selectionMode}
              isSelected={selectedSkills.includes(skill.id)}
              onSelect={() => handleSkillToggle(skill)}
              onEdit={() => setEditingSkill(skill)}
              onDelete={() => setShowDeleteConfirm(skill.id)}
            />
          ))}
        </div>
      )}

      {filteredSkills.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <Tag className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No skills found</h3>
          <p className="text-gray-600">Create your first skill to get started.</p>
        </div>
      )}

      {/* Create Skill Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Skill"
      >
        <SkillForm
          onSubmit={handleCreateSkill}
          onCancel={() => setShowCreateModal(false)}
          isLoading={createMutation.isPending}
        />
      </Modal>

      {/* Edit Skill Modal */}
      <Modal
        isOpen={!!editingSkill}
        onClose={() => setEditingSkill(null)}
        title="Edit Skill"
      >
        {editingSkill && (
          <SkillForm
            initialData={editingSkill}
            onSubmit={handleUpdateSkill}
            onCancel={() => setEditingSkill(null)}
            isLoading={updateMutation.isPending}
          />
        )}
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(null)}
        title="Delete Skill"
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
              onClick={() => showDeleteConfirm && handleDeleteSkill(showDeleteConfirm)}
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

function SkillCard({ 
  skill, 
  selectionMode, 
  isSelected, 
  onSelect, 
  onEdit, 
  onDelete 
}: {
  skill: Skill
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

  return (
    <div className={`bg-white rounded-lg border p-6 hover:shadow-md transition-all ${
      selectionMode ? 'cursor-pointer' : ''
    } ${isSelected ? 'border-purple-500 bg-purple-50' : ''}`}
    onClick={selectionMode ? onSelect : undefined}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">{skill.name}</h3>
            {selectionMode && isSelected && (
              <Badge className="bg-purple-100 text-purple-800">Selected</Badge>
            )}
          </div>
          <p className="text-gray-600 text-sm mb-3">{skill.description}</p>
          
          <div className="flex items-center space-x-2 mb-3">
            <Badge className="bg-blue-100 text-blue-800">{skill.category}</Badge>
            <Badge className={getStatusColor(skill.status)}>{skill.status}</Badge>
          </div>

          {skill.tags && skill.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-3">
              {skill.tags.map((tag) => (
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
            <Users className="w-4 h-4" />
            <span>{skill.usageCount} uses</span>
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
