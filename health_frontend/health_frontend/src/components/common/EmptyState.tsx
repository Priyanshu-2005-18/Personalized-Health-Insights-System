import { cn } from '../../utils'

interface EmptyStateProps {
  icon?:        React.ReactNode
  title:        string
  description?: string
  action?:      React.ReactNode
  className?:   string
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)}>
      {icon && (
        <div className="w-14 h-14 bg-health-surface rounded-2xl flex items-center justify-center mb-4 text-health-muted">
          {icon}
        </div>
      )}
      <h3 className="font-semibold text-health-slate mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-health-muted max-w-xs leading-relaxed mb-5">
          {description}
        </p>
      )}
      {action}
    </div>
  )
}
