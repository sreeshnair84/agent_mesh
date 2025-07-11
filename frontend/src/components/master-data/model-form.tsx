'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/ui/Button'
import { X, Plus, Eye, EyeOff } from 'lucide-react'

interface ModelFormData {
  name: string
  provider: string
  modelType: 'llm' | 'embedding' | 'vision' | 'audio' | 'custom'
  description?: string
  tags: string[]
  status: 'active' | 'inactive' | 'testing' | 'deprecated'
  config: {
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
  costs: {
    inputCostPer1kTokens: number
    outputCostPer1kTokens: number
  }
}

interface ModelFormProps {
  initialData?: Partial<ModelFormData>
  onSubmit: (data: ModelFormData) => void
  onCancel: () => void
  isLoading?: boolean
}

export function ModelForm({ 
  initialData, 
  onSubmit, 
  onCancel, 
  isLoading 
}: ModelFormProps) {
  const [tags, setTags] = useState<string[]>(initialData?.tags || [])
  const [newTag, setNewTag] = useState('')
  const [headers, setHeaders] = useState<Record<string, string>>(initialData?.config?.headers || {})
  const [newHeaderKey, setNewHeaderKey] = useState('')
  const [newHeaderValue, setNewHeaderValue] = useState('')
  const [showApiKey, setShowApiKey] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<ModelFormData>({
    defaultValues: initialData as ModelFormData
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

  const addHeader = () => {
    if (newHeaderKey && newHeaderValue) {
      setHeaders({ ...headers, [newHeaderKey]: newHeaderValue })
      setNewHeaderKey('')
      setNewHeaderValue('')
    }
  }

  const removeHeader = (keyToRemove: string) => {
    const updatedHeaders = { ...headers }
    delete updatedHeaders[keyToRemove]
    setHeaders(updatedHeaders)
  }

  const onSubmitForm = (data: ModelFormData) => {
    onSubmit({
      ...data,
      tags,
      config: {
        ...data.config,
        headers
      }
    })
  }

  const providers = [
    'OpenAI',
    'Anthropic',
    'Google',
    'Cohere',
    'Hugging Face',
    'Azure OpenAI',
    'AWS Bedrock',
    'Custom'
  ]

  const modelTypes = [
    { value: 'llm', label: 'Large Language Model' },
    { value: 'embedding', label: 'Embedding Model' },
    { value: 'vision', label: 'Vision Model' },
    { value: 'audio', label: 'Audio Model' },
    { value: 'custom', label: 'Custom Model' },
  ]

  return (
    <form onSubmit={handleSubmit(onSubmitForm)} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
            Model Name *
          </label>
          <input
            {...register('name', { required: 'Model name is required' })}
            type="text"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="e.g., GPT-4 Turbo"
          />
          {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>}
        </div>

        <div>
          <label htmlFor="provider" className="block text-sm font-medium text-gray-700 mb-2">
            Provider *
          </label>
          <select
            {...register('provider', { required: 'Provider is required' })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="">Select provider</option>
            {providers.map((provider) => (
              <option key={provider} value={provider}>
                {provider}
              </option>
            ))}
          </select>
          {errors.provider && <p className="mt-1 text-sm text-red-600">{errors.provider.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label htmlFor="modelType" className="block text-sm font-medium text-gray-700 mb-2">
            Model Type *
          </label>
          <select
            {...register('modelType', { required: 'Model type is required' })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="">Select type</option>
            {modelTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          {errors.modelType && <p className="mt-1 text-sm text-red-600">{errors.modelType.message}</p>}
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
            <option value="testing">Testing</option>
            <option value="deprecated">Deprecated</option>
          </select>
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
          placeholder="Describe this model configuration"
        />
      </div>

      {/* Configuration */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-gray-900">Configuration</h3>
        
        <div>
          <label htmlFor="config.endpoint" className="block text-sm font-medium text-gray-700 mb-2">
            API Endpoint *
          </label>
          <input
            {...register('config.endpoint', { required: 'API endpoint is required' })}
            type="url"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="https://api.openai.com/v1/chat/completions"
          />
          {errors.config?.endpoint && <p className="mt-1 text-sm text-red-600">{errors.config.endpoint.message}</p>}
        </div>

        <div>
          <label htmlFor="config.apiKey" className="block text-sm font-medium text-gray-700 mb-2">
            API Key *
          </label>
          <div className="relative">
            <input
              {...register('config.apiKey', { required: 'API key is required' })}
              type={showApiKey ? 'text' : 'password'}
              className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="Enter your API key"
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          {errors.config?.apiKey && <p className="mt-1 text-sm text-red-600">{errors.config.apiKey.message}</p>}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="config.maxTokens" className="block text-sm font-medium text-gray-700 mb-2">
              Max Tokens *
            </label>
            <input
              {...register('config.maxTokens', { 
                required: 'Max tokens is required',
                valueAsNumber: true,
                min: { value: 1, message: 'Must be at least 1' }
              })}
              type="number"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="4096"
            />
            {errors.config?.maxTokens && <p className="mt-1 text-sm text-red-600">{errors.config.maxTokens.message}</p>}
          </div>

          <div>
            <label htmlFor="config.temperature" className="block text-sm font-medium text-gray-700 mb-2">
              Temperature *
            </label>
            <input
              {...register('config.temperature', { 
                required: 'Temperature is required',
                valueAsNumber: true,
                min: { value: 0, message: 'Must be at least 0' },
                max: { value: 2, message: 'Must be at most 2' }
              })}
              type="number"
              step="0.1"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="0.7"
            />
            {errors.config?.temperature && <p className="mt-1 text-sm text-red-600">{errors.config.temperature.message}</p>}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="config.topP" className="block text-sm font-medium text-gray-700 mb-2">
              Top P
            </label>
            <input
              {...register('config.topP', { 
                valueAsNumber: true,
                min: { value: 0, message: 'Must be at least 0' },
                max: { value: 1, message: 'Must be at most 1' }
              })}
              type="number"
              step="0.1"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="1.0"
            />
          </div>

          <div>
            <label htmlFor="config.frequencyPenalty" className="block text-sm font-medium text-gray-700 mb-2">
              Frequency Penalty
            </label>
            <input
              {...register('config.frequencyPenalty', { 
                valueAsNumber: true,
                min: { value: -2, message: 'Must be at least -2' },
                max: { value: 2, message: 'Must be at most 2' }
              })}
              type="number"
              step="0.1"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="0"
            />
          </div>

          <div>
            <label htmlFor="config.presencePenalty" className="block text-sm font-medium text-gray-700 mb-2">
              Presence Penalty
            </label>
            <input
              {...register('config.presencePenalty', { 
                valueAsNumber: true,
                min: { value: -2, message: 'Must be at least -2' },
                max: { value: 2, message: 'Must be at most 2' }
              })}
              type="number"
              step="0.1"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="0"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="config.timeout" className="block text-sm font-medium text-gray-700 mb-2">
              Timeout (seconds)
            </label>
            <input
              {...register('config.timeout', { 
                valueAsNumber: true,
                min: { value: 1, message: 'Must be at least 1' }
              })}
              type="number"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="30"
            />
          </div>

          <div>
            <label htmlFor="config.retries" className="block text-sm font-medium text-gray-700 mb-2">
              Retries
            </label>
            <input
              {...register('config.retries', { 
                valueAsNumber: true,
                min: { value: 0, message: 'Must be at least 0' }
              })}
              type="number"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="3"
            />
          </div>
        </div>
      </div>

      {/* Cost Configuration */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-gray-900">Cost Configuration</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="costs.inputCostPer1kTokens" className="block text-sm font-medium text-gray-700 mb-2">
              Input Cost per 1K Tokens ($) *
            </label>
            <input
              {...register('costs.inputCostPer1kTokens', { 
                required: 'Input cost is required',
                valueAsNumber: true,
                min: { value: 0, message: 'Must be at least 0' }
              })}
              type="number"
              step="0.0001"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="0.01"
            />
            {errors.costs?.inputCostPer1kTokens && <p className="mt-1 text-sm text-red-600">{errors.costs.inputCostPer1kTokens.message}</p>}
          </div>

          <div>
            <label htmlFor="costs.outputCostPer1kTokens" className="block text-sm font-medium text-gray-700 mb-2">
              Output Cost per 1K Tokens ($) *
            </label>
            <input
              {...register('costs.outputCostPer1kTokens', { 
                required: 'Output cost is required',
                valueAsNumber: true,
                min: { value: 0, message: 'Must be at least 0' }
              })}
              type="number"
              step="0.0001"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="0.03"
            />
            {errors.costs?.outputCostPer1kTokens && <p className="mt-1 text-sm text-red-600">{errors.costs.outputCostPer1kTokens.message}</p>}
          </div>
        </div>
      </div>

      {/* Custom Headers */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Custom Headers</label>
        <div className="space-y-2 mb-4">
          {Object.entries(headers).map(([key, value]) => (
            <div key={key} className="flex items-center space-x-2">
              <input
                type="text"
                value={key}
                readOnly
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                placeholder="Header name"
              />
              <input
                type="text"
                value={value}
                readOnly
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                placeholder="Header value"
              />
              <button
                type="button"
                onClick={() => removeHeader(key)}
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
            value={newHeaderKey}
            onChange={(e) => setNewHeaderKey(e.target.value)}
            placeholder="Header name"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <input
            type="text"
            value={newHeaderValue}
            onChange={(e) => setNewHeaderValue(e.target.value)}
            placeholder="Header value"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <Button type="button" onClick={addHeader} size="sm" variant="outline">
            <Plus className="w-4 h-4" />
          </Button>
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

      <div className="flex justify-end space-x-3">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Saving...' : 'Save Model'}
        </Button>
      </div>
    </form>
  )
}
