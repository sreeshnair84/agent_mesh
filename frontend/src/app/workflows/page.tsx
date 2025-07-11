import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { WorkflowDashboard } from '@/components/workflows/workflow-dashboard'

export default function WorkflowsPage() {
  return (
    <DashboardLayout>
      <WorkflowDashboard />
    </DashboardLayout>
  )
}
