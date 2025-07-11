'use client'

import { Bot, Workflow, Wrench, Activity, TrendingUp, AlertCircle } from 'lucide-react'

export function DashboardHome() {
  const stats = [
    {
      name: 'Active Agents',
      value: '12',
      change: '+2.1%',
      changeType: 'positive',
      icon: Bot,
    },
    {
      name: 'Running Workflows',
      value: '8',
      change: '+5.4%',
      changeType: 'positive',
      icon: Workflow,
    },
    {
      name: 'Available Tools',
      value: '24',
      change: '+12.5%',
      changeType: 'positive',
      icon: Wrench,
    },
    {
      name: 'System Health',
      value: '99.9%',
      change: '+0.1%',
      changeType: 'positive',
      icon: Activity,
    },
  ]

  const recentActivities = [
    {
      id: 1,
      type: 'Agent Created',
      description: 'Customer Support Agent v2.0 created',
      timestamp: '2 minutes ago',
      icon: Bot,
    },
    {
      id: 2,
      type: 'Workflow Completed',
      description: 'Data Processing Pipeline completed successfully',
      timestamp: '5 minutes ago',
      icon: Workflow,
    },
    {
      id: 3,
      type: 'Tool Added',
      description: 'Email Integration tool added to marketplace',
      timestamp: '10 minutes ago',
      icon: Wrench,
    },
    {
      id: 4,
      type: 'Alert Resolved',
      description: 'High CPU usage alert resolved',
      timestamp: '15 minutes ago',
      icon: AlertCircle,
    },
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Welcome back! Here's what's happening with your Agent Mesh.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-200"
          >
            <div className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <stat.icon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {stat.name}
                    </dt>
                    <dd className="flex items-baseline">
                      <div className="text-2xl font-semibold text-gray-900">
                        {stat.value}
                      </div>
                      <div className="ml-2 flex items-baseline text-sm font-semibold text-green-600">
                        <TrendingUp className="h-4 w-4 mr-1" />
                        {stat.change}
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activities */}
      <div className="bg-white shadow-sm rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Recent Activities</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {recentActivities.map((activity) => (
            <div key={activity.id} className="px-6 py-4">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <activity.icon className="h-5 w-5 text-gray-400" />
                </div>
                <div className="ml-4 flex-1">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {activity.type}
                      </p>
                      <p className="text-sm text-gray-500">
                        {activity.description}
                      </p>
                    </div>
                    <div className="text-sm text-gray-500">
                      {activity.timestamp}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white shadow-sm rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Quick Actions</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <button className="btn-primary w-full">
              <Bot className="h-5 w-5 mr-2" />
              Create Agent
            </button>
            <button className="btn-secondary w-full">
              <Workflow className="h-5 w-5 mr-2" />
              New Workflow
            </button>
            <button className="btn-secondary w-full">
              <Wrench className="h-5 w-5 mr-2" />
              Add Tool
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
