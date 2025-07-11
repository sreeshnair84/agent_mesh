'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/ui/Button'
import { Eye, EyeOff, Key, Plus, X, AlertTriangle, Shield } from 'lucide-react'
import { EnvironmentSecret } from './types'

interface SecretFormData {
  name: string
  description: string
  environment: string
  category: 'api_key' | 'database' | 'auth' | 'service' | 'webhook' | 'other'
  key: string
  value: string
  encrypted: boolean
  accessLevel: 'public' | 'internal' | 'restricted' | 'confidential'
  tags: string[]
  expiresAt?: Date
}

interface SecretFormProps {
  secret?: EnvironmentSecret | null
  environments: string[]
  onSubmit: (data: SecretFormData) => void
  onCancel: () => void
  isLoading: boolean
}

const SECRET_CATEGORIES = [
  { value: 'api_key', label: 'API Key', description: 'External service API keys' },
  { value: 'database', label: 'Database', description: 'Database connection strings' },
  { value: 'auth', label: 'Authentication', description: 'Auth tokens and certificates' },
  { value: 'service', label: 'Service', description: 'Service-specific configurations' },
  { value: 'webhook', label: 'Webhook', description: 'Webhook URLs and secrets' },
  { value: 'other', label: 'Other', description: 'Other secret types' }
]

const ACCESS_LEVELS = [
  { value: 'public', label: 'Public', description: 'Can be accessed by anyone' },
  { value: 'internal', label: 'Internal', description: 'Internal team access only' },
  { value: 'restricted', label: 'Restricted', description: 'Limited access with approval' },
  { value: 'confidential', label: 'Confidential', description: 'Highly restricted access' }
]

