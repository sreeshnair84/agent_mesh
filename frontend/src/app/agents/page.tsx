import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { AgentMarketplace } from '@/components/agents/agent-marketplace'

export default function AgentsPage() {
  return (
    <DashboardLayout>
      <AgentMarketplace />
    </DashboardLayout>
  )
}
