import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn } from '../../utils'

interface StatCardProps {
  label:       string
  value:       string | number
  unit?:       string
  icon?:       React.ReactNode
  iconColor?:  string
  trend?:      number       // positive = up, negative = down, 0 = neutral
  trendLabel?: string
  sublabel?:   string
  className?:  string
  size?:       'sm' | 'md'
}

export function StatCard({
  label,
  value,
  unit,
  icon,
  iconColor = '#1D9E75',
  trend,
  trendLabel,
  sublabel,
  className,
  size = 'md',
}: StatCardProps) {
  const trendColor =
    trend == null   ? ''
    : trend > 0     ? 'text-teal-600'
    : trend < 0     ? 'text-red-500'
    : 'text-health-muted'

  const TrendIcon =
    trend == null   ? null
    : trend > 0     ? TrendingUp
    : trend < 0     ? TrendingDown
    : Minus

  return (
    <div className={cn('card p-4', className)}>
      <div className="flex items-start justify-between gap-2 mb-3">
        {icon && (
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
            style={{ backgroundColor: `${iconColor}15`, color: iconColor }}
          >
            {icon}
          </div>
        )}
        {TrendIcon && (
          <div className={cn('flex items-center gap-1 text-xs font-medium', trendColor)}>
            <TrendIcon className="h-3.5 w-3.5" />
            {trendLabel ?? `${Math.abs(trend!)}%`}
          </div>
        )}
      </div>

      <p className={cn('text-health-muted font-medium mb-0.5', size === 'sm' ? 'text-xs' : 'text-xs')}>
        {label}
      </p>
      <p className={cn('font-bold text-health-slate leading-tight', size === 'sm' ? 'text-lg' : 'text-2xl')}>
        {typeof value === 'number' ? value.toLocaleString() : value}
        {unit && (
          <span className={cn('font-normal text-health-muted ml-1', size === 'sm' ? 'text-xs' : 'text-sm')}>
            {unit}
          </span>
        )}
      </p>
      {sublabel && (
        <p className="text-xs text-health-muted mt-1">{sublabel}</p>
      )}
    </div>
  )
}
