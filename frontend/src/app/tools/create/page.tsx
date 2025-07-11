'use client'

import { ToolForm } from '@/components/forms/ToolForm'
import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'

export default function CreateToolPage() {
  const router = useRouter()

  const createTool = useMutation({
    mutationFn: (data: any) => api.tools.create(data),
    onSuccess: () => {
      router.push('/tools')
    },
  })

  const handleSubmit = (data: any) => {
    createTool.mutate(data)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <ToolForm onSubmit={handleSubmit} />
    </div>
  )
}
