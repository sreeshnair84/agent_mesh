'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { 
  Save, 
  ArrowLeft, 
  Code, 
  Settings, 
  Play, 
  Eye, 
  Upload,
  Plus,
  X
} from 'lucide-react'
import Link from 'next/link'

interface AgentFormData {
  name: string
  description: string
  tags: string[]
  type: 'template' | 'custom'
  template: string
  prompt: string
  tools: string[]
  model: string
  skills: string[]
  constraints: string[]
  dns: string
  healthCheckUrl: string
  authToken: string
}

const templates = [
  { id: 'crag', name: 'CRAG (Corrective RAG)', description: 'Knowledge base integration with query correction' },
  { id: 'supervisor', name: 'Supervisor Agent', description: 'Multi-agent coordination and task delegation' },
  { id: 'plan-execute', name: 'Plan-Execute Agent', description: 'Dynamic planning with step-by-step execution' },
  { id: 'basic', name: 'Basic Assistant', description: 'Simple conversational agent' },
]

const availableTools = [
  { id: 'web-search', name: 'Web Search', type: 'mcp' },
  { id: 'calculator', name: 'Calculator', type: 'mcp' },
  { id: 'code-interpreter', name: 'Code Interpreter', type: 'custom' },
  { id: 'database-query', name: 'Database Query', type: 'custom' },
]

