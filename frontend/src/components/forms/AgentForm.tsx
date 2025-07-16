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
  display_name: z.string().min(1, 'Display name is required'),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  tags: z.array(z.string()),
  type: z.enum(['lowcode', 'custom']),
  category_id: z.string().optional(),
  template_id: z.string().optional(),
  system_prompt: z.string().optional(),
  prompt: z.string().optional(),
  tools: z.array(z.string()),
  models: z.object({
    llm: z.string().optional(),
    embedding: z.string().optional(),
  }),
  model_id: z.string().optional(),
  skills: z.array(z.string()),
  constraints: z.array(z.string()),
  capabilities: z.array(z.string()),
  configuration: z.record(z.any()).optional(),
  memory_config: z.record(z.any()).optional(),
  rate_limits: z.record(z.any()).optional(),
  dns: z.string().url('Must be a valid URL').optional(),
  healthUrl: z.string().url('Must be a valid URL').optional(),
  port: z.number().optional(),
  authToken: z.string().optional(),
  is_public: z.boolean().default(true),
  version: z.string().default('1.0.0'),
  input_payload: z.record(z.any()).optional(),
  output_payload: z.record(z.any()).optional(),
}).refine((data) => {
  // For low-code agents, certain fields are mandatory
  if (data.type === 'lowcode') {
    const errors: string[] = [];
    
    if (!data.system_prompt && !data.prompt) {
      errors.push('System prompt is required for low-code agents');
    }
    
    if (!data.models.llm && !data.model_id) {
      errors.push('LLM model is required for low-code agents');
    }
    
    if (!data.tools || data.tools.length === 0) {
      errors.push('At least one tool is required for low-code agents');
    }
    
    if (errors.length > 0) {
      throw new z.ZodError(errors.map(error => ({
        code: 'custom',
        message: error,
        path: ['type']
      })));
    }
  }
  
  return true;
}, {
  message: 'Validation failed for agent configuration',
  path: ['type']
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
  
  const { data: categories } = useQuery({
    queryKey: ['agent-categories'],
    queryFn: () => api.agents.categories(),
  })
  
  const { data: tools } = useQuery({
    queryKey: ['tools'],
    queryFn: () => api.tools.list(),
  })
  
  const { data: models } = useQuery({
    queryKey: ['models'],
    queryFn: () => api.models.list(),
  })

  const { data: skills } = useQuery({
    queryKey: ['skills'],
    queryFn: () => api.masterData.skills.list(),
  })

  const { data: constraints } = useQuery({
    queryKey: ['constraints'],
    queryFn: () => api.masterData.constraints.list(),
  })

  const form = useForm<AgentFormData>({
    resolver: zodResolver(agentSchema),
    defaultValues: initialData || {
      type: 'lowcode',
      display_name: '',
      tags: [],
      tools: [],
      skills: [],
      constraints: [],
      capabilities: [],
      models: {
        llm: '',
        embedding: '',
      },
      is_public: true,
      version: '1.0.0',
      configuration: {},
      memory_config: {},
      rate_limits: {},
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
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Agent Name *
          </label>
          <input
            type="text"
            {...form.register('name')}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="Enter unique agent name"
          />
          {form.formState.errors.name && (
            <p className="text-red-500 text-sm mt-1">{form.formState.errors.name.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Display Name *
          </label>
          <input
            type="text"
            {...form.register('display_name')}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="Enter display name"
          />
          {form.formState.errors.display_name && (
            <p className="text-red-500 text-sm mt-1">{form.formState.errors.display_name.message}</p>
          )}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Description *
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

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Agent Type *
          </label>
          <select
            {...form.register('type')}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="lowcode">Low-Code Agent</option>
            <option value="custom">Custom Agent</option>
          </select>
          {form.formState.errors.type && (
            <p className="text-red-500 text-sm mt-1">{form.formState.errors.type.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Category
          </label>
          <select
            {...form.register('category_id')}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Select a category</option>
            {categories?.map((category) => (
              <option key={category.id} value={category.id}>
                {category.display_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Template
          </label>
          <select
            {...form.register('template_id')}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Select a template</option>
            {templates?.map((template) => (
              <option key={template.id} value={template.id}>
                {template.display_name}
              </option>
            ))}
          </select>
        </div>

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
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            {...form.register('is_public')}
            className="h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
          />
          <label className="text-sm font-medium text-gray-700">
            Public Agent
          </label>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Port
          </label>
          <input
            type="number"
            {...form.register('port', { valueAsNumber: true })}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="8080"
          />
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

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Capabilities
        </label>
        <input
          type="text"
          placeholder="Enter capabilities separated by commas"
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          onChange={(e) => {
            const capabilities = e.target.value.split(',').map(cap => cap.trim()).filter(Boolean)
            form.setValue('capabilities', capabilities)
          }}
        />
      </div>
    </div>
  )

  const renderConfiguration = () => {
    const agentType = form.watch('type')
    const isLowCode = agentType === 'lowcode'
    
    return (
      <div className="space-y-6">
        {/* System Prompt - Required for Low-Code, Optional for Custom */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            System Prompt {isLowCode ? '*' : '(Optional)'}
          </label>
          <textarea
            {...form.register('system_prompt')}
            rows={6}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="Enter the system prompt for your agent"
          />
          {form.formState.errors.system_prompt && (
            <p className="text-red-500 text-sm mt-1">{form.formState.errors.system_prompt.message}</p>
          )}
          {isLowCode && (
            <p className="text-sm text-gray-600 mt-1">
              Required for low-code agents to define behavior and capabilities
            </p>
          )}
        </div>

        {/* Model Selection - Required for Low-Code, Optional for Custom */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              LLM Model {isLowCode ? '*' : '(Optional)'}
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
            {form.formState.errors.models?.llm && (
              <p className="text-red-500 text-sm mt-1">{form.formState.errors.models.llm.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Embedding Model
            </label>
            <select
              {...form.register('models.embedding')}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Select embedding model</option>
              {models?.filter(m => m.type === 'embedding')?.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Model Configuration Reference */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Model Configuration
          </label>
          <select
            {...form.register('model_id')}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Select model configuration</option>
            {models?.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name} - {model.provider}
              </option>
            ))}
          </select>
        </div>

        {/* Tools - Required for Low-Code, Optional for Custom */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Available Tools {isLowCode ? '*' : '(Optional)'}
          </label>
          <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto border rounded-md p-3">
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
                  className="h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <span className="text-sm">{tool.name}</span>
              </label>
            ))}
          </div>
          {isLowCode && (
            <p className="text-sm text-gray-600 mt-1">
              At least one tool is required for low-code agents
            </p>
          )}
        </div>

        {/* Skills */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Skills
          </label>
          <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto border rounded-md p-3">
            {skills?.map((skill) => (
              <label key={skill.id} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  value={skill.id}
                  onChange={(e) => {
                    const currentSkills = form.getValues('skills')
                    if (e.target.checked) {
                      form.setValue('skills', [...currentSkills, skill.id])
                    } else {
                      form.setValue('skills', currentSkills.filter(s => s !== skill.id))
                    }
                  }}
                  className="h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <span className="text-sm">{skill.name}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Constraints */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Constraints
          </label>
          <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto border rounded-md p-3">
            {constraints?.map((constraint) => (
              <label key={constraint.id} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  value={constraint.id}
                  onChange={(e) => {
                    const currentConstraints = form.getValues('constraints')
                    if (e.target.checked) {
                      form.setValue('constraints', [...currentConstraints, constraint.id])
                    } else {
                      form.setValue('constraints', currentConstraints.filter(c => c !== constraint.id))
                    }
                  }}
                  className="h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <span className="text-sm">{constraint.name}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Advanced Configuration */}
        <div className="border-t pt-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Advanced Configuration</h3>
          
          {/* Memory Configuration */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Memory Configuration (JSON)
            </label>
            <textarea
              rows={3}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-sm"
              placeholder='{"type": "simple", "max_tokens": 1000}'
              onChange={(e) => {
                try {
                  const config = JSON.parse(e.target.value || '{}')
                  form.setValue('memory_config', config)
                } catch {
                  // Invalid JSON, ignore
                }
              }}
            />
          </div>

          {/* Rate Limits */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Rate Limits (JSON)
            </label>
            <textarea
              rows={3}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-sm"
              placeholder='{"requests_per_minute": 60, "tokens_per_minute": 10000}'
              onChange={(e) => {
                try {
                  const config = JSON.parse(e.target.value || '{}')
                  form.setValue('rate_limits', config)
                } catch {
                  // Invalid JSON, ignore
                }
              }}
            />
          </div>

          {/* General Configuration */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              General Configuration (JSON)
            </label>
            <textarea
              rows={4}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-sm"
              placeholder='{"temperature": 0.7, "max_tokens": 1000}'
              onChange={(e) => {
                try {
                  const config = JSON.parse(e.target.value || '{}')
                  form.setValue('configuration', config)
                } catch {
                  // Invalid JSON, ignore
                }
              }}
            />
          </div>
        </div>
      </div>
    )
  }

  const renderDeployment = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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

      {/* Payload Configuration */}
      <div className="border-t pt-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Payload Configuration</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Input Payload Schema (JSON)
            </label>
            <textarea
              rows={6}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-sm"
              placeholder='{"type": "object", "properties": {"message": {"type": "string"}}}'
              onChange={(e) => {
                try {
                  const schema = JSON.parse(e.target.value || '{}')
                  form.setValue('input_payload', schema)
                } catch {
                  // Invalid JSON, ignore
                }
              }}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Output Payload Schema (JSON)
            </label>
            <textarea
              rows={6}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-sm"
              placeholder='{"type": "object", "properties": {"response": {"type": "string"}}}'
              onChange={(e) => {
                try {
                  const schema = JSON.parse(e.target.value || '{}')
                  form.setValue('output_payload', schema)
                } catch {
                  // Invalid JSON, ignore
                }
              }}
            />
          </div>
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
