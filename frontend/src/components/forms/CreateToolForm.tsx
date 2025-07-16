'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select } from '@/components/ui/select'
import { Card } from '@/components/ui/card'
import { CreateToolFormData } from '@/types/create-forms'
import { Wrench, Settings, Shield, Clock, Zap } from 'lucide-react'

interface CreateToolFormProps {
  onSubmit: (data: CreateToolFormData) => void
  onCancel: () => void
  isLoading?: boolean
}

export default function CreateToolForm({
  onSubmit,
  onCancel,
  isLoading = false
}: CreateToolFormProps) {
  const [activeTab, setActiveTab] = useState<'basic' | 'config' | 'auth' | 'limits'>('basic')

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors }
  } = useForm<CreateToolFormData>({
    defaultValues: {
      type: 'api',
      authentication: {
        type: 'none',
        config: {}
      },
      rate_limits: {
        requests_per_minute: 60,
        requests_per_hour: 1000
      },
      timeout_seconds: 30,
      retries: 3,
      config: {},
      schema_input: {},
      schema_output: {}
    }
  })

  const toolType = watch('type')
  const authType = watch('authentication.type')

  const toolTypes = [
    { value: 'api', label: 'API Tool', description: 'HTTP/REST API integration' },
    { value: 'function', label: 'Function Tool', description: 'Custom function execution' },
    { value: 'database', label: 'Database Tool', description: 'Database operations' },
    { value: 'file', label: 'File Tool', description: 'File system operations' },
    { value: 'webhook', label: 'Webhook Tool', description: 'Webhook handling' }
  ]

  const authTypes = [
    { value: 'none', label: 'No Authentication' },
    { value: 'api_key', label: 'API Key' },
    { value: 'oauth', label: 'OAuth 2.0' },
    { value: 'basic', label: 'Basic Auth' }
  ]

  const toolCategories = [
    'Communication',
    'Data Processing',
    'File Management',
    'Web Services',
    'Database',
    'Analytics',
    'Security',
    'Monitoring',
    'Integration',
    'Automation'
  ]

  const tabs = [
    { id: 'basic', name: 'Basic Info', icon: Settings },
    { id: 'config', name: 'Configuration', icon: Wrench },
    { id: 'auth', name: 'Authentication', icon: Shield },
    { id: 'limits', name: 'Limits & Timeout', icon: Clock }
  ]

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2 flex items-center gap-2">
          <Wrench className="w-6 h-6 text-blue-600" />
          Create New Tool
        </h2>
        <p className="text-gray-600">Create a new tool that agents can use to perform specific tasks</p>
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

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Information Tab */}
        {activeTab === 'basic' && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Basic Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Tool Name *</Label>
                <Input
                  id="name"
                  {...register('name', { required: 'Tool name is required' })}
                  placeholder="web-search-tool"
                />
                {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>}
              </div>

              <div>
                <Label htmlFor="type">Tool Type *</Label>
                <Select
                  id="type"
                  {...register('type', { required: 'Tool type is required' })}
                >
                  {toolTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </Select>
                {errors.type && <p className="text-red-500 text-sm mt-1">{errors.type.message}</p>}
              </div>

              <div>
                <Label htmlFor="category">Category</Label>
                <Select
                  id="category"
                  {...register('category')}
                >
                  <option value="">Select a category</option>
                  {toolCategories.map(category => (
                    <option key={category} value={category.toLowerCase().replace(' ', '_')}>
                      {category}
                    </option>
                  ))}
                </Select>
              </div>

              {toolType === 'api' && (
                <div>
                  <Label htmlFor="endpoint_url">Endpoint URL *</Label>
                  <Input
                    id="endpoint_url"
                    {...register('endpoint_url', { 
                      required: toolType === 'api' ? 'Endpoint URL is required for API tools' : false 
                    })}
                    placeholder="https://api.example.com/v1/search"
                  />
                  {errors.endpoint_url && <p className="text-red-500 text-sm mt-1">{errors.endpoint_url.message}</p>}
                </div>
              )}
            </div>

            <div className="mt-4">
              <Label htmlFor="description">Description *</Label>
              <Textarea
                id="description"
                {...register('description', { required: 'Description is required' })}
                placeholder="Describe what this tool does and how it works..."
                rows={3}
              />
              {errors.description && <p className="text-red-500 text-sm mt-1">{errors.description.message}</p>}
            </div>
          </Card>
        )}

        {/* Configuration Tab */}
        {activeTab === 'config' && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Configuration</h3>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="schema_input">Input Schema (JSON)</Label>
                <Textarea
                  id="schema_input"
                  {...register('schema_input')}
                  placeholder='{"type": "object", "properties": {"query": {"type": "string"}}}'
                  rows={4}
                />
                <p className="text-sm text-gray-500 mt-1">Define the expected input structure</p>
              </div>

              <div>
                <Label htmlFor="schema_output">Output Schema (JSON)</Label>
                <Textarea
                  id="schema_output"
                  {...register('schema_output')}
                  placeholder='{"type": "object", "properties": {"results": {"type": "array"}}}'
                  rows={4}
                />
                <p className="text-sm text-gray-500 mt-1">Define the expected output structure</p>
              </div>

              <div>
                <Label htmlFor="config">Additional Configuration (JSON)</Label>
                <Textarea
                  id="config"
                  {...register('config')}
                  placeholder='{"headers": {"User-Agent": "AgentMesh/1.0"}}'
                  rows={3}
                />
                <p className="text-sm text-gray-500 mt-1">Tool-specific configuration options</p>
              </div>
            </div>
          </Card>
        )}

        {/* Authentication Tab */}
        {activeTab === 'auth' && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Authentication</h3>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="auth_type">Authentication Type</Label>
                <Select
                  id="auth_type"
                  {...register('authentication.type')}
                >
                  {authTypes.map(auth => (
                    <option key={auth.value} value={auth.value}>
                      {auth.label}
                    </option>
                  ))}
                </Select>
              </div>

              {authType === 'api_key' && (
                <div>
                  <Label htmlFor="api_key_config">API Key Configuration</Label>
                  <Textarea
                    id="api_key_config"
                    {...register('authentication.config')}
                    placeholder='{"header": "X-API-Key", "prefix": "Bearer "}'
                    rows={3}
                  />
                  <p className="text-sm text-gray-500 mt-1">API key configuration settings</p>
                </div>
              )}

              {authType === 'oauth' && (
                <div>
                  <Label htmlFor="oauth_config">OAuth Configuration</Label>
                  <Textarea
                    id="oauth_config"
                    {...register('authentication.config')}
                    placeholder='{"client_id": "your-client-id", "scope": "read write"}'
                    rows={3}
                  />
                  <p className="text-sm text-gray-500 mt-1">OAuth 2.0 configuration settings</p>
                </div>
              )}

              {authType === 'basic' && (
                <div>
                  <Label htmlFor="basic_config">Basic Auth Configuration</Label>
                  <Textarea
                    id="basic_config"
                    {...register('authentication.config')}
                    placeholder='{"username_field": "username", "password_field": "password"}'
                    rows={3}
                  />
                  <p className="text-sm text-gray-500 mt-1">Basic authentication configuration</p>
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Limits & Timeout Tab */}
        {activeTab === 'limits' && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Limits & Timeout</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="timeout_seconds">Timeout (seconds)</Label>
                <Input
                  id="timeout_seconds"
                  type="number"
                  {...register('timeout_seconds')}
                  placeholder="30"
                />
                <p className="text-sm text-gray-500 mt-1">Request timeout in seconds</p>
              </div>

              <div>
                <Label htmlFor="retries">Retry Attempts</Label>
                <Input
                  id="retries"
                  type="number"
                  {...register('retries')}
                  placeholder="3"
                />
                <p className="text-sm text-gray-500 mt-1">Number of retry attempts on failure</p>
              </div>

              <div>
                <Label htmlFor="rpm">Requests per Minute</Label>
                <Input
                  id="rpm"
                  type="number"
                  {...register('rate_limits.requests_per_minute')}
                  placeholder="60"
                />
                <p className="text-sm text-gray-500 mt-1">Rate limit per minute</p>
              </div>

              <div>
                <Label htmlFor="rph">Requests per Hour</Label>
                <Input
                  id="rph"
                  type="number"
                  {...register('rate_limits.requests_per_hour')}
                  placeholder="1000"
                />
                <p className="text-sm text-gray-500 mt-1">Rate limit per hour</p>
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
            {isLoading ? 'Creating...' : 'Create Tool'}
          </Button>
        </div>
      </form>
    </div>
  )
}
