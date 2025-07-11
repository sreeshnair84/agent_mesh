'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/ui/Button'
import { X, Plus, Eye, Code } from 'lucide-react'

interface PromptVariable {
  name: string
  type: 'string' | 'number' | 'boolean' | 'array'
  description: string
  required: boolean
  defaultValue?: any
}

interface PromptFormData {
  name: string
  content: string
  version: string
  description?: string
  tags: string[]
  type: 'system' | 'user' | 'assistant' | 'function'
  category: string
  variables: PromptVariable[]
  status: 'active' | 'inactive' | 'draft'
  isTemplate: boolean
}

interface PromptFormProps {
  initialData?: Partial<PromptFormData>
  onSubmit: (data: PromptFormData) => void
  onCancel: () => void
  isLoading?: boolean
}

export function PromptForm({ 
  initialData, 
  onSubmit, 
  onCancel, 
  isLoading 
}: PromptFormProps) {
  const [tags, setTags] = useState<string[]>(initialData?.tags || [])
  const [newTag, setNewTag] = useState('')
  const [variables, setVariables] = useState<PromptVariable[]>(initialData?.variables || [])
  const [showPreview, setShowPreview] = useState(false)
  const [previewVariables, setPreviewVariables] = useState<Record<string, any>>({})

  const { register, handleSubmit, formState: { errors }, watch } = useForm<PromptFormData>({
    defaultValues: initialData as PromptFormData
  })

  const watchedContent = watch('content')

  const addTag = () => {
    if (newTag && !tags.includes(newTag)) {
      setTags([...tags, newTag])
      setNewTag('')
    }
  }

  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove))
  }

  const addVariable = () => {
    const newVariable: PromptVariable = {
      name: '',
      type: 'string',
      description: '',
      required: false,
      defaultValue: ''
    }
    setVariables([...variables, newVariable])
  }

  const updateVariable = (index: number, field: keyof PromptVariable, value: any) => {
    const updatedVariables = [...variables]
    updatedVariables[index] = { ...updatedVariables[index], [field]: value }
    setVariables(updatedVariables)
  }

  const removeVariable = (index: number) => {
    setVariables(variables.filter((_, i) => i !== index))
  }

  const handlePreviewVariableChange = (name: string, value: any) => {
    setPreviewVariables(prev => ({ ...prev, [name]: value }))
  }

  const renderPreview = () => {
    let content = watchedContent || ''
    variables.forEach(variable => {
      const value = previewVariables[variable.name] || variable.defaultValue || `{${variable.name}}`
      content = content.replace(new RegExp(`{{${variable.name}}}`, 'g'), value)
    })
    return content
  }

  const onSubmitForm = (data: PromptFormData) => {
    onSubmit({
      ...data,
      tags,
      variables
    })
  }

  const promptTypes = [
    { value: 'system', label: 'System' },
    { value: 'user', label: 'User' },
    { value: 'assistant', label: 'Assistant' },
    { value: 'function', label: 'Function' },
  ]

  const categories = [
    'General',
    'Analysis',
    'Code Generation',
    'Content Creation',
    'Conversation',
    'Decision Making',
    'Problem Solving',
    'Custom'
  ]

  const variableTypes = [
    { value: 'string', label: 'String' },
    { value: 'number', label: 'Number' },
    { value: 'boolean', label: 'Boolean' },
    { value: 'array', label: 'Array' },
  ]

  return (
    <div className="space-y-6">
      {/* Header with Preview Toggle */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">
          {initialData ? 'Edit Prompt' : 'Create New Prompt'}
        </h3>
        <Button
          type="button"
          variant="outline"
          onClick={() => setShowPreview(!showPreview)}
        >
          {showPreview ? <Code className="w-4 h-4 mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
          {showPreview ? 'Edit' : 'Preview'}
        </Button>
      </div>

      {!showPreview ? (
        <form onSubmit={handleSubmit(onSubmitForm)} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Name *
              </label>
              <input
                {...register('name', { required: 'Name is required' })}
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Enter prompt name"
              />
              {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>}
            </div>

            <div>
              <label htmlFor="version" className="block text-sm font-medium text-gray-700 mb-2">
                Version *
              </label>
              <input
                {...register('version', { required: 'Version is required' })}
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="e.g., 1.0.0"
              />
              {errors.version && <p className="mt-1 text-sm text-red-600">{errors.version.message}</p>}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="type" className="block text-sm font-medium text-gray-700 mb-2">
                Type *
              </label>
              <select
                {...register('type', { required: 'Type is required' })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Select type</option>
                {promptTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
              {errors.type && <p className="mt-1 text-sm text-red-600">{errors.type.message}</p>}
            </div>

            <div>
              <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
                Category *
              </label>
              <select
                {...register('category', { required: 'Category is required' })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Select category</option>
                {categories.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
              {errors.category && <p className="mt-1 text-sm text-red-600">{errors.category.message}</p>}
            </div>
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              {...register('description')}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="Describe what this prompt does"
            />
          </div>

          <div>
            <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-2">
              Content *
            </label>
            <textarea
              {...register('content', { required: 'Content is required' })}
              rows={10}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono"
              placeholder="Enter your prompt content here... Use {{variable}} for variables"
            />
            {errors.content && <p className="mt-1 text-sm text-red-600">{errors.content.message}</p>}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <select
                {...register('status')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="draft">Draft</option>
              </select>
            </div>

            <div className="flex items-center space-x-2 pt-8">
              <input
                {...register('isTemplate')}
                type="checkbox"
                className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
              />
              <label className="text-sm font-medium text-gray-700">
                Is Template
              </label>
            </div>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
            <div className="flex flex-wrap gap-2 mb-2">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-purple-100 text-purple-800"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => removeTag(tag)}
                    className="ml-1 hover:text-purple-600"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                placeholder="Add a tag"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <Button type="button" onClick={addTag} size="sm" variant="outline">
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Variables */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <label className="block text-sm font-medium text-gray-700">
                Variables
              </label>
              <Button type="button" onClick={addVariable} size="sm" variant="outline">
                <Plus className="w-4 h-4 mr-2" />
                Add Variable
              </Button>
            </div>

            <div className="space-y-4">
              {variables.map((variable, index) => (
                <div key={index} className="border rounded-lg p-4 bg-gray-50">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Variable Name
                      </label>
                      <input
                        type="text"
                        value={variable.name}
                        onChange={(e) => updateVariable(index, 'name', e.target.value)}
                        placeholder="e.g., userName"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Type
                      </label>
                      <select
                        value={variable.type}
                        onChange={(e) => updateVariable(index, 'type', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                      >
                        {variableTypes.map((type) => (
                          <option key={type.value} value={type.value}>
                            {type.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Description
                      </label>
                      <input
                        type="text"
                        value={variable.description}
                        onChange={(e) => updateVariable(index, 'description', e.target.value)}
                        placeholder="Describe this variable"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Default Value
                      </label>
                      <input
                        type="text"
                        value={variable.defaultValue}
                        onChange={(e) => updateVariable(index, 'defaultValue', e.target.value)}
                        placeholder="Optional default value"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                  </div>
                  <div className="flex items-center justify-between mt-4">
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={variable.required}
                        onChange={(e) => updateVariable(index, 'required', e.target.checked)}
                        className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                      />
                      <label className="text-sm font-medium text-gray-700">
                        Required
                      </label>
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => removeVariable(index)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>

            {variables.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                No variables defined. Variables allow dynamic content in your prompts.
              </div>
            )}
          </div>

          <div className="flex justify-end space-x-3">
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Saving...' : 'Save Prompt'}
            </Button>
          </div>
        </form>
      ) : (
        <div className="space-y-6">
          {/* Preview Variables */}
          {variables.length > 0 && (
            <div>
              <h4 className="text-lg font-medium mb-4">Test Variables</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {variables.map((variable) => (
                  <div key={variable.name}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {variable.name}
                      {variable.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    <input
                      type={variable.type === 'number' ? 'number' : 'text'}
                      value={previewVariables[variable.name] || variable.defaultValue || ''}
                      onChange={(e) => handlePreviewVariableChange(variable.name, e.target.value)}
                      placeholder={variable.description}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Preview */}
          <div>
            <h4 className="text-lg font-medium mb-4">Preview</h4>
            <div className="bg-gray-50 p-4 rounded-lg border">
              <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
                {renderPreview()}
              </pre>
            </div>
          </div>

          <div className="flex justify-end space-x-3">
            <Button type="button" variant="outline" onClick={() => setShowPreview(false)}>
              Back to Edit
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