const availableModels = [
  { id: 'gpt-4', name: 'GPT-4', provider: 'OpenAI' },
  { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', provider: 'OpenAI' },
  { id: 'claude-3', name: 'Claude 3', provider: 'Anthropic' },
  { id: 'gemini-pro', name: 'Gemini Pro', provider: 'Google' },
]

const availableSkills = [
  'natural-language-processing',
  'data-analysis',
  'code-generation',
  'customer-service',
  'content-creation',
  'research',
  'problem-solving'
]

const availableConstraints = [
  'response-length-limit',
  'no-external-api-calls',
  'family-friendly-only',
  'business-hours-only',
  'rate-limiting',
  'data-privacy-compliance'
]

export function CreateAgentForm() {
  const router = useRouter()
  const [currentTab, setCurrentTab] = useState<'basic' | 'configuration' | 'deployment'>('basic')
  const [formData, setFormData] = useState<AgentFormData>({
    name: '',
    description: '',
    tags: [],
    type: 'template',
    template: '',
    prompt: '',
    tools: [],
    model: '',
    skills: [],
    constraints: [],
    dns: '',
    healthCheckUrl: '',
    authToken: ''
  })

  const [newTag, setNewTag] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleInputChange = (field: keyof AgentFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const addTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      handleInputChange('tags', [...formData.tags, newTag.trim()])
      setNewTag('')
    }
  }

  const removeTag = (tagToRemove: string) => {
    handleInputChange('tags', formData.tags.filter(tag => tag !== tagToRemove))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // Redirect to agent marketplace
      router.push('/agents')
    } catch (error) {
      console.error('Error creating agent:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleTest = () => {
    // Implement test functionality
    console.log('Testing agent configuration...')
  }

  const tabs = [
    { id: 'basic', name: 'Basic Info', icon: Eye },
    { id: 'configuration', name: 'Configuration', icon: Settings },
    { id: 'deployment', name: 'Deployment', icon: Play },
  ]

  const renderBasicInfo = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Agent Name *
        </label>
        <input
          type="text"
          required
          value={formData.name}
          onChange={(e) => handleInputChange('name', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          placeholder="Enter agent name"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Description *
        </label>
        <textarea
          required
          rows={3}
          value={formData.description}
          onChange={(e) => handleInputChange('description', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          placeholder="Describe what this agent does"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tags
        </label>
        <div className="flex flex-wrap gap-2 mb-2">
          {formData.tags.map(tag => (
            <span
              key={tag}
              className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800"
            >
              {tag}
              <button
                type="button"
                onClick={() => removeTag(tag)}
                className="ml-1 text-purple-600 hover:text-purple-800"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>
        <div className="flex space-x-2">
          <input
            type="text"
            value={newTag}
            onChange={(e) => setNewTag(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            placeholder="Add a tag"
          />
          <button
            type="button"
            onClick={addTag}
            className="px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Agent Type *
        </label>
        <div className="grid grid-cols-2 gap-4">
          <button
            type="button"
            onClick={() => handleInputChange('type', 'template')}
            className={`p-4 border rounded-lg text-left ${
              formData.type === 'template' 
                ? 'border-purple-500 bg-purple-50' 
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <div className="font-medium">Template-based</div>
            <div className="text-sm text-gray-600">Use pre-built templates</div>
          </button>
          <button
            type="button"
            onClick={() => handleInputChange('type', 'custom')}
            className={`p-4 border rounded-lg text-left ${
              formData.type === 'custom' 
                ? 'border-purple-500 bg-purple-50' 
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <div className="font-medium">Custom</div>
            <div className="text-sm text-gray-600">Build from scratch</div>
          </button>
        </div>
      </div>

      {formData.type === 'template' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Template *
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {templates.map(template => (
              <button
                key={template.id}
                type="button"
                onClick={() => handleInputChange('template', template.id)}
                className={`p-4 border rounded-lg text-left ${
                  formData.template === template.id 
                    ? 'border-purple-500 bg-purple-50' 
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <div className="font-medium">{template.name}</div>
                <div className="text-sm text-gray-600">{template.description}</div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )

  const renderConfiguration = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          System Prompt *
        </label>
        <textarea
          required
          rows={10}
          value={formData.prompt}
          onChange={(e) => handleInputChange('prompt', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono text-sm"
          placeholder="Enter the system prompt for your agent..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Model *
        </label>
        <select
          required
          value={formData.model}
          onChange={(e) => handleInputChange('model', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          <option value="">Choose a model</option>
          {availableModels.map(model => (
            <option key={model.id} value={model.id}>
              {model.name} ({model.provider})
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tools
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {availableTools.map(tool => (
            <label key={tool.id} className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.tools.includes(tool.id)}
                onChange={(e) => {
                  const newTools = e.target.checked
                    ? [...formData.tools, tool.id]
                    : formData.tools.filter(t => t !== tool.id)
                  handleInputChange('tools', newTools)
                }}
                className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <span className="text-sm">
                {tool.name} 
                <span className="text-gray-500 ml-1">({tool.type})</span>
              </span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Skills
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {availableSkills.map(skill => (
            <label key={skill} className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.skills.includes(skill)}
                onChange={(e) => {
                  const newSkills = e.target.checked
                    ? [...formData.skills, skill]
                    : formData.skills.filter(s => s !== skill)
                  handleInputChange('skills', newSkills)
                }}
                className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <span className="text-sm capitalize">{skill.replace('-', ' ')}</span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Constraints
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {availableConstraints.map(constraint => (
            <label key={constraint} className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.constraints.includes(constraint)}
                onChange={(e) => {
                  const newConstraints = e.target.checked
                    ? [...formData.constraints, constraint]
                    : formData.constraints.filter(c => c !== constraint)
                  handleInputChange('constraints', newConstraints)
                }}
                className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <span className="text-sm capitalize">{constraint.replace('-', ' ')}</span>
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
          DNS Configuration
        </label>
        <input
          type="text"
          value={formData.dns}
          onChange={(e) => handleInputChange('dns', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          placeholder="e.g., my-agent.agents.example.com"
        />
        <p className="text-sm text-gray-500 mt-1">
          Leave empty for auto-generated DNS
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Health Check URL
        </label>
        <input
          type="url"
          value={formData.healthCheckUrl}
          onChange={(e) => handleInputChange('healthCheckUrl', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          placeholder="https://your-agent.com/health"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Authentication Token
        </label>
        <input
          type="password"
          value={formData.authToken}
          onChange={(e) => handleInputChange('authToken', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          placeholder="Enter authentication token"
        />
      </div>

      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="font-medium text-gray-900 mb-2">Deployment Preview</h3>
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-gray-500">Agent Name:</dt>
            <dd className="text-gray-900">{formData.name || 'Not set'}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Type:</dt>
            <dd className="text-gray-900 capitalize">{formData.type}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Model:</dt>
            <dd className="text-gray-900">
              {availableModels.find(m => m.id === formData.model)?.name || 'Not selected'}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Tools:</dt>
            <dd className="text-gray-900">{formData.tools.length} selected</dd>
          </div>
        </dl>
      </div>
    </div>
  )

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link href="/agents" className="text-gray-400 hover:text-gray-600">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Create New Agent</h1>
            <p className="text-gray-600">Configure your intelligent agent</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={handleTest}
            className="btn-secondary flex items-center space-x-2"
          >
            <Play className="h-4 w-4" />
            <span>Test</span>
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="btn-primary flex items-center space-x-2"
          >
            <Save className="h-4 w-4" />
            <span>{isSubmitting ? 'Creating...' : 'Create Agent'}</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map(tab => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setCurrentTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                currentTab === tab.id
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              <span>{tab.name}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        {currentTab === 'basic' && renderBasicInfo()}
        {currentTab === 'configuration' && renderConfiguration()}
        {currentTab === 'deployment' && renderDeployment()}
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <div>
          {currentTab !== 'basic' && (
            <button
              type="button"
              onClick={() => {
                const tabs = ['basic', 'configuration', 'deployment']
                const currentIndex = tabs.indexOf(currentTab)
                setCurrentTab(tabs[currentIndex - 1] as any)
              }}
              className="btn-secondary"
            >
              Previous
            </button>
          )}
        </div>
        <div>
          {currentTab !== 'deployment' && (
            <button
              type="button"
              onClick={() => {
                const tabs = ['basic', 'configuration', 'deployment']
                const currentIndex = tabs.indexOf(currentTab)
                setCurrentTab(tabs[currentIndex + 1] as any)
              }}
              className="btn-primary"
            >
              Next
            </button>
          )}
        </div>
      </div>
    </form>
  )
}
