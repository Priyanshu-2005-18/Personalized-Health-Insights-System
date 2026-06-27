import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  ResponsiveContainer, Tooltip,
} from 'recharts'
import type { MetricStatus } from '../../types'

interface MetricRadarChartProps {
  metrics: MetricStatus[]
  height?: number
}

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-health-border rounded-xl shadow-card px-3 py-2 text-xs">
      <p className="font-medium text-health-slate">{payload[0].payload.name}</p>
      <p className="text-teal-600">Score: {payload[0].value?.toFixed(0)}</p>
    </div>
  )
}

export function MetricRadarChart({ metrics, height = 240 }: MetricRadarChartProps) {
  const data = metrics.map((m) => ({
    name: m.name,
    score: Math.round(m.score),
    fullMark: 100,
  }))

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
        <PolarGrid stroke="#e2e8f0" />
        <PolarAngleAxis
          dataKey="name"
          tick={{ fontSize: 10, fill: '#94a3b8' }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Radar
          name="Health"
          dataKey="score"
          stroke="#1D9E75"
          fill="#1D9E75"
          fillOpacity={0.15}
          strokeWidth={2}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}
