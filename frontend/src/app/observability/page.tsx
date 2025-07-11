'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  Activity, TrendingUp, AlertTriangle, CheckCircle, Search, Filter, 
  Download, RefreshCw, Calendar, Eye, ArrowUpDown, Clock, Users,
  BarChart3, TrendingDown, Zap, AlertCircle
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts'
import { apiClient } from '@/lib/api-client'
import { Badge } from '@/components/ui/Badge'
import { TransactionDetailModal } from '@/components/observability/TransactionDetailModal'
import { TransactionFilters } from '@/components/observability/TransactionFilters'

interface Transaction {
  id: string
  session_id: string
  trace_id: string
  timestamp: string
  status: 'success' | 'error' | 'pending'
  duration: number
  agent_name: string
  workflow_name?: string
  error_message?: string
  request_count: number
  llm_tokens: number
}

interface Stats {
  total_agents: number
  total_workflows: number
  success_rate: number
  error_rate: number
  avg_latency: number
  total_requests: number
  active_sessions: number
  llm_usage: number
}

export default function ObservabilityPage() {
  const [timeRange, setTimeRange] = useState('24h')
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState({})
  const [showFilters, setShowFilters] = useState(false)
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [sortBy, setSortBy] = useState('timestamp')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  // Fetch real-time data
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['observability-stats', timeRange],
    queryFn: () => apiClient.get('/observability/stats', { params: { timeRange } }),
    refetchInterval: autoRefresh ? 5000 : false,
  })

  const { data: transactions, isLoading: transactionsLoading } = useQuery({
    queryKey: ['transactions', timeRange, searchQuery, filters, sortBy, sortOrder],
    queryFn: () => apiClient.get('/observability/transactions', { 
      params: { 
        timeRange, 
        search: searchQuery, 
        sort: sortBy,
        order: sortOrder,
        ...filters 
      } 
    }),
    refetchInterval: autoRefresh ? 5000 : false,
  })

  const { data: chartData } = useQuery({
    queryKey: ['observability-charts', timeRange],
    queryFn: () => apiClient.get('/observability/charts', { params: { timeRange } }),
    refetchInterval: autoRefresh ? 30000 : false,
  })

  // Mock data for demo
  const mockStats: Stats = {
    total_agents: 12,
    total_workflows: 8,
    success_rate: 99.2,
    error_rate: 0.8,
    avg_latency: 42,
    total_requests: 24532,
    active_sessions: 156,
    llm_usage: 2.4
  }

  const mockTransactions: Transaction[] = [
    {
      id: 'tx_001',
      session_id: 'sess_abc123',
      trace_id: 'trace_xyz789',
      timestamp: '2025-07-12T10:30:00Z',
      status: 'success',
      duration: 1250,
      agent_name: 'Customer Support Bot',
      workflow_name: 'Ticket Resolution',
      request_count: 3,
      llm_tokens: 1500
    },
    {
      id: 'tx_002',
      session_id: 'sess_def456',
      trace_id: 'trace_uvw123',
      timestamp: '2025-07-12T10:25:00Z',
      status: 'error',
      duration: 3200,
      agent_name: 'Data Analysis Agent',
      error_message: 'Connection timeout to external API',
      request_count: 1,
      llm_tokens: 800
    },
    // Add more mock transactions...
  ]

  const mockChartData = [
    { name: '00:00', requests: 1200, errors: 5, latency: 45, success_rate: 99.5 },
    { name: '04:00', requests: 800, errors: 2, latency: 38, success_rate: 99.8 },
    { name: '08:00', requests: 2400, errors: 12, latency: 52, success_rate: 99.0 },
    { name: '12:00', requests: 3200, errors: 8, latency: 41, success_rate: 99.2 },
    { name: '16:00', requests: 2800, errors: 15, latency: 48, success_rate: 98.8 },
    { name: '20:00', requests: 1600, errors: 4, latency: 35, success_rate: 99.6 },
  ]

  const statusColors = {
    success: 'bg-green-100 text-green-800',
    error: 'bg-red-100 text-red-800',
    pending: 'bg-yellow-100 text-yellow-800'
  }

  const handleExport = () => {
    // Export transactions to CSV
    const csv = [
      ['Transaction ID', 'Session ID', 'Trace ID', 'Timestamp', 'Status', 'Duration', 'Agent', 'Workflow'].join(','),
      ...mockTransactions.map(tx => [
        tx.id, tx.session_id, tx.trace_id, tx.timestamp, tx.status, tx.duration,
        tx.agent_name, tx.workflow_name || ''
      ].join(','))
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `transactions_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
  }

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
  }

  const currentStats = (stats?.data as Stats) || mockStats
  const currentTransactions = (transactions?.data as Transaction[]) || mockTransactions
  const currentChartData = (chartData?.data as any[]) || mockChartData

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Observability</h1>
          <p className="text-gray-600">Monitor agents, workflows, and system performance</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg border transition-colors ${
              autoRefresh ? 'bg-green-50 border-green-200 text-green-700' : 'bg-gray-50 border-gray-200 text-gray-700'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            <span>Auto Refresh</span>
          </button>
          <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
            {['1h', '6h', '24h', '7d', '30d'].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1 rounded-md text-sm transition-colors ${
                  timeRange === range
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {range}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-full bg-blue-100">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
            <Badge variant="secondary">{currentStats.total_agents} agents</Badge>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-600">Total Requests</p>
            <p className="text-2xl font-bold text-gray-900">{currentStats.total_requests.toLocaleString()}</p>
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-full bg-green-100">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <Badge variant="secondary">{currentStats.success_rate}%</Badge>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-600">Success Rate</p>
            <p className="text-2xl font-bold text-gray-900">{currentStats.success_rate}%</p>
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-full bg-purple-100">
              <Clock className="w-6 h-6 text-purple-600" />
            </div>
            <Badge variant="outline">{currentStats.avg_latency}ms avg</Badge>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-600">Response Time</p>
            <p className="text-2xl font-bold text-gray-900">{currentStats.avg_latency}ms</p>
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-full bg-red-100">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
            <Badge variant="destructive">{currentStats.error_rate}%</Badge>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-600">Error Rate</p>
            <p className="text-2xl font-bold text-gray-900">{currentStats.error_rate}%</p>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold mb-4">Request Volume & Success Rate</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={currentChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Line yAxisId="left" type="monotone" dataKey="requests" stroke="#7c3aed" strokeWidth={2} name="Requests" />
              <Line yAxisId="right" type="monotone" dataKey="success_rate" stroke="#10b981" strokeWidth={2} name="Success Rate %" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <h3 className="text-lg font-semibold mb-4">Response Latency & Errors</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={currentChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Bar yAxisId="left" dataKey="latency" fill="#7c3aed" name="Latency (ms)" />
              <Bar yAxisId="right" dataKey="errors" fill="#ef4444" name="Errors" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Transaction Search */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6 border-b">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Transaction Search</h2>
            <div className="flex items-center space-x-3">
              <button
                onClick={handleExport}
                className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <Download className="w-4 h-4" />
                <span>Export</span>
              </button>
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <Filter className="w-4 h-4" />
                <span>Filters</span>
              </button>
            </div>
          </div>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search by transaction ID, session ID, trace ID, or agent name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        {showFilters && (
          <TransactionFilters
            filters={filters}
            onFiltersChange={setFilters}
            onClose={() => setShowFilters(false)}
          />
        )}

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('timestamp')}
                    className="flex items-center space-x-1 hover:text-gray-900"
                  >
                    <span>Timestamp</span>
                    <ArrowUpDown className="w-4 h-4" />
                  </button>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Transaction ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Agent/Workflow
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('duration')}
                    className="flex items-center space-x-1 hover:text-gray-900"
                  >
                    <span>Duration</span>
                    <ArrowUpDown className="w-4 h-4" />
                  </button>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  LLM Tokens
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {transactionsLoading ? (
                [...Array(5)].map((_, i) => (
                  <tr key={i}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
                    </td>
                  </tr>
                ))
              ) : (
                currentTransactions.map((transaction) => (
                  <tr key={transaction.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(transaction.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-600">
                      {transaction.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge className={statusColors[transaction.status]}>
                        {transaction.status}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{transaction.agent_name}</div>
                      {transaction.workflow_name && (
                        <div className="text-sm text-gray-500">{transaction.workflow_name}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {transaction.duration}ms
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {transaction.llm_tokens.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => setSelectedTransaction(transaction)}
                        className="text-primary-600 hover:text-primary-900 flex items-center space-x-1"
                      >
                        <Eye className="w-4 h-4" />
                        <span>View</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Transaction Detail Modal */}
      {selectedTransaction && (
        <TransactionDetailModal
          transaction={selectedTransaction}
          onClose={() => setSelectedTransaction(null)}
        />
      )}
    </div>
  )
}
