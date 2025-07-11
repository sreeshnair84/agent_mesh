'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/ui/Button'
import { X, Plus, Code } from 'lucide-react'

interface ConstraintRule {
  field: string
  operator: 'equals' | 'contains' | 'regex' | 'range' | 'custom'
  value: any
  message: string
}

interface ConstraintFormData {
  name: string
  description: string
  type: 'validation' | 'security' | 'performance' | 'custom'
  template?: string
  rules: ConstraintRule[]
  config: Record<string, any>
  status: 'active' | 'inactive' | 'draft'
}

interface ConstraintFormProps {
  initialData?: Partial<ConstraintFormData>
  templates?: any[]
  onSubmit: (data: ConstraintFormData) => void
  onCancel: () => void
  isLoading?: boolean
}

export function ConstraintForm({ 
  initialData, 
  templates = [], 
  onSubmit, 
  onCancel, 
  isLoading 
}: ConstraintFormProps) {
  const [rules, setRules] = useState<ConstraintRule[]>(initialData?.rules || [])
  const [selectedTemplate, setSelectedTemplate] = useState(initialData?.template || '')
  const [showTemplateCode, setShowTemplateCode] = useState(false)

  const { register, handleSubmit, formState: { errors }, watch, setValue } = useForm<ConstraintFormData>({
    defaultValues: initialData as ConstraintFormData
  })

  const constraintType = watch('type')

  const addRule = () => {
    const newRule: ConstraintRule = {
      field: '',
      operator: 'equals',
      value: '',
      message: ''
    }
    setRules([...rules, newRule])
  }

  const updateRule = (index: number, field: keyof ConstraintRule, value: any) => {
    const updatedRules = [...rules]
    updatedRules[index] = { ...updatedRules[index], [field]: value }
    setRules(updatedRules)
  }

  const removeRule = (index: number) => {
    setRules(rules.filter((_, i) => i !== index))
  }

  const handleTemplateChange = (templateId: string) => {
    setSelectedTemplate(templateId)
    const template = templates.find(t => t.id === templateId)
    if (template) {
      setValue('name', template.name)
      setValue('description', template.description)
      setValue('type', template.type)
      setRules(template.rules || [])
    }
  }

  const onSubmitForm = (data: ConstraintFormData) => {
    onSubmit({
      ...data,
      rules,
      template: selectedTemplate
    })
  }

  const operatorOptions = [
    { value: 'equals', label: 'Equals' },
    { value: 'contains', label: 'Contains' },
    { value: 'regex', label: 'Regex' },
    { value: 'range', label: 'Range' },
    { value: 'custom', label: 'Custom' }
  ]

  return (
    <form onSubmit={handleSubmit(onSubmitForm)} className="space-y-6">
      {/* Template Selection */}
      {templates.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Template (Optional)
          </label>
          <select
            value={selectedTemplate}
            onChange={(e) => handleTemplateChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="">Select a template</option>
            {templates.map((template) => (
              <option key={template.id} value={template.id}>
                {template.name} ({template.type})
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
            Name *
          </label>
          <input
            {...register('name', { required: 'Name is required' })}
            type="text"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="Enter constraint name"
          />
          {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>}
        </div>

        <div>
          <label htmlFor="type" className="block text-sm font-medium text-gray-700 mb-2">
            Type *
          </label>
          <select
            {...register('type', { required: 'Type is required' })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="">Select type</option>
            <option value="validation">Validation</option>
            <option value="security">Security</option>
            <option value="performance">Performance</option>
            <option value="custom">Custom</option>
          </select>
          {errors.type && <p className="mt-1 text-sm text-red-600">{errors.type.message}</p>}
        </div>
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
          Description *
        </label>
        <textarea
          {...register('description', { required: 'Description is required' })}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
          placeholder="Describe what this constraint does"
        />
        {errors.description && <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>}
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
          <option value="draft">Draft</option>
        </select>
      </div>

      {/* Rules */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <label className="block text-sm font-medium text-gray-700">
            Validation Rules
          </label>
          <Button type="button" onClick={addRule} size="sm" variant="outline">
            <Plus className="w-4 h-4 mr-2" />
            Add Rule
          </Button>
        </div>

        <div className="space-y-4">
          {rules.map((rule, index) => (
            <div key={index} className="border rounded-lg p-4 bg-gray-50">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Field
                  </label>
                  <input
                    type="text"
                    value={rule.field}
                    onChange={(e) => updateRule(index, 'field', e.target.value)}
                    placeholder="e.g., input.length"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Operator
                  </label>
                  <select
                    value={rule.operator}
                    onChange={(e) => updateRule(index, 'operator', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    {operatorOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Value
                  </label>
                  <input
                    type="text"
                    value={rule.value}
                    onChange={(e) => updateRule(index, 'value', e.target.value)}
                    placeholder="Expected value"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Error Message
                  </label>
                  <input
                    type="text"
                    value={rule.message}
                    onChange={(e) => updateRule(index, 'message', e.target.value)}
                    placeholder="Error message when rule fails"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>
              <div className="flex justify-end mt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => removeRule(index)}
                  className="text-red-600 hover:text-red-700"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>

        {rules.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No rules defined. Add rules to validate agent behavior.
          </div>
        )}
      </div>

      {/* Template Code Preview */}
      {constraintType && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-gray-700">
              Template Code
            </label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowTemplateCode(!showTemplateCode)}
            >
              <Code className="w-4 h-4 mr-2" />
              {showTemplateCode ? 'Hide' : 'Show'} Code
            </Button>
          </div>
          {showTemplateCode && (
            <div className="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm font-mono">
              <pre>{`// Generated constraint template
function validateConstraint(input, config) {
  const rules = ${JSON.stringify(rules, null, 2)};
  
  for (const rule of rules) {
    const fieldValue = getFieldValue(input, rule.field);
    const isValid = validateRule(fieldValue, rule.operator, rule.value);
    
    if (!isValid) {
      return {
        valid: false,
        message: rule.message
      };
    }
  }
  
  return { valid: true };
}`}</pre>
            </div>
          )}
        </div>
      )}

      <div className="flex justify-end space-x-3">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Saving...' : 'Save Constraint'}
        </Button>
      </div>
    </form>
  )
}
