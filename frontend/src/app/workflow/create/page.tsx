'use client'

import { WorkflowForm } from '@/components/forms/WorkflowForm'
import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'

export default function CreateWorkflowPage() {
  const router = useRouter()

  const createWorkflow = useMutation({
    mutationFn: (data: any) => api.workflows.create(data),
    onSuccess: () => {
      router.push('/workflow')
    },
  })

  const handleSubmit = (data: any) => {
    createWorkflow.mutate(data)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <WorkflowForm onSubmit={handleSubmit} />
    </div>
  )
}
