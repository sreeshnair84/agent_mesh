'use client'

import { useState } from 'react'
import { Header } from './header'
import { Sidebar } from './sidebar'
import { ClientOnly } from '@/components/ClientOnly'

interface MainLayoutProps {
  children: React.ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Fixed Header at Top */}
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
      
      {/* Main Content Area with Sidebar */}
      <div className="flex">
        {/* Sidebar - Wrapped in ClientOnly to prevent hydration mismatch */}
        <ClientOnly>
          <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
        </ClientOnly>
        
        {/* Main Content - Responsive margin based on sidebar state */}
        <main className={`flex-1 pt-16 transition-all duration-300 ${
          sidebarOpen ? 'lg:ml-64' : 'lg:ml-0'
        }`}>
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
