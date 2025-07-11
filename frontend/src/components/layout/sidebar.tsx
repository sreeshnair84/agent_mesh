'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  ChevronLeft,
  ChevronRight,
  Store,
  Workflow,
  Wrench,
  BarChart3,
  Settings,
  ChevronDown,
  ChevronUp,
  X,
} from 'lucide-react'

const menuItems = [
  { href: '/agent-marketplace' as const, label: 'Agent Marketplace', icon: Store },
  { href: '/workflow' as const, label: 'Agentic Workflow', icon: Workflow },
  { href: '/tools' as const, label: 'Tools', icon: Wrench },
  { href: '/observability' as const, label: 'Observability', icon: BarChart3 },
  {
    href: '/master-data' as const,
    label: 'Master Data',
    icon: Settings,
    subItems: [
      { href: '/master-data/skills' as const, label: 'Skills' },
      { href: '/master-data/constraints' as const, label: 'Constraints' },
      { href: '/master-data/prompts' as const, label: 'Prompts' },
      { href: '/master-data/models' as const, label: 'BYOModel' },
      { href: '/master-data/secrets' as const, label: 'Env Secrets' },
    ],
  },
]

interface SidebarProps {
  sidebarOpen?: boolean
  setSidebarOpen?: (open: boolean) => void
}

export function Sidebar({ sidebarOpen, setSidebarOpen }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [expandedItems, setExpandedItems] = useState<string[]>([])
  const pathname = usePathname()

  const toggleExpanded = (href: string) => {
    setExpandedItems(prev =>
      prev.includes(href)
        ? prev.filter(item => item !== href)
        : [...prev, href]
    )
  }

  return (
    <>
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-gray-900/80" onClick={() => setSidebarOpen?.(false)} />
          <div className="fixed left-0 top-16 bottom-0 z-50 w-64 bg-gray-50 border-r">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">Menu</h2>
              <button
                onClick={() => setSidebarOpen?.(false)}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <nav className="p-4 space-y-2 overflow-y-auto h-full">
              {menuItems.map((item) => (
                <div key={item.href}>
                  <Link
                    href={item.href as any}
                    onClick={(e) => {
                      if (item.subItems) {
                        e.preventDefault()
                        toggleExpanded(item.href)
                      } else {
                        setSidebarOpen?.(false)
                      }
                    }}
                    className={`flex items-center justify-between p-3 rounded-lg hover:bg-gray-100 ${
                      pathname === item.href || pathname.startsWith(item.href + '/') 
                        ? 'bg-primary-100 text-primary-700' 
                        : 'text-gray-700'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <item.icon className="w-5 h-5" />
                      <span>{item.label}</span>
                    </div>
                    {item.subItems && (
                      expandedItems.includes(item.href) ? 
                        <ChevronUp className="w-4 h-4" /> : 
                        <ChevronDown className="w-4 h-4" />
                    )}
                  </Link>
                  
                  {item.subItems && expandedItems.includes(item.href) && (
                    <div className="ml-8 mt-2 space-y-1">
                      {item.subItems.map((subItem) => (
                        <Link
                          key={subItem.href}
                          href={subItem.href as any}
                          onClick={() => setSidebarOpen?.(false)}
                          className={`block p-2 rounded-lg text-sm hover:bg-gray-100 ${
                            pathname === subItem.href ? 'bg-primary-100 text-primary-700' : 'text-gray-600'
                          }`}
                        >
                          {subItem.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </nav>
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <aside className={`fixed left-0 top-16 bottom-0 bg-gray-50 border-r transition-all duration-300 z-30 ${
        sidebarOpen ? 'w-64' : 'w-0'
      } lg:block hidden`}>
        <div className="h-full overflow-hidden">
          <div className="p-4">
            <button
              onClick={() => setSidebarOpen?.(false)}
              className="w-full flex justify-end p-2 hover:bg-gray-100 rounded-lg"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
          </div>
          
          <nav className="px-4 overflow-y-auto h-full pb-20">
            {menuItems.map((item) => (
              <div key={item.href} className="mb-2">
                <Link
                  href={item.href as any}
                  onClick={(e) => {
                    if (item.subItems) {
                      e.preventDefault()
                      toggleExpanded(item.href)
                    }
                  }}
                  className={`flex items-center justify-between p-3 rounded-lg hover:bg-gray-100 ${
                    pathname === item.href || pathname.startsWith(item.href + '/') 
                      ? 'bg-primary-100 text-primary-700' 
                      : 'text-gray-700'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <item.icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </div>
                  {item.subItems && (
                    expandedItems.includes(item.href) ? 
                      <ChevronUp className="w-4 h-4" /> : 
                      <ChevronDown className="w-4 h-4" />
                  )}
                </Link>
                
                {item.subItems && expandedItems.includes(item.href) && (
                  <div className="ml-8 mt-2 space-y-1">
                    {item.subItems.map((subItem) => (
                      <Link
                        key={subItem.href}
                        href={subItem.href as any}
                        className={`block p-2 rounded-lg text-sm hover:bg-gray-100 ${
                          pathname === subItem.href ? 'bg-primary-100 text-primary-700' : 'text-gray-600'
                        }`}
                      >
                        {subItem.label}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </nav>
        </div>
      </aside>
    </>
  )
}