'use client'

import { Store, Workflow, Wrench, BarChart3, TrendingUp, Users, Activity, Clock } from 'lucide-react'
import Link from 'next/link'
import { ClientOnly } from '@/components/ClientOnly'

export default function Home() {
  const stats = [
    { title: 'Active Agents', value: '12', icon: Activity, color: 'text-green-600' },
    { title: 'Workflows', value: '8', icon: Workflow, color: 'text-blue-600' },
    { title: 'Tools', value: '24', icon: Wrench, color: 'text-purple-600' },
    { title: 'Total Users', value: '156', icon: Users, color: 'text-orange-600' },
  ]

  const quickActions = [
    { 
      title: 'Create Agent', 
      description: 'Build and deploy new intelligent agents',
      href: '/agent-marketplace/create',
      icon: Store,
      color: 'bg-primary-600'
    },
    { 
      title: 'Design Workflow', 
      description: 'Create automated workflows with multiple agents',
      href: '/workflow/create',
      icon: Workflow,
      color: 'bg-green-600'
    },
    { 
      title: 'Add Tools', 
      description: 'Integrate new tools and capabilities',
      href: '/tools/create',
      icon: Wrench,
      color: 'bg-purple-600'
    },
    { 
      title: 'View Analytics', 
      description: 'Monitor performance and usage metrics',
      href: '/observability',
      icon: BarChart3,
      color: 'bg-orange-600'
    },
  ]

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">Welcome to Agent Mesh - Your intelligent agent orchestration platform</p>
      </div>

      {/* Stats Grid */}
      <ClientOnly fallback={
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg p-6 shadow-sm border animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      }>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat) => (
            <div key={stat.title} className="bg-white rounded-lg p-6 shadow-sm border">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                </div>
                <div className={`p-3 rounded-full bg-gray-100 ${stat.color}`}>
                  <stat.icon className="w-6 h-6" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </ClientOnly>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {quickActions.map((action) => (
            <Link
              key={action.title}
              href={action.href as any}
              className="bg-white rounded-lg p-6 shadow-sm border hover:shadow-md transition-shadow"
            >
              <div className={`inline-flex p-3 rounded-full ${action.color} text-white mb-4`}>
                <action.icon className="w-6 h-6" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{action.title}</h3>
              <p className="text-sm text-gray-600">{action.description}</p>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Recent Activity</h2>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm text-gray-900">Agent "Customer Support Bot" was deployed successfully</p>
                <p className="text-xs text-gray-500">2 hours ago</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm text-gray-900">New workflow "Order Processing" created</p>
                <p className="text-xs text-gray-500">4 hours ago</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm text-gray-900">Tool "Web Search API" added to marketplace</p>
                <p className="text-xs text-gray-500">6 hours ago</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
