'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useState } from 'react'
import { ArrowLeft, ArrowRight, Plus, X } from 'lucide-react'
import { useRouter } from 'next/navigation'

const toolSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  type: z.enum(['mcp', 'custom']),
  version: z.string().min(1, 'Version is required'),
  category: z.string().min(1, 'Category is required'),
  tags: z.array(z.string()),
  configuration: z.object({
    endpoint: z.string().url('Must be a valid URL').optional(),
    authentication: z.object({
      type: z.enum(['none', 'bearer', 'apikey', 'oauth']),
      token: z.string().optional(),
      apiKey: z.string().optional(),
    }).optional(),
    parameters: z.array(z.object({
      name: z.string(),
      type: z.string(),
      required: z.boolean(),
      description: z.string(),
    })),
  }),
  mcpConfig: z.object({
    server: z.string().optional(),
    transport: z.enum(['stdio', 'sse', 'websocket']).optional(),
    args: z.array(z.string()).optional(),
  }).optional(),
})

type ToolFormData = z.infer<typeof toolSchema>

interface ToolFormProps {
  onSubmit: (data: ToolFormData) => void
  initialData?: Partial<ToolFormData>
}

export function ToolForm({ onSubmit, initialData }: ToolFormProps) {
  const [currentTab, setCurrentTab] = useState(0)
  const [parameters, setParameters] = useState<any[]>([])
  const [mcpArgs, setMcpArgs] = useState<string[]>([])
  const router = useRouter()

  const form = useForm<ToolFormData>({
    resolver: zodResolver(toolSchema),
    defaultValues: initialData || {
      type: 'custom',
      version: '1.0.0',
      tags: [],
      configuration: {
        authentication: {
          type: 'none',
        },
        parameters: [],
      },
      mcpConfig: {
        transport: 'stdio',
        args: [],
      },
    },
  })

  const tabs = [
    { label: 'Basic Info', id: 'basic' },
    { label: 'Configuration', id: 'config' },
    { label: 'Parameters', id: 'parameters' },
  ]

  const handleSubmit = (data: ToolFormData) => {
    onSubmit({
      ...data,
      configuration: {
        ...data.configuration,
        parameters: parameters,
      },
      mcpConfig: {
        ...data.mcpConfig,
        args: mcpArgs,
      },
    })
  }

  const addParameter = () => {
    setParameters([...parameters, { name: '', type: 'string', required: false, description: '' }])
  }

  const removeParameter = (index: number) => {
    setParameters(parameters.filter((_, i) => i !== index))
  }

  const updateParameter = (index: number, field: string, value: any) => {
    const updated = parameters.map((param, i) => 
      i === index ? { ...param, [field]: value } : param
    )
    setParameters(updated)
  }

  const addMcpArg = () => {
    setMcpArgs([...mcpArgs, ''])
  }

  const removeMcpArg = (index: number) => {
    setMcpArgs(mcpArgs.filter((_, i) => i !== index))
  }

  const updateMcpArg = (index: number, value: string) => {
    const updated = mcpArgs.map((arg, i) => i === index ? value : arg)
    setMcpArgs(updated)
  }

  const renderBasicInfo = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tool Name
        </label>
        <input
          type="text"
          {...form.register('name')}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="Enter tool name"
        />
        {form.formState.errors.name && (
          <p className="text-red-500 text-sm mt-1">{form.formState.errors.name.message}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Description
        </label>
        <textarea
          {...form.register('description')}
          rows={4}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="Describe what this tool does"
        />
        {form.formState.errors.description && (
          <p className="text-red-500 text-sm mt-1">{form.formState.errors.description.message}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tool Type
        </label>
        <select
          {...form.register('type')}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="custom">Custom Tool</option>
          <option value="mcp">MCP Tool</option>
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Version
          </label>
          <input
            type="text"
            {...form.register('version')}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="1.0.0"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Category
          </label>
          <select
            {...form.register('category')}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Select category</option>
            <option value="web">Web</option>
            <option value="database">Database</option>
            <option value="api">API</option>
            <option value="file">File System</option>
            <option value="ai">AI/ML</option>
            <option value="communication">Communication</option>
            <option value="utility">Utility</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tags
        </label>
        <input
          type="text"
          placeholder="Enter tags separated by commas"
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          onChange={(e) => {
            const tags = e.target.value.split(',').map(tag => tag.trim()).filter(Boolean)
            form.setValue('tags', tags)
          }}
        />
      </div>
    </div>
  )

  const renderConfiguration = () => (
    <div className="space-y-6">
      {form.watch('type') === 'custom' && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Endpoint URL
            </label>
            <input
              type="url"
              {...form.register('configuration.endpoint')}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="https://api.example.com/tool"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Authentication Type
            </label>
            <select
              {...form.register('configuration.authentication.type')}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="none">No Authentication</option>
              <option value="bearer">Bearer Token</option>
              <option value="apikey">API Key</option>
              <option value="oauth">OAuth</option>
            </select>
          </div>

          {form.watch('configuration.authentication.type') === 'bearer' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bearer Token
              </label>
              <input
                type="password"
                {...form.register('configuration.authentication.token')}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="Enter bearer token"
              />
            </div>
          )}

          {form.watch('configuration.authentication.type') === 'apikey' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Key
              </label>
              <input
                type="password"
                {...form.register('configuration.authentication.apiKey')}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="Enter API key"
              />
            </div>
          )}
        </>
      )}

      {form.watch('type') === 'mcp' && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              MCP Server
            </label>
            <input
              type="text"
              {...form.register('mcpConfig.server')}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="path/to/mcp/server"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Transport
            </label>
            <select
              {...form.register('mcpConfig.transport')}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="stdio">STDIO</option>
              <option value="sse">Server-Sent Events</option>
              <option value="websocket">WebSocket</option>
            </select>
          </div>

          <div>
            <div className="flex justify-between items-center mb-4">
              <label className="block text-sm font-medium text-gray-700">
                Arguments
              </label>
              <button
                type="button"
                onClick={addMcpArg}
                className="flex items-center space-x-2 px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700"
              >
                <Plus className="w-4 h-4" />
                <span>Add Argument</span>
              </button>
            </div>
            <div className="space-y-2">
              {mcpArgs.map((arg, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={arg}
                    onChange={(e) => updateMcpArg(index, e.target.value)}
                    className="flex-1 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="Argument value"
                  />
                  <button
                    type="button"
                    onClick={() => removeMcpArg(index)}
                    className="p-2 hover:bg-gray-100 rounded"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )

  const renderParameters = () => (
    <div className="space-y-6">
      <div>
        <div className="flex justify-between items-center mb-4">
          <label className="block text-sm font-medium text-gray-700">
            Tool Parameters
          </label>
          <button
            type="button"
            onClick={addParameter}
            className="flex items-center space-x-2 px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700"
          >
            <Plus className="w-4 h-4" />
            <span>Add Parameter</span>
          </button>
        </div>
        <div className="space-y-4">
          {parameters.map((param, index) => (
            <div key={index} className="p-4 bg-gray-50 rounded-lg">
              <div className="grid grid-cols-2 gap-4 mb-3">
                <input
                  type="text"
                  value={param.name}
                  onChange={(e) => updateParameter(index, 'name', e.target.value)}
                  placeholder="Parameter name"
                  className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <select
                  value={param.type}
                  onChange={(e) => updateParameter(index, 'type', e.target.value)}
                  className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="string">String</option>
                  <option value="number">Number</option>
                  <option value="boolean">Boolean</option>
                  <option value="array">Array</option>
                  <option value="object">Object</option>
                </select>
              </div>
              <div className="mb-3">
                <textarea
                  value={param.description}
                  onChange={(e) => updateParameter(index, 'description', e.target.value)}
                  placeholder="Parameter description"
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={2}
                />
              </div>
              <div className="flex items-center justify-between">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={param.required}
                    onChange={(e) => updateParameter(index, 'required', e.target.checked)}
                  />
                  <span className="text-sm">Required</span>
                </label>
                <button
                  type="button"
                  onClick={() => removeParameter(index)}
                  className="p-1 hover:bg-gray-200 rounded"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
          {parameters.length === 0 && (
            <p className="text-gray-500 text-center py-8">No parameters defined</p>
          )}
        </div>
      </div>
    </div>
  )

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <div className="flex items-center space-x-4 mb-4">
          <button
            onClick={() => router.back()}
            className="flex items-center space-x-2 text-gray-600 hover:text-gray-800"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>
          <h1 className="text-2xl font-bold">Create New Tool</h1>
        </div>
        
        <div className="border-b">
          <nav className="flex space-x-8">
            {tabs.map((tab, index) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setCurrentTab(index)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  currentTab === index
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          {currentTab === 0 && renderBasicInfo()}
          {currentTab === 1 && renderConfiguration()}
          {currentTab === 2 && renderParameters()}
        </div>
        
        <div className="flex justify-between">
          <button
            type="button"
            onClick={() => setCurrentTab(Math.max(0, currentTab - 1))}
            disabled={currentTab === 0}
            className="flex items-center space-x-2 px-4 py-2 border rounded-lg disabled:opacity-50"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Previous</span>
          </button>
          
          {currentTab === tabs.length - 1 ? (
            <button
              type="submit"
              className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700"
            >
              Create Tool
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setCurrentTab(Math.min(tabs.length - 1, currentTab + 1))}
              className="flex items-center space-x-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
            >
              <span>Next</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </form>
    </div>
  )
}
