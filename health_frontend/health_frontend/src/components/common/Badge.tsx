import React from 'react'
import { cn } from '../../utils'
import type { Priority } from '../../types'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'muted'
  priority?: Priority
  size?: 'sm' | 'md'
}

const variantMap = {
  default: 'bg-health-surface text-health-slate border border-health-border',
  success: 'bg-teal-50 text-teal-700 border border-teal-200',
  warning: 'bg-yellow-50 text-yellow-700 border border-yellow-200',
  danger:  'bg-red-50 text-red-700 border border-red-200',
  info:    'bg-blue-50 text-blue-700 border border-blue-200',
  muted:   'bg-gray-50 text-gray-500 border border-gray-200',
}

const priorityMap: Record<Priority, string> = {
  critical: 'bg-red-100 text-red-700 border border-red-200',
  high:     'bg-orange-50 text-orange-700 border border-orange-200',
  medium:   'bg-yellow-50 text-yellow-700 border border-yellow-200',
  low:      'bg-teal-50 text-teal-700 border border-teal-200',
}

export function Badge({
  variant = 'default',
  priority,
  size = 'sm',
  children,
  className,
  ...props
}: BadgeProps) {
  const base = priority ? priorityMap[priority] : variantMap[variant]
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 font-medium rounded-full',
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm',
        base,
        className
      )}
      {...props}
    >
      {children}
    </span>
  )
}
