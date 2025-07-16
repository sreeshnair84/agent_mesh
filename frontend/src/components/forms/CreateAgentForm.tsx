'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select } from '@/components/ui/select'
import { Card } from '@/components/ui/card'
import { Modal } from '@/components/ui/Modal'
import { Badge } from '@/components/ui/Badge'
import { CreateAgentFormData } from '@/types/create-forms'
import { Plus, X, Settings, Zap, Shield, Clock } from 'lucide-react'

interface CreateAgentFormProps {
  onSubmit: (data: CreateAgentFormData) => void
  onCancel: () => void
  isLoading?: boolean
  categories?: Array<{ id: string; name: string; display_name: string }>
  templates?: Array<{ id: string; name: string; display_name: string }>
  models?: Array<{ id: string; name: string; display_name: string }>
  tools?: Array<{ id: string; name: string; description: string }>
}

export default function CreateAgentForm({
  onSubmit,
  onCancel,
  isLoading = false,
  categories = [],
  templates = [],
  models = [],
  tools = []
}: CreateAgentFormProps) {
  const [selectedTools, setSelectedTools] = useState<string[]>([])
  const [selectedCapabilities, setSelectedCapabilities] = useState<string[]>([])
  const [tags, setTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')
  const [activeTab, setActiveTab] = useState<'basic' | 'advanced' | 'tools' | 'config'>('basic')

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors }
  } = useForm<CreateAgentFormData>({
    defaultValues: {
      configuration: {
        temperature: 0.7,
        max_tokens: 2000,
        timeout: 30
      },
      memory_config: {
        type: 'short_term',
        max_size: 1000,
        persistence: false
      },
      rate_limits: {
        requests_per_minute: 60,
        requests_per_hour: 1000
      },
      capabilities: [],
      tools: [],
      tags: []
    }
  })

  const selectedTemplate = watch('template_id')
  const memoryType = watch('memory_config.type')

  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      const updatedTags = [...tags, newTag.trim()]
      setTags(updatedTags)
      setValue('tags', updatedTags)
      setNewTag('')
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    const updatedTags = tags.filter(tag => tag !== tagToRemove)
    setTags(updatedTags)
    setValue('tags', updatedTags)
  }

  const handleToolToggle = (toolId: string) => {
    const updatedTools = selectedTools.includes(toolId)
      ? selectedTools.filter(id => id !== toolId)
      : [...selectedTools, toolId]
    setSelectedTools(updatedTools)
    setValue('tools', updatedTools)
  }

  const handleCapabilityToggle = (capability: string) => {
    const updatedCapabilities = selectedCapabilities.includes(capability)
      ? selectedCapabilities.filter(c => c !== capability)
      : [...selectedCapabilities, capability]
    setSelectedCapabilities(updatedCapabilities)
    setValue('capabilities', updatedCapabilities)
  }

  const onFormSubmit = (data: CreateAgentFormData) => {
    onSubmit({
      ...data,
      capabilities: selectedCapabilities,
      tools: selectedTools,
      tags
    })
  }

  const commonCapabilities = [
    'Natural Language Processing',
    'Code Generation',
    'Data Analysis',
    'Web Search',
    'File Processing',
    'Image Analysis',
    'Task Planning',
    'API Integration',
    'Database Operations',
    'Real-time Chat'
  ]

  const tabs = [
    { id: 'basic', name: 'Basic Info', icon: Settings },
    { id: 'advanced', name: 'Advanced', icon: Zap },
    { id: 'tools', name: 'Tools & Capabilities', icon: Shield },
    { id: 'config', name: 'Configuration', icon: Clock }
  ]

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Create New Agent</h2>
        <p className="text-gray-600">Set up a new AI agent with custom configuration and capabilities</p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.name}</span>
              </button>
            )
          })}
        </nav>
      </div>

      <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
        {/* Basic Information Tab */}
        {activeTab === 'basic' && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Basic Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Agent Name *</Label>
                <Input
                  id="name"
                  {...register('name', { required: 'Agent name is required' })}
                  placeholder="my-assistant-agent"
                />
                {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>}
              </div>

              <div>
                <Label htmlFor="display_name">Display Name *</Label>
                <Input
                  id="display_name"
                  {...register('display_name', { required: 'Display name is required' })}
                  placeholder="My Assistant Agent"
                />
                {errors.display_name && <p className="text-red-500 text-sm mt-1">{errors.display_name.message}</p>}
              </div>

              <div>
                <Label htmlFor="category_id">Category *</Label>
                <Select
                  id="category_id"
                  {...register('category_id', { required: 'Category is required' })}
                >
                  <option value="">Select a category</option>
                  {categories.map(category => (
                    <option key={category.id} value={category.id}>
                      {category.display_name}
                    </option>
                  ))}
                </Select>
                {errors.category_id && <p className="text-red-500 text-sm mt-1">{errors.category_id.message}</p>}
              </div>

              <div>
                <Label htmlFor="template_id">Template (Optional)</Label>
                <Select
                  id="template_id"
                  {...register('template_id')}
                >
                  <option value="">Select a template</option>
                  {templates.map(template => (
                    <option key={template.id} value={template.id}>
                      {template.display_name}
                    </option>
                  ))}
                </Select>
              </div>

              <div>
                <Label htmlFor="model_id">AI Model *</Label>
                <Select
                  id="model_id"
                  {...register('model_id', { required: 'Model is required' })}
                >
                  <option value="">Select a model</option>
                  {models.map(model => (
                    <option key={model.id} value={model.id}>
                      {model.display_name}
                    </option>
                  ))}
                </Select>
                {errors.model_id && <p className="text-red-500 text-sm mt-1">{errors.model_id.message}</p>}
              </div>
            </div>

            <div className="mt-4">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                {...register('description')}
                placeholder="Describe what this agent does..."
                rows={3}
              />
            </div>

            <div className="mt-4">
              <Label htmlFor="system_prompt">System Prompt *</Label>
              <Textarea
                id="system_prompt"
                {...register('system_prompt', { required: 'System prompt is required' })}
                placeholder="You are a helpful AI assistant..."
                rows={4}
              />
              {errors.system_prompt && <p className="text-red-500 text-sm mt-1">{errors.system_prompt.message}</p>}
            </div>

            {/* Tags */}
            <div className="mt-4">
              <Label>Tags</Label>
              <div className="flex flex-wrap gap-2 mb-2">
                {tags.map(tag => (
                  <Badge key={tag} variant="secondary" className="flex items-center gap-1">
                    {tag}
                    <X
                      className="w-3 h-3 cursor-pointer hover:text-red-500"
                      onClick={() => handleRemoveTag(tag)}
                    />
                  </Badge>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  placeholder="Add a tag..."
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                />
                <Button type="button" variant="outline" onClick={handleAddTag}>
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </Card>
        )}

        {/* Advanced Tab */}
        {activeTab === 'advanced' && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Advanced Settings</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Memory Configuration */}
              <div>
                <h4 className="font-medium mb-3">Memory Configuration</h4>
                <div className="space-y-3">
                  <div>
                    <Label htmlFor="memory_type">Memory Type</Label>
                    <Select
                      id="memory_type"
                      {...register('memory_config.type')}
                    >
                      <option value="short_term">Short Term</option>
                      <option value="long_term">Long Term</option>
                      <option value="hybrid">Hybrid</option>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="memory_size">Max Memory Size</Label>
                    <Input
                      id="memory_size"
                      type="number"
                      {...register('memory_config.max_size')}
                      placeholder="1000"
                    />
                  </div>

                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="persistence"
                      {...register('memory_config.persistence')}
                    />
                    <Label htmlFor="persistence">Enable Persistence</Label>
                  </div>
                </div>
              </div>

              {/* Rate Limits */}
              <div>
                <h4 className="font-medium mb-3">Rate Limits</h4>
                <div className="space-y-3">
                  <div>
                    <Label htmlFor="rpm">Requests per Minute</Label>
                    <Input
                      id="rpm"
                      type="number"
                      {...register('rate_limits.requests_per_minute')}
                      placeholder="60"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="rph">Requests per Hour</Label>
                    <Input
                      id="rph"
                      type="number"
                      {...register('rate_limits.requests_per_hour')}
                      placeholder="1000"
                    />
                  </div>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Tools & Capabilities Tab */}
        {activeTab === 'tools' && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Tools & Capabilities</h3>
            
            {/* Capabilities */}
            <div className="mb-6">
              <h4 className="font-medium mb-3">Capabilities</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {commonCapabilities.map(capability => (
                  <label key={capability} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={selectedCapabilities.includes(capability)}
                      onChange={() => handleCapabilityToggle(capability)}
                    />
                    <span className="text-sm">{capability}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Tools */}
            <div>
              <h4 className="font-medium mb-3">Available Tools</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {tools.map(tool => (
                  <div key={tool.id} className="border rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <h5 className="font-medium">{tool.name}</h5>
                        <p className="text-sm text-gray-600">{tool.description}</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={selectedTools.includes(tool.id)}
                        onChange={() => handleToolToggle(tool.id)}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        )}

        {/* Configuration Tab */}
        {activeTab === 'config' && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Model Configuration</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="temperature">Temperature</Label>
                <Input
                  id="temperature"
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  {...register('configuration.temperature')}
                />
                <p className="text-sm text-gray-500 mt-1">Controls randomness (0-2)</p>
              </div>

              <div>
                <Label htmlFor="max_tokens">Max Tokens</Label>
                <Input
                  id="max_tokens"
                  type="number"
                  {...register('configuration.max_tokens')}
                />
                <p className="text-sm text-gray-500 mt-1">Maximum response length</p>
              </div>

              <div>
                <Label htmlFor="timeout">Timeout (seconds)</Label>
                <Input
                  id="timeout"
                  type="number"
                  {...register('configuration.timeout')}
                />
                <p className="text-sm text-gray-500 mt-1">Request timeout</p>
              </div>
            </div>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="flex justify-end space-x-4 pt-6 border-t">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Creating...' : 'Create Agent'}
          </Button>
        </div>
      </form>
    </div>
  )
}
