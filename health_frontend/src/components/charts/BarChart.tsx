import {
  BarChart as RechartsBar, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

interface BarDataPoint {
  label: string
  value: number
  color?: string
}

interface BarChartProps {
  data:    BarDataPoint[]
  height?: number
  unit?:   string
  color?:  string
}

function CustomTooltip({ active, payload, label, unit }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-health-border rounded-xl shadow-card px-3 py-2 text-sm">
      <p className="text-health-muted text-xs mb-0.5">{label}</p>
      <p className="font-semibold text-health-slate">
        {payload[0].value?.toLocaleString()} {unit ?? ''}
      </p>
    </div>
  )
}

export function SimpleBarChart({ data, height = 200, unit, color = '#1D9E75' }: BarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBar data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: '#94a3b8' }}
          axisLine={false} tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: '#94a3b8' }}
          axisLine={false} tickLine={false}
        />
        <Tooltip content={<CustomTooltip unit={unit} />} />
        <Bar dataKey="value" radius={[6, 6, 0, 0]}>
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.color ?? color} fillOpacity={0.85} />
          ))}
        </Bar>
      </RechartsBar>
    </ResponsiveContainer>
  )
}
