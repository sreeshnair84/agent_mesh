'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { ArrowLeft, ArrowRight, Plus, X } from 'lucide-react'
import { useRouter } from 'next/navigation'

const workflowSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  tags: z.array(z.string()),
  trigger: z.enum(['manual', 'schedule', 'event']),
  agents: z.array(z.object({
    id: z.string(),
    name: z.string(),
    order: z.number(),
  })),
  parameters: z.array(z.object({
    name: z.string(),
    type: z.string(),
    required: z.boolean(),
  })),
  scheduleExpression: z.string().optional(),
  timeoutMinutes: z.number().optional(),
})

type WorkflowFormData = z.infer<typeof workflowSchema>

interface WorkflowFormProps {
  onSubmit: (data: WorkflowFormData) => void
  initialData?: Partial<WorkflowFormData>
}

export function WorkflowForm({ onSubmit, initialData }: WorkflowFormProps) {
  const [currentTab, setCurrentTab] = useState(0)
  const [selectedAgents, setSelectedAgents] = useState<any[]>([])
  const [parameters, setParameters] = useState<any[]>([])
  const router = useRouter()
  
  const { data: agents } = useQuery({
    queryKey: ['agents'],
    queryFn: () => api.agents.list(),
  })

  const form = useForm<WorkflowFormData>({
    resolver: zodResolver(workflowSchema),
    defaultValues: initialData || {
      trigger: 'manual',
      tags: [],
      agents: [],
      parameters: [],
      timeoutMinutes: 30,
    },
  })

  const tabs = [
    { label: 'Basic Info', id: 'basic' },
    { label: 'Agent Flow', id: 'flow' },
    { label: 'Configuration', id: 'config' },
  ]

  const handleSubmit = (data: WorkflowFormData) => {
    onSubmit({
      ...data,
      agents: selectedAgents,
      parameters: parameters,
    })
  }

  const addAgent = (agent: any) => {
    const newAgent = {
      id: agent.id,
      name: agent.name,
      order: selectedAgents.length + 1,
    }
    setSelectedAgents([...selectedAgents, newAgent])
  }

  const removeAgent = (agentId: string) => {
    setSelectedAgents(selectedAgents.filter(a => a.id !== agentId))
  }

  const addParameter = () => {
    setParameters([...parameters, { name: '', type: 'string', required: false }])
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

  const renderBasicInfo = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Workflow Name
        </label>
        <input
          type="text"
          {...form.register('name')}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="Enter workflow name"
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
          placeholder="Describe what this workflow does"
        />
        {form.formState.errors.description && (
          <p className="text-red-500 text-sm mt-1">{form.formState.errors.description.message}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Trigger Type
        </label>
        <select
          {...form.register('trigger')}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="manual">Manual Trigger</option>
          <option value="schedule">Scheduled</option>
          <option value="event">Event-based</option>
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

  const renderAgentFlow = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Available Agents
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-64 overflow-y-auto">
          {agents?.map((agent: any) => (
            <div key={agent.id} className="border rounded-lg p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h4 className="font-medium">{agent.name}</h4>
                  <p className="text-sm text-gray-600">{agent.description}</p>
                </div>
                <button
                  type="button"
                  onClick={() => addAgent(agent)}
                  disabled={selectedAgents.some(a => a.id === agent.id)}
                  className="ml-2 px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
                >
                  Add
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Workflow Flow ({selectedAgents.length} agents)
        </label>
        <div className="space-y-2">
          {selectedAgents.map((agent, index) => (
            <div key={agent.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-500">Step {index + 1}</span>
              <div className="flex-1">
                <span className="font-medium">{agent.name}</span>
              </div>
              <button
                type="button"
                onClick={() => removeAgent(agent.id)}
                className="p-1 hover:bg-gray-200 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
          {selectedAgents.length === 0 && (
            <p className="text-gray-500 text-center py-8">No agents selected</p>
          )}
        </div>
      </div>
    </div>
  )

  const renderConfiguration = () => (
    <div className="space-y-6">
      {form.watch('trigger') === 'schedule' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Schedule Expression (Cron)
          </label>
          <input
            type="text"
            {...form.register('scheduleExpression')}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="0 0 * * * (every day at midnight)"
          />
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Timeout (minutes)
        </label>
        <input
          type="number"
          {...form.register('timeoutMinutes', { valueAsNumber: true })}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="30"
        />
      </div>

      <div>
        <div className="flex justify-between items-center mb-4">
          <label className="block text-sm font-medium text-gray-700">
            Workflow Parameters
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
        <div className="space-y-3">
          {parameters.map((param, index) => (
            <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
              <input
                type="text"
                value={param.name}
                onChange={(e) => updateParameter(index, 'name', e.target.value)}
                placeholder="Parameter name"
                className="flex-1 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <select
                value={param.type}
                onChange={(e) => updateParameter(index, 'type', e.target.value)}
                className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="string">String</option>
                <option value="number">Number</option>
                <option value="boolean">Boolean</option>
              </select>
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
          ))}
          {parameters.length === 0 && (
            <p className="text-gray-500 text-center py-4">No parameters defined</p>
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
          <h1 className="text-2xl font-bold">Create New Workflow</h1>
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
          {currentTab === 1 && renderAgentFlow()}
          {currentTab === 2 && renderConfiguration()}
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
              Create Workflow
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
