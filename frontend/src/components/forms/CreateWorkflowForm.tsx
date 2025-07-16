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
import { CreateWorkflowFormData, WorkflowStep, WorkflowTrigger } from '@/types/create-forms'
import { Plus, X, GitBranch, Settings, Zap, Play, Trash2 } from 'lucide-react'

interface CreateWorkflowFormProps {
  onSubmit: (data: CreateWorkflowFormData) => void
  onCancel: () => void
  isLoading?: boolean
  agents?: Array<{ id: string; name: string; display_name: string }>
  tools?: Array<{ id: string; name: string; description: string }>
}

export default function CreateWorkflowForm({
  onSubmit,
  onCancel,
  isLoading = false,
  agents = [],
  tools = []
}: CreateWorkflowFormProps) {
  const [steps, setSteps] = useState<WorkflowStep[]>([])
  const [triggers, setTriggers] = useState<WorkflowTrigger[]>([])
  const [selectedAgents, setSelectedAgents] = useState<string[]>([])
  const [selectedTools, setSelectedTools] = useState<string[]>([])
  const [activeTab, setActiveTab] = useState<'basic' | 'steps' | 'triggers' | 'config'>('basic')

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors }
  } = useForm<CreateWorkflowFormData>({
    defaultValues: {
      type: 'sequential',
      config: {},
      agents: [],
      tools: [],
      steps: [],
      triggers: []
    }
  })

  const workflowType = watch('type')

  const workflowTypes = [
    { value: 'sequential', label: 'Sequential', description: 'Execute steps one after another' },
    { value: 'parallel', label: 'Parallel', description: 'Execute steps simultaneously' },
    { value: 'conditional', label: 'Conditional', description: 'Execute based on conditions' },
    { value: 'crag', label: 'CRAG', description: 'Corrective Retrieval Augmented Generation' }
  ]

  const stepTypes = [
    { value: 'agent', label: 'Agent Execution' },
    { value: 'tool', label: 'Tool Execution' },
    { value: 'condition', label: 'Conditional Logic' },
    { value: 'loop', label: 'Loop/Iteration' }
  ]

  const triggerTypes = [
    { value: 'manual', label: 'Manual Trigger' },
    { value: 'scheduled', label: 'Scheduled' },
    { value: 'webhook', label: 'Webhook' },
    { value: 'event', label: 'Event-based' }
  ]

  const handleAddStep = () => {
    const newStep: WorkflowStep = {
      id: `step-${Date.now()}`,
      name: `Step ${steps.length + 1}`,
      type: 'agent',
      config: {},
      dependencies: [],
      next_steps: []
    }
    setSteps([...steps, newStep])
    setValue('steps', [...steps, newStep])
  }

  const handleRemoveStep = (stepId: string) => {
    const updatedSteps = steps.filter(step => step.id !== stepId)
    setSteps(updatedSteps)
    setValue('steps', updatedSteps)
  }

  const handleUpdateStep = (stepId: string, updates: Partial<WorkflowStep>) => {
    const updatedSteps = steps.map(step => 
      step.id === stepId ? { ...step, ...updates } : step
    )
    setSteps(updatedSteps)
    setValue('steps', updatedSteps)
  }

  const handleAddTrigger = () => {
    const newTrigger: WorkflowTrigger = {
      type: 'manual',
      config: {}
    }
    setTriggers([...triggers, newTrigger])
    setValue('triggers', [...triggers, newTrigger])
  }

  const handleRemoveTrigger = (index: number) => {
    const updatedTriggers = triggers.filter((_, i) => i !== index)
    setTriggers(updatedTriggers)
    setValue('triggers', updatedTriggers)
  }

  const handleAgentToggle = (agentId: string) => {
    const updatedAgents = selectedAgents.includes(agentId)
      ? selectedAgents.filter(id => id !== agentId)
      : [...selectedAgents, agentId]
    setSelectedAgents(updatedAgents)
    setValue('agents', updatedAgents)
  }

  const handleToolToggle = (toolId: string) => {
    const updatedTools = selectedTools.includes(toolId)
      ? selectedTools.filter(id => id !== toolId)
      : [...selectedTools, toolId]
    setSelectedTools(updatedTools)
    setValue('tools', updatedTools)
  }

  const onFormSubmit = (data: CreateWorkflowFormData) => {
    onSubmit({
      ...data,
      agents: selectedAgents,
      tools: selectedTools,
      steps,
      triggers
    })
  }

  const tabs = [
    { id: 'basic', name: 'Basic Info', icon: Settings },
    { id: 'steps', name: 'Workflow Steps', icon: GitBranch },
    { id: 'triggers', name: 'Triggers', icon: Play },
    { id: 'config', name: 'Configuration', icon: Zap }
  ]

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2 flex items-center gap-2">
          <GitBranch className="w-6 h-6 text-blue-600" />
          Create New Workflow
        </h2>
        <p className="text-gray-600">Design a workflow that orchestrates multiple agents and tools</p>
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

      <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
        {/* Basic Information Tab */}
        {activeTab === 'basic' && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Basic Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Workflow Name *</Label>
                <Input
                  id="name"
                  {...register('name', { required: 'Workflow name is required' })}
                  placeholder="customer-support-workflow"
                />
                {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>}
              </div>

              <div>
                <Label htmlFor="type">Workflow Type *</Label>
                <Select
                  id="type"
                  {...register('type', { required: 'Workflow type is required' })}
                >
                  {workflowTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </Select>
                {errors.type && <p className="text-red-500 text-sm mt-1">{errors.type.message}</p>}
              </div>
            </div>

            <div className="mt-4">
              <Label htmlFor="description">Description *</Label>
              <Textarea
                id="description"
                {...register('description', { required: 'Description is required' })}
                placeholder="Describe what this workflow does..."
                rows={3}
              />
              {errors.description && <p className="text-red-500 text-sm mt-1">{errors.description.message}</p>}
            </div>

            <div className="mt-4">
              <p className="text-sm text-gray-600">
                {workflowTypes.find(t => t.value === workflowType)?.description}
              </p>
            </div>
          </Card>
        )}

        {/* Workflow Steps Tab */}
        {activeTab === 'steps' && (
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Workflow Steps</h3>
              <Button type="button" onClick={handleAddStep} size="sm">
                <Plus className="w-4 h-4 mr-2" />
                Add Step
              </Button>
            </div>

            <div className="space-y-4">
              {steps.map((step, index) => (
                <div key={step.id} className="border rounded-lg p-4 bg-gray-50">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm font-medium">
                        {index + 1}
                      </span>
                      <Input
                        value={step.name}
                        onChange={(e) => handleUpdateStep(step.id, { name: e.target.value })}
                        className="w-48"
                      />
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleRemoveStep(step.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Step Type</Label>
                      <Select
                        value={step.type}
                        onChange={(e) => handleUpdateStep(step.id, { type: e.target.value as any })}
                      >
                        {stepTypes.map(type => (
                          <option key={type.value} value={type.value}>
                            {type.label}
                          </option>
                        ))}
                      </Select>
                    </div>

                    <div>
                      <Label>Configuration</Label>
                      <Textarea
                        value={JSON.stringify(step.config, null, 2)}
                        onChange={(e) => {
                          try {
                            const config = JSON.parse(e.target.value)
                            handleUpdateStep(step.id, { config })
                          } catch (err) {
                            // Invalid JSON, ignore
                          }
                        }}
                        rows={2}
                      />
                    </div>
                  </div>
                </div>
              ))}

              {steps.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No steps defined yet. Click "Add Step" to get started.
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Triggers Tab */}
        {activeTab === 'triggers' && (
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Workflow Triggers</h3>
              <Button type="button" onClick={handleAddTrigger} size="sm">
                <Plus className="w-4 h-4 mr-2" />
                Add Trigger
              </Button>
            </div>

            <div className="space-y-4">
              {triggers.map((trigger, index) => (
                <div key={index} className="border rounded-lg p-4 bg-gray-50">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium">Trigger {index + 1}</h4>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleRemoveTrigger(index)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Trigger Type</Label>
                      <Select
                        value={trigger.type}
                        onChange={(e) => {
                          const updatedTriggers = [...triggers]
                          updatedTriggers[index] = { ...trigger, type: e.target.value as any }
                          setTriggers(updatedTriggers)
                          setValue('triggers', updatedTriggers)
                        }}
                      >
                        {triggerTypes.map(type => (
                          <option key={type.value} value={type.value}>
                            {type.label}
                          </option>
                        ))}
                      </Select>
                    </div>

                    <div>
                      <Label>Configuration</Label>
                      <Textarea
                        value={JSON.stringify(trigger.config, null, 2)}
                        onChange={(e) => {
                          try {
                            const config = JSON.parse(e.target.value)
                            const updatedTriggers = [...triggers]
                            updatedTriggers[index] = { ...trigger, config }
                            setTriggers(updatedTriggers)
                            setValue('triggers', updatedTriggers)
                          } catch (err) {
                            // Invalid JSON, ignore
                          }
                        }}
                        rows={2}
                      />
                    </div>
                  </div>
                </div>
              ))}

              {triggers.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No triggers defined yet. Click "Add Trigger" to get started.
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Configuration Tab */}
        {activeTab === 'config' && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Available Resources</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Agents */}
              <div>
                <h4 className="font-medium mb-3">Available Agents</h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {agents.map(agent => (
                    <div key={agent.id} className="flex items-center justify-between p-2 border rounded">
                      <div>
                        <p className="font-medium">{agent.display_name}</p>
                        <p className="text-sm text-gray-600">{agent.name}</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={selectedAgents.includes(agent.id)}
                        onChange={() => handleAgentToggle(agent.id)}
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Tools */}
              <div>
                <h4 className="font-medium mb-3">Available Tools</h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {tools.map(tool => (
                    <div key={tool.id} className="flex items-center justify-between p-2 border rounded">
                      <div>
                        <p className="font-medium">{tool.name}</p>
                        <p className="text-sm text-gray-600">{tool.description}</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={selectedTools.includes(tool.id)}
                        onChange={() => handleToolToggle(tool.id)}
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-6">
              <Label htmlFor="config">Additional Configuration (JSON)</Label>
              <Textarea
                id="config"
                {...register('config')}
                placeholder='{"timeout": 300, "retry_count": 3}'
                rows={4}
              />
              <p className="text-sm text-gray-500 mt-1">Workflow-specific configuration options</p>
            </div>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="flex justify-end space-x-4 pt-6 border-t">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Creating...' : 'Create Workflow'}
          </Button>
        </div>
      </form>
    </div>
  )
}
