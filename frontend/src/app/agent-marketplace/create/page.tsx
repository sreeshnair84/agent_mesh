'use client'

import { AgentForm } from '@/components/forms/AgentForm'
import { api } from '@/lib/api'
import { useRouter } from 'next/navigation'
import { toast } from 'react-hot-toast'

export default function CreateAgentPage() {
  const router = useRouter()

  const handleSubmit = async (data: any) => {
    try {
      await api.agents.create(data)
      toast.success('Agent created successfully!')
      router.push('/agent-marketplace')
    } catch (error) {
      toast.error('Failed to create agent')
      console.error('Create agent error:', error)
    }
  }

  return (
    <AgentForm onSubmit={handleSubmit} />
  )
}
