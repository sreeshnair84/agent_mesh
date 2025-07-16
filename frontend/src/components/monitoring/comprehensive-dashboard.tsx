'use client'

import { useState, useEffect } from 'react'
import { 
  Activity, 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  Cpu, 
  Database, 
  Globe, 
  HardDrive,
  MemoryStick,
  Server,
  TrendingUp,
  TrendingDown,
  Users,
  Zap,
  AlertTriangle,
  RefreshCw,
  Settings,
  Download,
  Filter,
  Search,
  BarChart3,
  PieChart,
  LineChart,
  Network,
  Bell,
  Shield,
  Target,
  Gauge
} from 'lucide-react'

interface SystemMetrics {
  total_agents: number
  active_agents: number
  failed_agents: number
  total_requests: number
  success_rate: number
  average_response_time: number
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  uptime: string
  timestamp: string
}

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

interface Agent {
  id: string
  name: string
  type: string
  status: 'active' | 'inactive' | 'error'
  metrics: {
    cpu_usage: number
    memory_usage: number
    request_count: number
    average_response_time: number
    success_rate: number
  }
}

interface NetworkNode {
  id: string
  name: string
  type: 'agent' | 'workflow' | 'service'
  status: 'active' | 'inactive' | 'error'
  metrics: Record<string, number>
}

interface NetworkTopology {
  nodes: NetworkNode[]
  edges: Array<{
    source: string
    target: string
    type: string
    metrics: Record<string, number>
  }>
  clusters: Array<{
    id: string
    name: string
    nodes: string[]
    status: string
  }>
  metrics: Record<string, number>
}

