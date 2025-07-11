import React, { useState } from 'react'
import { X, Calendar, User, AlertCircle, CheckCircle, Clock } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'

interface TransactionFiltersProps {
  filters: any
  onFiltersChange: (filters: any) => void
  onClose: () => void
}

export function TransactionFilters({ filters, onFiltersChange, onClose }: TransactionFiltersProps) {
  const [localFilters, setLocalFilters] = useState(filters)

  const statusOptions = [
    { value: 'success', label: 'Success', icon: CheckCircle, color: 'text-green-600' },
    { value: 'error', label: 'Error', icon: AlertCircle, color: 'text-red-600' },
    { value: 'pending', label: 'Pending', icon: Clock, color: 'text-yellow-600' },
  ]

  const durationRanges = [
    { value: '0-100', label: '0-100ms' },
    { value: '100-500', label: '100-500ms' },
    { value: '500-1000', label: '500ms-1s' },
    { value: '1000-5000', label: '1s-5s' },
    { value: '5000+', label: '5s+' },
  ]

  const agents = [
    'Customer Support Bot',
    'Data Analysis Agent',
    'Content Generator',
    'Translation Service',
    'Order Processor',
    'Notification Service'
  ]

  const workflows = [
    'Ticket Resolution',
    'Data Processing',
    'Content Creation',
    'Order Fulfillment',
    'User Onboarding',
    'Report Generation'
  ]

  const handleFilterChange = (key: string, value: any) => {
    const newFilters = { ...localFilters, [key]: value }
    setLocalFilters(newFilters)
    onFiltersChange(newFilters)
  }

  const handleMultiSelectChange = (key: string, value: string) => {
    const currentValues = localFilters[key] || []
    const newValues = currentValues.includes(value)
      ? currentValues.filter((v: string) => v !== value)
      : [...currentValues, value]
    
    const newFilters = { ...localFilters, [key]: newValues }
    setLocalFilters(newFilters)
    onFiltersChange(newFilters)
  }

  const clearFilters = () => {
    setLocalFilters({})
    onFiltersChange({})
  }

  const hasActiveFilters = Object.keys(localFilters).some(key => {
    const value = localFilters[key]
    return Array.isArray(value) ? value.length > 0 : value !== undefined && value !== ''
  })

  return (
    <div className="border-t bg-gray-50 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Advanced Filters</h3>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-200 rounded-full transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Date Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Calendar className="w-4 h-4 inline mr-1" />
            Date Range
          </label>
          <div className="space-y-2">
            <input
              type="datetime-local"
              value={localFilters.start_date || ''}
              onChange={(e) => handleFilterChange('start_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
              placeholder="Start date"
            />
            <input
              type="datetime-local"
              value={localFilters.end_date || ''}
              onChange={(e) => handleFilterChange('end_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
              placeholder="End date"
            />
          </div>
        </div>

        {/* Status */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Status
          </label>
          <div className="space-y-2">
            {statusOptions.map((option) => (
              <label key={option.value} className="flex items-center">
                <input
                  type="checkbox"
                  checked={localFilters.status?.includes(option.value) || false}
                  onChange={() => handleMultiSelectChange('status', option.value)}
                  className="mr-2 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <option.icon className={`w-4 h-4 mr-1 ${option.color}`} />
                <span className="text-sm text-gray-700">{option.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Duration */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Duration
          </label>
          <div className="space-y-2">
            {durationRanges.map((range) => (
              <label key={range.value} className="flex items-center">
                <input
                  type="checkbox"
                  checked={localFilters.duration?.includes(range.value) || false}
                  onChange={() => handleMultiSelectChange('duration', range.value)}
                  className="mr-2 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700">{range.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Agents */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <User className="w-4 h-4 inline mr-1" />
            Agents
          </label>
          <div className="max-h-32 overflow-y-auto space-y-2">
            {agents.map((agent) => (
              <label key={agent} className="flex items-center">
                <input
                  type="checkbox"
                  checked={localFilters.agents?.includes(agent) || false}
                  onChange={() => handleMultiSelectChange('agents', agent)}
                  className="mr-2 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700">{agent}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Additional Filters Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
        {/* Workflows */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Workflows
          </label>
          <div className="max-h-32 overflow-y-auto space-y-2">
            {workflows.map((workflow) => (
              <label key={workflow} className="flex items-center">
                <input
                  type="checkbox"
                  checked={localFilters.workflows?.includes(workflow) || false}
                  onChange={() => handleMultiSelectChange('workflows', workflow)}
                  className="mr-2 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700">{workflow}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Session ID */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Session ID
          </label>
          <input
            type="text"
            value={localFilters.session_id || ''}
            onChange={(e) => handleFilterChange('session_id', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
            placeholder="Enter session ID"
          />
        </div>

        {/* Trace ID */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Trace ID
          </label>
          <input
            type="text"
            value={localFilters.trace_id || ''}
            onChange={(e) => handleFilterChange('trace_id', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
            placeholder="Enter trace ID"
          />
        </div>
      </div>

      {/* LLM Token Range */}
      <div className="mt-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          LLM Token Range
        </label>
        <div className="flex items-center space-x-4">
          <input
            type="number"
            value={localFilters.min_tokens || ''}
            onChange={(e) => handleFilterChange('min_tokens', e.target.value)}
            className="w-24 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
            placeholder="Min"
          />
          <span className="text-gray-500">to</span>
          <input
            type="number"
            value={localFilters.max_tokens || ''}
            onChange={(e) => handleFilterChange('max_tokens', e.target.value)}
            className="w-24 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
            placeholder="Max"
          />
          <span className="text-sm text-gray-500">tokens</span>
        </div>
      </div>

      {/* Active Filters Display */}
      {hasActiveFilters && (
        <div className="mt-6 pt-4 border-t">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-gray-700">Active Filters</h4>
            <button
              onClick={clearFilters}
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              Clear All
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(localFilters).map(([key, value]) => {
              if (!value || (Array.isArray(value) && value.length === 0)) return null
              
              if (Array.isArray(value)) {
                return value.map((item: string) => (
                  <Badge
                    key={`${key}-${item}`}
                    variant="secondary"
                    className="flex items-center space-x-1"
                  >
                    <span>{key}: {item}</span>
                    <button
                      onClick={() => handleMultiSelectChange(key, item)}
                      className="ml-1 hover:bg-gray-200 rounded-full p-0.5"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </Badge>
                ))
              }
              
              return (
                <Badge
                  key={key}
                  variant="secondary"
                  className="flex items-center space-x-1"
                >
                  <span>{key}: {String(value)}</span>
                  <button
                    onClick={() => handleFilterChange(key, '')}
                    className="ml-1 hover:bg-gray-200 rounded-full p-0.5"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
