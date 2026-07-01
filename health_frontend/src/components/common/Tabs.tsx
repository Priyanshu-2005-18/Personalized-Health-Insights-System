import { useState } from 'react'
import { cn } from '../../utils'

interface Tab {
  id:      string
  label:   string
  icon?:   React.ReactNode
  badge?:  number | string
}

interface TabsProps {
  tabs:        Tab[]
  defaultTab?: string
  onChange?:   (id: string) => void
  children:    (activeTab: string) => React.ReactNode
  className?:  string
  size?:       'sm' | 'md'
}

export function Tabs({
  tabs,
  defaultTab,
  onChange,
  children,
  className,
  size = 'md',
}: TabsProps) {
  const [active, setActive] = useState(defaultTab ?? tabs[0]?.id ?? '')

  const select = (id: string) => {
    setActive(id)
    onChange?.(id)
  }

  return (
    <div className={cn('w-full', className)}>
      {/* Tab bar */}
      <div
        role="tablist"
        className="flex gap-0.5 bg-health-surface border border-health-border rounded-xl p-1"
      >
        {tabs.map((tab) => {
          const isActive = tab.id === active
          return (
            <button
              key={tab.id}
              role="tab"
              aria-selected={isActive}
              onClick={() => select(tab.id)}
              className={cn(
                'flex-1 flex items-center justify-center gap-1.5 rounded-lg font-medium transition-all duration-150',
                size === 'sm' ? 'px-3 py-1.5 text-xs' : 'px-4 py-2 text-sm',
                isActive
                  ? 'bg-white shadow-card text-health-slate'
                  : 'text-health-muted hover:text-health-slate'
              )}
            >
              {tab.icon && <span className="shrink-0">{tab.icon}</span>}
              {tab.label}
              {tab.badge != null && (
                <span
                  className={cn(
                    'text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center',
                    isActive
                      ? 'bg-teal-100 text-teal-700'
                      : 'bg-health-border text-health-muted'
                  )}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Tab content */}
      <div className="mt-5" role="tabpanel">
        {children(active)}
      </div>
    </div>
  )
}