interface MetricTrend {
  timestamps: string[]
  values: number[]
  metric_name: string
  unit: string
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = {
  async get(endpoint: string) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`)
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`)
    }
    return response.json()
  },
  async post(endpoint: string, data: any) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`)
    }
    return response.json()
  }
}

export function ComprehensiveMonitoringDashboard() {
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [topology, setTopology] = useState<NetworkTopology | null>(null)
  const [trends, setTrends] = useState<Record<string, MetricTrend>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTimeRange, setSelectedTimeRange] = useState('1h')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null)
  const [websocket, setWebsocket] = useState<WebSocket | null>(null)

  // Fetch system overview
  const fetchSystemMetrics = async () => {
    try {
      const data = await apiClient.get('/api/v1/monitoring/overview')
      setSystemMetrics(data)
    } catch (err) {
      console.error('Error fetching system metrics:', err)
      setError('Failed to fetch system metrics')
    }
  }

  // Fetch alerts
  const fetchAlerts = async () => {
    try {
      const data = await apiClient.get('/api/v1/monitoring/alerts')
      setAlerts(data.alerts)
    } catch (err) {
      console.error('Error fetching alerts:', err)
    }
  }

  // Fetch agents
  const fetchAgents = async () => {
    try {
      const data = await apiClient.get('/api/v1/monitoring/agents')
      setAgents(data.agents)
    } catch (err) {
      console.error('Error fetching agents:', err)
    }
  }

  // Fetch network topology
  const fetchTopology = async () => {
    try {
      const data = await apiClient.get('/api/v1/monitoring/topology')
      setTopology(data)
    } catch (err) {
      console.error('Error fetching topology:', err)
    }
  }

  // Fetch performance trends
  const fetchTrends = async () => {
    try {
      const endTime = new Date()
      const startTime = new Date(endTime.getTime() - (selectedTimeRange === '1h' ? 3600000 : 
                                                      selectedTimeRange === '24h' ? 86400000 : 
                                                      selectedTimeRange === '7d' ? 604800000 : 2592000000))
      
      const data = await apiClient.get(
        `/api/v1/monitoring/performance/trends?start_time=${startTime.toISOString()}&end_time=${endTime.toISOString()}`
      )
      setTrends(data.trends)
    } catch (err) {
      console.error('Error fetching trends:', err)
    }
  }

  // Setup WebSocket connection
  const setupWebSocket = () => {
    if (websocket) {
      websocket.close()
    }

    const ws = new WebSocket(`ws://localhost:8002/api/v1/monitoring/ws/metrics`)
    
    ws.onopen = () => {
      console.log('WebSocket connected')
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'system_overview') {
        setSystemMetrics(data.data)
      } else if (data.type === 'agent_metric') {
        // Update agent metrics in real-time
        setAgents(prev => prev.map(agent => 
          agent.id === data.data.agent_id 
            ? { ...agent, metrics: { ...agent.metrics, [data.data.metric_name]: data.data.value } }
            : agent
        ))
      }
    }
    
    ws.onclose = () => {
      console.log('WebSocket disconnected')
      // Reconnect after 5 seconds
      setTimeout(setupWebSocket, 5000)
    }
    
    setWebsocket(ws)
  }

  // Load data
  const loadData = async () => {
    setLoading(true)
    setError(null)

    try {
      await Promise.all([
        fetchSystemMetrics(),
        fetchAlerts(),
        fetchAgents(),
        fetchTopology(),
        fetchTrends()
      ])
    } catch (err) {
      setError('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  // Resolve alert
  const resolveAlert = async (alertId: string) => {
    try {
      await apiClient.post(`/api/v1/monitoring/alerts/${alertId}/resolve`, {})
      await fetchAlerts()
    } catch (err) {
      console.error('Error resolving alert:', err)
    }
  }

  // Initial load
  useEffect(() => {
    loadData()
    setupWebSocket()

    // Auto-refresh
    const interval = setInterval(() => {
      if (autoRefresh) {
        loadData()
      }
    }, 30000)

    return () => {
      clearInterval(interval)
      if (websocket) {
        websocket.close()
      }
    }
  }, [selectedTimeRange, autoRefresh])

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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600'
      case 'inactive': return 'text-gray-600'
      case 'error': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'inactive': return <Clock className="h-4 w-4 text-gray-600" />
      case 'error': return <AlertCircle className="h-4 w-4 text-red-600" />
      default: return <Clock className="h-4 w-4 text-gray-600" />
    }
  }

  const formatValue = (value: number, unit: string) => {
    if (unit === 'percent') {
      return `${value.toFixed(1)}%`
    } else if (unit === 'seconds') {
      return `${value.toFixed(2)}s`
    } else if (unit === 'bytes') {
      return `${(value / 1024 / 1024).toFixed(1)}MB`
    }
    return value.toString()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Dashboard</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button onClick={loadData} className="btn-primary">
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Monitoring Dashboard</h1>
          <p className="text-gray-600">Real-time system observability and alerting</p>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-3 py-2 rounded-md text-sm font-medium ${
              autoRefresh ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
            }`}
          >
            <RefreshCw className="h-4 w-4 mr-1 inline" />
            Auto Refresh
          </button>
          <button onClick={loadData} className="btn-secondary">
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </button>
        </div>
      </div>

      {/* System Overview Cards */}
      {systemMetrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Agents</p>
                <p className="text-2xl font-bold text-green-600">{systemMetrics.active_agents}</p>
                <p className="text-xs text-gray-500">of {systemMetrics.total_agents} total</p>
              </div>
              <Users className="h-8 w-8 text-green-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold text-blue-600">{systemMetrics.success_rate.toFixed(1)}%</p>
                <p className="text-xs text-gray-500">{systemMetrics.total_requests} requests</p>
              </div>
              <Target className="h-8 w-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Response Time</p>
                <p className="text-2xl font-bold text-purple-600">{systemMetrics.average_response_time.toFixed(2)}s</p>
                <p className="text-xs text-gray-500">last hour</p>
              </div>
              <Clock className="h-8 w-8 text-purple-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">System Health</p>
                <p className="text-2xl font-bold text-green-600">
                  {systemMetrics.failed_agents === 0 ? 'Healthy' : 'Issues'}
                </p>
                <p className="text-xs text-gray-500">Uptime: {systemMetrics.uptime}</p>
              </div>
              <Shield className="h-8 w-8 text-green-600" />
            </div>
          </div>
        </div>
      )}

      {/* Resource Usage */}
      {systemMetrics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">CPU Usage</h3>
              <Cpu className="h-5 w-5 text-blue-600" />
            </div>
            <div className="relative">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Current</span>
                <span className="text-sm font-medium">{systemMetrics.cpu_usage.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    systemMetrics.cpu_usage > 80 ? 'bg-red-500' : 
                    systemMetrics.cpu_usage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${systemMetrics.cpu_usage}%` }}
                />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Memory Usage</h3>
              <MemoryStick className="h-5 w-5 text-purple-600" />
            </div>
            <div className="relative">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Current</span>
                <span className="text-sm font-medium">{systemMetrics.memory_usage.toFixed(1)}GB</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    systemMetrics.memory_usage > 80 ? 'bg-red-500' : 
                    systemMetrics.memory_usage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(systemMetrics.memory_usage, 100)}%` }}
                />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Disk Usage</h3>
              <HardDrive className="h-5 w-5 text-green-600" />
            </div>
            <div className="relative">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Current</span>
                <span className="text-sm font-medium">{systemMetrics.disk_usage.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    systemMetrics.disk_usage > 80 ? 'bg-red-500' : 
                    systemMetrics.disk_usage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${systemMetrics.disk_usage}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Alerts */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Active Alerts</h3>
          <div className="flex items-center space-x-2">
            <Bell className="h-5 w-5 text-yellow-600" />
            <span className="text-sm text-gray-600">{alerts.filter(a => a.status === 'active').length} active</span>
          </div>
        </div>
        
        {alerts.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
            <p className="text-gray-600">No active alerts</p>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.slice(0, 5).map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border ${getSeverityColor(alert.severity)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium">{alert.rule_name}</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                        {alert.severity}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(alert.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <button
                    onClick={() => resolveAlert(alert.id)}
                    className="btn-sm btn-secondary"
                  >
                    Resolve
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Agents Status */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Agent Status</h3>
          <div className="flex items-center space-x-2">
            <Server className="h-5 w-5 text-blue-600" />
            <span className="text-sm text-gray-600">{agents.length} agents</span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <div key={agent.id} className="p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">{agent.name}</h4>
                {getStatusIcon(agent.status)}
              </div>
              <p className="text-sm text-gray-600 mb-3">{agent.type}</p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-500">CPU:</span>
                  <span className="ml-1 font-medium">{agent.metrics.cpu_usage.toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-gray-500">Memory:</span>
                  <span className="ml-1 font-medium">{agent.metrics.memory_usage.toFixed(1)}MB</span>
                </div>
                <div>
                  <span className="text-gray-500">Requests:</span>
                  <span className="ml-1 font-medium">{agent.metrics.request_count}</span>
                </div>
                <div>
                  <span className="text-gray-500">Success:</span>
                  <span className="ml-1 font-medium">{agent.metrics.success_rate.toFixed(1)}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Network Topology */}
      {topology && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Network Topology</h3>
            <Network className="h-5 w-5 text-purple-600" />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Nodes</h4>
              <div className="space-y-2">
                {topology.nodes.map((node) => (
                  <div key={node.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(node.status)}
                      <span className="text-sm font-medium">{node.name}</span>
                    </div>
                    <span className="text-xs text-gray-500">{node.type}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Clusters</h4>
              <div className="space-y-2">
                {topology.clusters.map((cluster) => (
                  <div key={cluster.id} className="p-2 bg-gray-50 rounded">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{cluster.name}</span>
                      <span className={`text-xs ${getStatusColor(cluster.status)}`}>
                        {cluster.status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {cluster.nodes.length} nodes
                    </p>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Connections</h4>
              <div className="space-y-2">
                {topology.edges.map((edge, index) => (
                  <div key={index} className="p-2 bg-gray-50 rounded">
                    <p className="text-sm font-medium">{edge.source} → {edge.target}</p>
                    <p className="text-xs text-gray-500">{edge.type}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