export function SecretForm({ secret, environments, onSubmit, onCancel, isLoading }: SecretFormProps) {
  const [showValue, setShowValue] = useState(false)
  const [tagInput, setTagInput] = useState('')
  const [tags, setTags] = useState<string[]>(secret?.tags || [])
  const [hasExpiration, setHasExpiration] = useState(!!secret?.expiresAt)

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors }
  } = useForm<SecretFormData>({
    defaultValues: {
      name: secret?.name || '',
      description: secret?.description || '',
      environment: secret?.environment || (environments[0] || ''),
      category: secret?.category || 'api_key',
      key: secret?.key || '',
      value: secret?.value || '',
      encrypted: secret?.encrypted ?? true,
      accessLevel: secret?.accessLevel || 'internal',
      tags: secret?.tags || [],
      expiresAt: secret?.expiresAt ? new Date(secret.expiresAt) : undefined
    }
  })

  const watchedCategory = watch('category')
  const watchedAccessLevel = watch('accessLevel')

  useEffect(() => {
    setValue('tags', tags)
  }, [tags, setValue])

  const addTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()])
      setTagInput('')
    }
  }

  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addTag()
    }
  }

  const generateSecretKey = () => {
    const category = watchedCategory
    const timestamp = Date.now()
    const random = Math.random().toString(36).substring(2, 8)
    const key = `${category.toUpperCase()}_${timestamp}_${random}`
    setValue('key', key)
  }

  const onSubmitForm = (data: SecretFormData) => {
    const submitData = {
      ...data,
      tags,
      expiresAt: hasExpiration ? data.expiresAt : undefined
    }
    onSubmit(submitData)
  }

  const selectedCategory = SECRET_CATEGORIES.find(c => c.value === watchedCategory)
  const selectedAccessLevel = ACCESS_LEVELS.find(a => a.value === watchedAccessLevel)

  return (
    <form onSubmit={handleSubmit(onSubmitForm)} className="space-y-6">
      {/* Basic Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
            Secret Name *
          </label>
          <input
            {...register('name', { required: 'Name is required' })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            placeholder="e.g., OpenAI API Key"
          />
          {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>}
        </div>

        <div>
          <label htmlFor="environment" className="block text-sm font-medium text-gray-700 mb-2">
            Environment *
          </label>
          <select
            {...register('environment', { required: 'Environment is required' })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            {environments.map(env => (
              <option key={env} value={env}>{env}</option>
            ))}
          </select>
          {errors.environment && <p className="mt-1 text-sm text-red-600">{errors.environment.message}</p>}
        </div>
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
          Description
        </label>
        <textarea
          {...register('description')}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          placeholder="Describe what this secret is used for..."
        />
      </div>

      {/* Category and Access Level */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
            Category *
          </label>
          <select
            {...register('category', { required: 'Category is required' })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            {SECRET_CATEGORIES.map(category => (
              <option key={category.value} value={category.value}>
                {category.label}
              </option>
            ))}
          </select>
          {selectedCategory && (
            <p className="mt-1 text-xs text-gray-500">{selectedCategory.description}</p>
          )}
          {errors.category && <p className="mt-1 text-sm text-red-600">{errors.category.message}</p>}
        </div>

        <div>
          <label htmlFor="accessLevel" className="block text-sm font-medium text-gray-700 mb-2">
            Access Level *
          </label>
          <select
            {...register('accessLevel', { required: 'Access level is required' })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            {ACCESS_LEVELS.map(level => (
              <option key={level.value} value={level.value}>
                {level.label}
              </option>
            ))}
          </select>
          {selectedAccessLevel && (
            <p className="mt-1 text-xs text-gray-500">{selectedAccessLevel.description}</p>
          )}
          {errors.accessLevel && <p className="mt-1 text-sm text-red-600">{errors.accessLevel.message}</p>}
        </div>
      </div>

      {/* Key and Value */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="key" className="block text-sm font-medium text-gray-700 mb-2">
            Secret Key *
          </label>
          <div className="flex space-x-2">
            <input
              {...register('key', { required: 'Key is required' })}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono"
              placeholder="ENVIRONMENT_VARIABLE_NAME"
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={generateSecretKey}
              className="px-3"
            >
              <Key className="h-4 w-4" />
            </Button>
          </div>
          {errors.key && <p className="mt-1 text-sm text-red-600">{errors.key.message}</p>}
        </div>

        <div>
          <label htmlFor="value" className="block text-sm font-medium text-gray-700 mb-2">
            Secret Value *
          </label>
          <div className="flex space-x-2">
            <input
              {...register('value', { required: 'Value is required' })}
              type={showValue ? 'text' : 'password'}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono"
              placeholder="Enter the secret value"
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowValue(!showValue)}
              className="px-3"
            >
              {showValue ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </Button>
          </div>
          {errors.value && <p className="mt-1 text-sm text-red-600">{errors.value.message}</p>}
        </div>
      </div>

      {/* Security Options */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex items-center mb-3">
          <Shield className="h-5 w-5 text-gray-400 mr-2" />
          <h3 className="text-sm font-medium text-gray-900">Security Options</h3>
        </div>
        
        <div className="space-y-3">
          <div className="flex items-center">
            <input
              {...register('encrypted')}
              type="checkbox"
              className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
            />
            <label htmlFor="encrypted" className="ml-2 block text-sm text-gray-900">
              Encrypt value at rest
            </label>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              checked={hasExpiration}
              onChange={(e) => setHasExpiration(e.target.checked)}
              className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
            />
            <label className="ml-2 block text-sm text-gray-900">
              Set expiration date
            </label>
          </div>

          {hasExpiration && (
            <div className="ml-6">
              <label htmlFor="expiresAt" className="block text-sm font-medium text-gray-700 mb-1">
                Expires At
              </label>
              <input
                {...register('expiresAt')}
                type="datetime-local"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
          )}
        </div>
      </div>

      {/* Tags */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tags
        </label>
        <div className="flex flex-wrap gap-2 mb-2">
          {tags.map(tag => (
            <span
              key={tag}
              className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800"
            >
              {tag}
              <button
                type="button"
                onClick={() => removeTag(tag)}
                className="ml-1 hover:text-purple-600"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>
        <div className="flex space-x-2">
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Add a tag..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addTag}
            disabled={!tagInput.trim()}
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Security Warning */}
      {watchedAccessLevel === 'confidential' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <AlertTriangle className="h-5 w-5 text-red-400 mr-2 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-red-800">High Security Secret</h3>
              <p className="text-sm text-red-700 mt-1">
                This secret is marked as confidential. It will have restricted access and require additional approvals for usage.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Form Actions */}
      <div className="flex justify-end space-x-4 pt-4 border-t">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isLoading}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={isLoading}
          className="bg-purple-600 hover:bg-purple-700"
        >
          {isLoading ? 'Saving...' : secret ? 'Update Secret' : 'Create Secret'}
        </Button>
      </div>
    </form>
  )
}
