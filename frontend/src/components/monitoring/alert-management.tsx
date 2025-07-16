'use client'

import { useState, useEffect } from 'react'
import { 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Bell, 
  BellOff, 
  Settings, 
  Plus, 
  Edit, 
  Trash2, 
  Search, 
  Filter, 
  X, 
  Mail, 
  MessageSquare, 
  Globe, 
  Save,
  AlertCircle,
  Info,
  Shield,
  Zap,
  Activity
} from 'lucide-react'

interface Alert {
  id: string
  rule_name: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: 'active' | 'resolved' | 'silenced'
  message: string
  timestamp: string
  resolved_at?: string
  agent_id?: string
  metric_name?: string
  threshold?: number
  current_value?: number
  labels?: Record<string, string>
}

interface AlertRule {
  id: string
  name: string
  description: string
  metric_name: string
  operator: 'gt' | 'lt' | 'eq' | 'ne' | 'gte' | 'lte'
  threshold: number
  severity: 'low' | 'medium' | 'high' | 'critical'
  enabled: boolean
  labels?: Record<string, string>
  notification_channels: string[]
  created_at: string
  updated_at: string
}

interface NotificationChannel {
  id: string
  name: string
  type: 'email' | 'webhook' | 'slack'
  config: Record<string, any>
  enabled: boolean
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = {
  async get(endpoint: string) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`)
    if (!response.ok) throw new Error(`API Error: ${response.status}`)
    return response.json()
  },
  async post(endpoint: string, data: any) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (!response.ok) throw new Error(`API Error: ${response.status}`)
    return response.json()
  },
  async put(endpoint: string, data: any) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (!response.ok) throw new Error(`API Error: ${response.status}`)
    return response.json()
  },
  async delete(endpoint: string) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE'
    })
    if (!response.ok) throw new Error(`API Error: ${response.status}`)
    return response.json()
  }
}

export function AlertManagement() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [alertRules, setAlertRules] = useState<AlertRule[]>([])
  const [notificationChannels, setNotificationChannels] = useState<NotificationChannel[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTab, setSelectedTab] = useState<'alerts' | 'rules' | 'channels'>('alerts')
  const [searchTerm, setSearchTerm] = useState('')
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null)
  const [editingChannel, setEditingChannel] = useState<NotificationChannel | null>(null)

  // Fetch data
  const fetchAlerts = async () => {
    try {
      const data = await apiClient.get('/api/v1/monitoring/alerts')
      setAlerts(data.alerts)
    } catch (err) {
      console.error('Error fetching alerts:', err)
    }
  }

  const fetchAlertRules = async () => {
    try {
      const data = await apiClient.get('/api/v1/monitoring/alert-rules')
      setAlertRules(data.rules)
    } catch (err) {
      console.error('Error fetching alert rules:', err)
    }
  }

  const fetchNotificationChannels = async () => {
    try {
      const data = await apiClient.get('/api/v1/monitoring/notification-channels')
      setNotificationChannels(data.channels)
    } catch (err) {
      console.error('Error fetching notification channels:', err)
    }
  }

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      await Promise.all([fetchAlerts(), fetchAlertRules(), fetchNotificationChannels()])
    } catch (err) {
      setError('Failed to load alert data')
    } finally {
      setLoading(false)
    }
  }

  // Alert actions
  const resolveAlert = async (alertId: string) => {
    try {
      await apiClient.post(`/api/v1/monitoring/alerts/${alertId}/resolve`, {})
      await fetchAlerts()
    } catch (err) {
      console.error('Error resolving alert:', err)
    }
  }

  const silenceAlert = async (alertId: string, duration: number) => {
    try {
      await apiClient.post(`/api/v1/monitoring/alerts/${alertId}/silence`, { duration })
      await fetchAlerts()
    } catch (err) {
      console.error('Error silencing alert:', err)
    }
  }

  // Rule actions
  const createRule = async (rule: Omit<AlertRule, 'id' | 'created_at' | 'updated_at'>) => {
    try {
      await apiClient.post('/api/v1/monitoring/alert-rules', rule)
      await fetchAlertRules()
      setShowCreateModal(false)
    } catch (err) {
      console.error('Error creating rule:', err)
    }
  }

  const updateRule = async (rule: AlertRule) => {
    try {
      await apiClient.put(`/api/v1/monitoring/alert-rules/${rule.id}`, rule)
      await fetchAlertRules()
      setEditingRule(null)
    } catch (err) {
      console.error('Error updating rule:', err)
    }
  }

  const deleteRule = async (ruleId: string) => {
    try {
      await apiClient.delete(`/api/v1/monitoring/alert-rules/${ruleId}`)
      await fetchAlertRules()
    } catch (err) {
      console.error('Error deleting rule:', err)
    }
  }

  const toggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      await apiClient.put(`/api/v1/monitoring/alert-rules/${ruleId}`, { enabled })
      await fetchAlertRules()
    } catch (err) {
      console.error('Error toggling rule:', err)
    }
  }

  // Channel actions
  const createChannel = async (channel: Omit<NotificationChannel, 'id'>) => {
    try {
      await apiClient.post('/api/v1/monitoring/notification-channels', channel)
      await fetchNotificationChannels()
      setEditingChannel(null)
    } catch (err) {
      console.error('Error creating channel:', err)
    }
  }

  const updateChannel = async (channel: NotificationChannel) => {
    try {
      await apiClient.put(`/api/v1/monitoring/notification-channels/${channel.id}`, channel)
      await fetchNotificationChannels()
      setEditingChannel(null)
    } catch (err) {
      console.error('Error updating channel:', err)
    }
  }

  const deleteChannel = async (channelId: string) => {
    try {
      await apiClient.delete(`/api/v1/monitoring/notification-channels/${channelId}`)
      await fetchNotificationChannels()
    } catch (err) {
      console.error('Error deleting channel:', err)
    }
  }

  // Filter functions
  const filteredAlerts = alerts.filter(alert => {
    const matchesSearch = alert.rule_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         alert.message.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesSeverity = severityFilter === 'all' || alert.severity === severityFilter
    const matchesStatus = statusFilter === 'all' || alert.status === statusFilter
    return matchesSearch && matchesSeverity && matchesStatus
  })

  const filteredRules = alertRules.filter(rule => {
    const matchesSearch = rule.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         rule.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesSeverity = severityFilter === 'all' || rule.severity === severityFilter
    return matchesSearch && matchesSeverity
  })

  // Helper functions
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200'
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low': return 'bg-green-100 text-green-800 border-green-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <AlertTriangle className="h-4 w-4 text-red-600" />
      case 'high': return <AlertCircle className="h-4 w-4 text-orange-600" />
      case 'medium': return <Info className="h-4 w-4 text-yellow-600" />
      case 'low': return <CheckCircle className="h-4 w-4 text-green-600" />
      default: return <Info className="h-4 w-4 text-gray-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-red-600'
      case 'resolved': return 'text-green-600'
      case 'silenced': return 'text-gray-600'
      default: return 'text-gray-600'
    }
  }

  const getChannelIcon = (type: string) => {
    switch (type) {
      case 'email': return <Mail className="h-4 w-4" />
      case 'slack': return <MessageSquare className="h-4 w-4" />
      case 'webhook': return <Globe className="h-4 w-4" />
      default: return <Bell className="h-4 w-4" />
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Alert Management</h2>
          <p className="text-gray-600">Manage alerts, rules, and notification channels</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary"
          >
            <Plus className="h-4 w-4 mr-1" />
            New Rule
          </button>
          <button
            onClick={() => setEditingChannel({} as NotificationChannel)}
            className="btn-secondary"
          >
            <Plus className="h-4 w-4 mr-1" />
            New Channel
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {[
            { id: 'alerts', label: 'Active Alerts', count: alerts.filter(a => a.status === 'active').length },
            { id: 'rules', label: 'Alert Rules', count: alertRules.length },
            { id: 'channels', label: 'Notification Channels', count: notificationChannels.length }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setSelectedTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                selectedTab === tab.id
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className={`ml-2 px-2 py-1 rounded-full text-xs ${
                  selectedTab === tab.id ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        {selectedTab === 'alerts' && (
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active</option>
            <option value="resolved">Resolved</option>
            <option value="silenced">Silenced</option>
          </select>
        )}
      </div>

      {/* Content */}
      {selectedTab === 'alerts' && (
        <div className="space-y-4">
          {filteredAlerts.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <p className="text-gray-600">No alerts found</p>
            </div>
          ) : (
            filteredAlerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border ${getSeverityColor(alert.severity)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      {getSeverityIcon(alert.severity)}
                      <span className="font-medium">{alert.rule_name}</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                        {alert.severity}
                      </span>
                      <span className={`text-sm font-medium ${getStatusColor(alert.status)}`}>
                        {alert.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                    <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                      <span>Triggered: {new Date(alert.timestamp).toLocaleString()}</span>
                      {alert.agent_id && <span>Agent: {alert.agent_id}</span>}
                      {alert.metric_name && <span>Metric: {alert.metric_name}</span>}
                      {alert.threshold && alert.current_value && (
                        <span>Value: {alert.current_value} (threshold: {alert.threshold})</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {alert.status === 'active' && (
                      <>
                        <button
                          onClick={() => silenceAlert(alert.id, 3600)}
                          className="btn-sm btn-secondary"
                        >
                          <BellOff className="h-4 w-4 mr-1" />
                          Silence 1h
                        </button>
                        <button
                          onClick={() => resolveAlert(alert.id)}
                          className="btn-sm btn-primary"
                        >
                          <CheckCircle className="h-4 w-4 mr-1" />
                          Resolve
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {selectedTab === 'rules' && (
        <div className="space-y-4">
          {filteredRules.length === 0 ? (
            <div className="text-center py-8">
              <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No alert rules found</p>
            </div>
          ) : (
            filteredRules.map((rule) => (
              <div key={rule.id} className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      {getSeverityIcon(rule.severity)}
                      <span className="font-medium">{rule.name}</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(rule.severity)}`}>
                        {rule.severity}
                      </span>
                      <span className={`text-sm ${rule.enabled ? 'text-green-600' : 'text-gray-600'}`}>
                        {rule.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{rule.description}</p>
                    <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                      <span>Metric: {rule.metric_name}</span>
                      <span>Condition: {rule.operator} {rule.threshold}</span>
                      <span>Channels: {rule.notification_channels.length}</span>
                      <span>Updated: {new Date(rule.updated_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => toggleRule(rule.id, !rule.enabled)}
                      className={`btn-sm ${rule.enabled ? 'btn-secondary' : 'btn-primary'}`}
                    >
                      {rule.enabled ? <BellOff className="h-4 w-4" /> : <Bell className="h-4 w-4" />}
                    </button>
                    <button
                      onClick={() => setEditingRule(rule)}
                      className="btn-sm btn-secondary"
                    >
                      <Edit className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => deleteRule(rule.id)}
                      className="btn-sm btn-secondary text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {selectedTab === 'channels' && (
        <div className="space-y-4">
          {notificationChannels.length === 0 ? (
            <div className="text-center py-8">
              <Bell className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No notification channels configured</p>
            </div>
          ) : (
            notificationChannels.map((channel) => (
              <div key={channel.id} className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      {getChannelIcon(channel.type)}
                      <span className="font-medium">{channel.name}</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        channel.type === 'email' ? 'bg-blue-100 text-blue-800' :
                        channel.type === 'slack' ? 'bg-purple-100 text-purple-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {channel.type}
                      </span>
                      <span className={`text-sm ${channel.enabled ? 'text-green-600' : 'text-gray-600'}`}>
                        {channel.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                    <div className="mt-2 text-xs text-gray-500">
                      {channel.type === 'email' && <span>Email: {channel.config.email}</span>}
                      {channel.type === 'slack' && <span>Channel: {channel.config.channel}</span>}
                      {channel.type === 'webhook' && <span>URL: {channel.config.url}</span>}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setEditingChannel(channel)}
                      className="btn-sm btn-secondary"
                    >
                      <Edit className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => deleteChannel(channel.id)}
                      className="btn-sm btn-secondary text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
