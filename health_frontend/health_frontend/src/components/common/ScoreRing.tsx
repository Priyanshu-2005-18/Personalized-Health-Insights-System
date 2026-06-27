import { scoreColor, scoreLabel } from '../../utils'

interface ScoreRingProps {
  score: number
  size?: number
  strokeWidth?: number
  label?: string
  showLabel?: boolean
  animate?: boolean
}

export function ScoreRing({
  score,
  size = 128,
  strokeWidth = 10,
  label,
  showLabel = true,
  animate = true,
}: ScoreRingProps) {
  const radius  = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const clampedScore  = Math.max(0, Math.min(100, score))
  const dashoffset    = circumference * (1 - clampedScore / 100)
  const color         = scoreColor(clampedScore)
  const scoreText     = scoreLabel(clampedScore)

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          {/* Track */}
          <circle
            cx={size / 2} cy={size / 2}
            r={radius}
            fill="none"
            stroke="#e2e8f0"
            strokeWidth={strokeWidth}
          />
          {/* Progress */}
          <circle
            cx={size / 2} cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashoffset}
            style={{
              transition: animate ? 'stroke-dashoffset 1s ease-in-out' : 'none',
            }}
          />
        </svg>

        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold" style={{ color }}>
            {Math.round(clampedScore)}
          </span>
          <span className="text-xs text-health-muted font-medium">/100</span>
        </div>
      </div>

      {showLabel && (
        <span
          className="text-sm font-semibold px-3 py-0.5 rounded-full"
          style={{ color, backgroundColor: `${color}18` }}
        >
          {label ?? scoreText}
        </span>
      )}
    </div>
  )
}
