import { cn } from '../../utils'

interface ProgressBarProps {
  value:      number        // 0–100
  max?:       number
  label?:     string
  showValue?: boolean
  size?:      'sm' | 'md' | 'lg'
  color?:     'green' | 'teal' | 'yellow' | 'orange' | 'red' | 'auto'
  className?: string
  animate?:   boolean
}

function autoColor(pct: number): string {
  if (pct >= 85) return 'bg-health-green'
  if (pct >= 70) return 'bg-teal-500'
  if (pct >= 55) return 'bg-yellow-400'
  if (pct >= 40) return 'bg-orange-400'
  return 'bg-red-500'
}

const colorMap = {
  green:  'bg-health-green',
  teal:   'bg-teal-500',
  yellow: 'bg-yellow-400',
  orange: 'bg-orange-400',
  red:    'bg-red-500',
}

const heightMap = {
  sm: 'h-1.5',
  md: 'h-2.5',
  lg: 'h-4',
}

export function ProgressBar({
  value,
  max = 100,
  label,
  showValue = false,
  size = 'md',
  color = 'auto',
  className,
  animate = true,
}: ProgressBarProps) {
  const pct   = Math.min(100, Math.max(0, (value / max) * 100))
  const track = color === 'auto' ? autoColor(pct) : colorMap[color]

  return (
    <div className={cn('w-full', className)}>
      {(label || showValue) && (
        <div className="flex items-center justify-between mb-1.5">
          {label   && <span className="text-xs font-medium text-health-muted">{label}</span>}
          {showValue && <span className="text-xs font-semibold text-health-slate">{pct.toFixed(0)}%</span>}
        </div>
      )}
      <div className={cn('w-full bg-health-border rounded-full overflow-hidden', heightMap[size])}>
        <div
          className={cn('h-full rounded-full', track, animate && 'transition-all duration-700')}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
    </div>
  )
}
