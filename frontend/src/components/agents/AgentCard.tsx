import Link from 'next/link'
import { Badge } from '@/components/ui/Badge'
import { Avatar } from '@/components/ui/Avatar'
import { formatDistanceToNow } from 'date-fns'

interface Agent {
  id: string
  name: string
  description: string
  tags: string[]
  owner: { name: string; avatar?: string }
  status: 'active' | 'inactive' | 'deploying'
  createdAt: string
  healthStatus: 'healthy' | 'unhealthy' | 'unknown'
}

interface AgentCardProps {
  agent: Agent
  viewMode: 'grid' | 'list'
}

export function AgentCard({ agent, viewMode }: AgentCardProps) {
  const statusColors = {
    active: 'bg-green-100 text-green-800',
    inactive: 'bg-gray-100 text-gray-800',
    deploying: 'bg-yellow-100 text-yellow-800',
  }

  const healthColors = {
    healthy: 'bg-green-500',
    unhealthy: 'bg-red-500',
    unknown: 'bg-gray-500',
  }

  if (viewMode === 'list') {
    return (
      <div className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className={`w-3 h-3 rounded-full ${healthColors[agent.healthStatus]}`} />
            <div>
              <Link href={`/agent-marketplace/${agent.id}` as any} className="font-semibold text-lg hover:text-primary-600">
                {agent.name}
              </Link>
              <p className="text-gray-600 text-sm">{agent.description}</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex space-x-2">
              {agent.tags.slice(0, 3).map((tag) => (
                <Badge key={tag} variant="secondary">{tag}</Badge>
              ))}
            </div>
            <Badge className={statusColors[agent.status]}>{agent.status}</Badge>
            <div className="flex items-center space-x-2">
              <Avatar src={agent.owner.avatar} name={agent.owner.name} size="sm" />
              <span className="text-sm text-gray-600">{agent.owner.name}</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white border rounded-lg p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-3 h-3 rounded-full ${healthColors[agent.healthStatus]} mt-1`} />
        <Badge className={statusColors[agent.status]}>{agent.status}</Badge>
      </div>
      
      <h3 className="font-semibold text-lg mb-2">
        <Link href={`/agent-marketplace/${agent.id}` as any} className="hover:text-primary-600">
          {agent.name}
        </Link>
      </h3>
      
      <p className="text-gray-600 text-sm mb-4 line-clamp-3">{agent.description}</p>
      
      <div className="flex flex-wrap gap-2 mb-4">
        {agent.tags.slice(0, 3).map((tag) => (
          <Badge key={tag} variant="secondary">{tag}</Badge>
        ))}
        {agent.tags.length > 3 && (
          <Badge variant="outline">+{agent.tags.length - 3}</Badge>
        )}
      </div>
      
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Avatar src={agent.owner.avatar} name={agent.owner.name} size="sm" />
          <span className="text-sm text-gray-600">{agent.owner.name}</span>
        </div>
        <span className="text-xs text-gray-500">
          {formatDistanceToNow(new Date(agent.createdAt), { addSuffix: true })}
        </span>
      </div>
    </div>
  )
}
