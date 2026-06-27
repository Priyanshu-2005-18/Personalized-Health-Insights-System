import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { scoreColor } from '../../utils'

interface DataPoint {
  date: string
  score: number
  label?: string
}

interface HealthTrendChartProps {
  data: DataPoint[]
  height?: number
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  const score = payload[0].value as number
  return (
    <div className="bg-white border border-health-border rounded-xl shadow-card-md px-3 py-2.5 text-sm">
      <p className="text-health-muted text-xs mb-1">{label}</p>
      <p className="font-semibold" style={{ color: scoreColor(score) }}>
        Score: {score.toFixed(1)}
      </p>
    </div>
  )
}

export function HealthTrendChart({ data, height = 200 }: HealthTrendChartProps) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-40 text-health-muted text-sm">
        No trend data yet. Log your health metrics to see your progress.
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: '#94a3b8' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fontSize: 11, fill: '#94a3b8' }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={70} stroke="#e2e8f0" strokeDasharray="4 4" />
        <Line
          type="monotone"
          dataKey="score"
          stroke="#1D9E75"
          strokeWidth={2.5}
          dot={{ r: 3, fill: '#1D9E75', strokeWidth: 0 }}
          activeDot={{ r: 5, fill: '#1D9E75', strokeWidth: 2, stroke: '#fff' }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
