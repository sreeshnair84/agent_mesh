'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/ui/Button'
import { X, Plus } from 'lucide-react'

interface SkillFormData {
  name: string
  description: string
  category: string
  tags: string[]
  status: 'active' | 'inactive' | 'draft'
  dependencies?: string[]
  examples?: string[]
}

interface SkillFormProps {
  initialData?: Partial<SkillFormData>
  onSubmit: (data: SkillFormData) => void
  onCancel: () => void
  isLoading?: boolean
}

export function SkillForm({ initialData, onSubmit, onCancel, isLoading }: SkillFormProps) {
  const [tags, setTags] = useState<string[]>(initialData?.tags || [])
  const [newTag, setNewTag] = useState('')
  const [dependencies, setDependencies] = useState<string[]>(initialData?.dependencies || [])
  const [newDependency, setNewDependency] = useState('')
  const [examples, setExamples] = useState<string[]>(initialData?.examples || [])
  const [newExample, setNewExample] = useState('')

  const { register, handleSubmit, formState: { errors } } = useForm<SkillFormData>({
    defaultValues: initialData as SkillFormData
  })

  const addTag = () => {
    if (newTag && !tags.includes(newTag)) {
      setTags([...tags, newTag])
      setNewTag('')
    }
  }

  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove))
  }

  const addDependency = () => {
    if (newDependency && !dependencies.includes(newDependency)) {
      setDependencies([...dependencies, newDependency])
      setNewDependency('')
    }
  }

  const removeDependency = (depToRemove: string) => {
    setDependencies(dependencies.filter(dep => dep !== depToRemove))
  }

  const addExample = () => {
    if (newExample && !examples.includes(newExample)) {
      setExamples([...examples, newExample])
      setNewExample('')
    }
  }

  const removeExample = (exampleToRemove: string) => {
    setExamples(examples.filter(example => example !== exampleToRemove))
  }

  const onSubmitForm = (data: SkillFormData) => {
    onSubmit({
      ...data,
      tags,
      dependencies,
      examples
    })
  }

  return (
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
            placeholder="Enter skill name"
          />
          {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>}
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
            <option value="communication">Communication</option>
            <option value="analysis">Analysis</option>
            <option value="automation">Automation</option>
            <option value="integration">Integration</option>
            <option value="custom">Custom</option>
          </select>
          {errors.category && <p className="mt-1 text-sm text-red-600">{errors.category.message}</p>}
        </div>
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
          Description *
        </label>
        <textarea
          {...register('description', { required: 'Description is required' })}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
          placeholder="Describe what this skill does"
        />
        {errors.description && <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>}
      </div>

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

      {/* Dependencies */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Dependencies</label>
        <div className="flex flex-wrap gap-2 mb-2">
          {dependencies.map((dep) => (
            <span
              key={dep}
              className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800"
            >
              {dep}
              <button
                type="button"
                onClick={() => removeDependency(dep)}
                className="ml-1 hover:text-blue-600"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={newDependency}
            onChange={(e) => setNewDependency(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addDependency())}
            placeholder="Add a dependency"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <Button type="button" onClick={addDependency} size="sm" variant="outline">
            <Plus className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Examples */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Examples</label>
        <div className="space-y-2 mb-2">
          {examples.map((example, index) => (
            <div key={index} className="flex items-center gap-2">
              <input
                type="text"
                value={example}
                readOnly
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
              />
              <button
                type="button"
                onClick={() => removeExample(example)}
                className="text-red-500 hover:text-red-700"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={newExample}
            onChange={(e) => setNewExample(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addExample())}
            placeholder="Add an example"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <Button type="button" onClick={addExample} size="sm" variant="outline">
            <Plus className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div className="flex justify-end space-x-3">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Saving...' : 'Save Skill'}
        </Button>
      </div>
    </form>
  )
}
