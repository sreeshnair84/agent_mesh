'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { useRouter } from 'next/navigation'

const agentSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  tags: z.array(z.string()),
  type: z.enum(['lowcode', 'custom']),
  template: z.string().optional(),
  prompt: z.string().optional(),
  tools: z.array(z.string()),
  models: z.object({
    llm: z.string(),
    embedding: z.string().optional(),
  }),
  skills: z.array(z.string()),
  constraints: z.array(z.string()),
  dns: z.string().url('Must be a valid URL').optional(),
  healthUrl: z.string().url('Must be a valid URL').optional(),
  authToken: z.string().optional(),
}).refine((data) => {
  if (data.type === 'lowcode' && !data.prompt) {
    return false
  }
  return true
}, {
  message: 'Prompt is required for low-code agents',
  path: ['prompt']
})

type AgentFormData = z.infer<typeof agentSchema>

interface AgentFormProps {
  onSubmit: (data: AgentFormData) => void
  initialData?: Partial<AgentFormData>
}

export function AgentForm({ onSubmit, initialData }: AgentFormProps) {
  const [currentTab, setCurrentTab] = useState(0)
  const router = useRouter()
  
  const { data: templates } = useQuery({
    queryKey: ['agent-templates'],
    queryFn: () => api.templates.getAgentTemplates(),
  })
  
  const { data: tools } = useQuery({
    queryKey: ['tools'],
    queryFn: () => api.tools.list(),
  })
  
  const { data: models } = useQuery({
    queryKey: ['models'],
    queryFn: () => api.models.list(),
  })

  const form = useForm<AgentFormData>({
    resolver: zodResolver(agentSchema),
    defaultValues: initialData || {
      type: 'lowcode',
      tags: [],
      tools: [],
      skills: [],
      constraints: [],
      models: {
        llm: '',
        embedding: '',
      },
    },
  })

  const tabs = [
    { label: 'Basic Info', id: 'basic' },
    { label: 'Configuration', id: 'config' },
    { label: 'Deployment', id: 'deployment' },
  ]

  const handleSubmit = (data: AgentFormData) => {
    onSubmit(data)
  }

  const renderBasicInfo = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Agent Name
        </label>
        <input
          type="text"
          {...form.register('name')}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="Enter agent name"
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
          placeholder="Describe what this agent does"
        />
        {form.formState.errors.description && (
          <p className="text-red-500 text-sm mt-1">{form.formState.errors.description.message}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Agent Type
        </label>
        <select
          {...form.register('type')}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="lowcode">Low-Code Agent</option>
          <option value="custom">Custom Agent</option>
        </select>
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
      {form.watch('type') === 'lowcode' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            System Prompt
          </label>
          <textarea
            {...form.register('prompt')}
            rows={6}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="Enter the system prompt for your agent"
          />
          {form.formState.errors.prompt && (
            <p className="text-red-500 text-sm mt-1">{form.formState.errors.prompt.message}</p>
          )}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          LLM Model
        </label>
        <select
          {...form.register('models.llm')}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="">Select a model</option>
          {models?.map((model) => (
            <option key={model.id} value={model.id}>
              {model.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Available Tools
        </label>
        <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
          {tools?.map((tool) => (
            <label key={tool.id} className="flex items-center space-x-2">
              <input
                type="checkbox"
                value={tool.id}
                onChange={(e) => {
                  const currentTools = form.getValues('tools')
                  if (e.target.checked) {
                    form.setValue('tools', [...currentTools, tool.id])
                  } else {
                    form.setValue('tools', currentTools.filter(t => t !== tool.id))
                  }
                }}
              />
              <span className="text-sm">{tool.name}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  )

  const renderDeployment = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          DNS (Optional)
        </label>
        <input
          type="url"
          {...form.register('dns')}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="https://your-agent-domain.com"
        />
        {form.formState.errors.dns && (
          <p className="text-red-500 text-sm mt-1">{form.formState.errors.dns.message}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Health Check URL (Optional)
        </label>
        <input
          type="url"
          {...form.register('healthUrl')}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="https://your-agent-domain.com/health"
        />
        {form.formState.errors.healthUrl && (
          <p className="text-red-500 text-sm mt-1">{form.formState.errors.healthUrl.message}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Authentication Token (Optional)
        </label>
        <input
          type="password"
          {...form.register('authToken')}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="Enter authentication token"
        />
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
          <h1 className="text-2xl font-bold">Create New Agent</h1>
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
          {currentTab === 2 && renderDeployment()}
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
              Create Agent
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
