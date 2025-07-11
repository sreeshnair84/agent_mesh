'use client'

import { useState } from 'react'
import { Search, User, Settings, Bell, Menu } from 'lucide-react'
import { useAuth } from '@/lib/auth'

interface HeaderProps {
  onMenuClick?: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const { user, logout } = useAuth()

  return (
    <header className="fixed top-0 left-0 right-0 bg-gradient-to-r from-purple-600 via-purple-700 to-purple-800 shadow-lg z-50 h-16">
      <div className="flex items-center justify-between px-4 sm:px-6 h-full">
        {/* Left Section */}
        <div className="flex items-center space-x-2 sm:space-x-3 min-w-0">
          {onMenuClick && (
            <button
              onClick={onMenuClick}
              className="p-2 hover:bg-white/20 rounded-lg flex-shrink-0 transition-colors"
            >
              <Menu className="w-5 h-5 text-white" />
            </button>
          )}
          <h1 className="text-lg sm:text-xl lg:text-2xl font-bold text-white flex-shrink-0">
            Agent Mesh
          </h1>
        </div>

        {/* Center Section - Search */}
        <div className="flex-1 max-w-md lg:max-w-2xl mx-4 hidden md:block">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-purple-300 w-4 h-4" />
            <input
              type="text"
              placeholder="Search agents, workflows, tools..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white/20 border border-white/30 rounded-lg placeholder-purple-200 text-white focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-white/50 transition-colors"
              suppressHydrationWarning={true}
            />
          </div>
        </div>
        
        {/* Right Section */}
        <div className="flex items-center space-x-1 sm:space-x-2 lg:space-x-3 flex-shrink-0">
          {/* Mobile search button */}
          <button className="p-2 hover:bg-white/20 rounded-lg md:hidden transition-colors">
            <Search className="w-5 h-5 text-white" />
          </button>
          
          <button className="p-2 hover:bg-white/20 rounded-lg relative transition-colors">
            <Bell className="w-5 h-5 text-white" />
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
          </button>
          
          <button className="p-2 hover:bg-white/20 rounded-lg transition-colors">
            <Settings className="w-5 h-5 text-white" />
          </button>
          
          <div className="relative">
            <button className="flex items-center space-x-2 p-2 hover:bg-white/20 rounded-lg transition-colors">
              <User className="w-5 h-5 text-white" />
              <span className="hidden sm:inline text-sm font-medium text-white">
                {user?.name || 'Guest'}
              </span>
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
