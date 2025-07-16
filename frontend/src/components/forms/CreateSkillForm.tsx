'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select } from '@/components/ui/select'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/Badge'
import { CreateSkillFormData } from '@/types/create-forms'
import { Plus, X, Code, Brain, Zap } from 'lucide-react'

interface CreateSkillFormProps {
  onSubmit: (data: CreateSkillFormData) => void
  onCancel: () => void
  isLoading?: boolean
}

export default function CreateSkillForm({
  onSubmit,
  onCancel,
  isLoading = false
}: CreateSkillFormProps) {
  const [tags, setTags] = useState<string[]>([])
  const [dependencies, setDependencies] = useState<string[]>([])
  const [examples, setExamples] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')
  const [newDependency, setNewDependency] = useState('')
  const [newExample, setNewExample] = useState('')

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors }
  } = useForm<CreateSkillFormData>({
    defaultValues: {
      config: {},
      tags: [],
      dependencies: [],
      examples: []
    }
  })

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

  const handleAddDependency = () => {
    if (newDependency.trim() && !dependencies.includes(newDependency.trim())) {
      const updatedDeps = [...dependencies, newDependency.trim()]
      setDependencies(updatedDeps)
      setValue('dependencies', updatedDeps)
      setNewDependency('')
    }
  }

  const handleRemoveDependency = (depToRemove: string) => {
    const updatedDeps = dependencies.filter(dep => dep !== depToRemove)
    setDependencies(updatedDeps)
    setValue('dependencies', updatedDeps)
  }

  const handleAddExample = () => {
    if (newExample.trim() && !examples.includes(newExample.trim())) {
      const updatedExamples = [...examples, newExample.trim()]
      setExamples(updatedExamples)
      setValue('examples', updatedExamples)
      setNewExample('')
    }
  }

  const handleRemoveExample = (exampleToRemove: string) => {
    const updatedExamples = examples.filter(example => example !== exampleToRemove)
    setExamples(updatedExamples)
    setValue('examples', updatedExamples)
  }

  const onFormSubmit = (data: CreateSkillFormData) => {
    onSubmit({
      ...data,
      tags,
      dependencies,
      examples
    })
  }

  const skillCategories = [
    'Development',
    'Data Analysis',
    'Communication',
    'Research',
    'Content Creation',
    'API Integration',
    'File Processing',
    'Database',
    'Machine Learning',
    'Automation'
  ]

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2 flex items-center gap-2">
          <Brain className="w-6 h-6 text-blue-600" />
          Create New Skill
        </h2>
        <p className="text-gray-600">Define a reusable skill that agents can use</p>
      </div>

      <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Code className="w-5 h-5" />
            Basic Information
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">Skill Name *</Label>
              <Input
                id="name"
                {...register('name', { required: 'Skill name is required' })}
                placeholder="web_search"
              />
              {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>}
            </div>

            <div>
              <Label htmlFor="category">Category *</Label>
              <Select
                id="category"
                {...register('category', { required: 'Category is required' })}
              >
                <option value="">Select a category</option>
                {skillCategories.map(category => (
                  <option key={category} value={category.toLowerCase().replace(' ', '_')}>
                    {category}
                  </option>
                ))}
              </Select>
              {errors.category && <p className="text-red-500 text-sm mt-1">{errors.category.message}</p>}
            </div>
          </div>

          <div className="mt-4">
            <Label htmlFor="description">Description *</Label>
            <Textarea
              id="description"
              {...register('description', { required: 'Description is required' })}
              placeholder="Describe what this skill does and how it can be used..."
              rows={3}
            />
            {errors.description && <p className="text-red-500 text-sm mt-1">{errors.description.message}</p>}
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5" />
            Configuration & Metadata
          </h3>

          {/* Tags */}
          <div className="mb-4">
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

          {/* Dependencies */}
          <div className="mb-4">
            <Label>Dependencies</Label>
            <div className="flex flex-wrap gap-2 mb-2">
              {dependencies.map(dep => (
                <Badge key={dep} variant="outline" className="flex items-center gap-1">
                  {dep}
                  <X
                    className="w-3 h-3 cursor-pointer hover:text-red-500"
                    onClick={() => handleRemoveDependency(dep)}
                  />
                </Badge>
              ))}
            </div>
            <div className="flex gap-2">
              <Input
                value={newDependency}
                onChange={(e) => setNewDependency(e.target.value)}
                placeholder="Add a dependency..."
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddDependency())}
              />
              <Button type="button" variant="outline" onClick={handleAddDependency}>
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Examples */}
          <div>
            <Label>Usage Examples</Label>
            <div className="space-y-2 mb-2">
              {examples.map((example, index) => (
                <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                  <span className="flex-1 text-sm">{example}</span>
                  <X
                    className="w-4 h-4 cursor-pointer hover:text-red-500"
                    onClick={() => handleRemoveExample(example)}
                  />
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <Input
                value={newExample}
                onChange={(e) => setNewExample(e.target.value)}
                placeholder="Add usage example..."
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddExample())}
              />
              <Button type="button" variant="outline" onClick={handleAddExample}>
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-4 pt-6 border-t">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Creating...' : 'Create Skill'}
          </Button>
        </div>
      </form>
    </div>
  )
}
