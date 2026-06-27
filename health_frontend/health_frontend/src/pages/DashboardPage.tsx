import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Moon, Footprints, Flame, Droplets,
  Brain, Heart, ArrowRight, TrendingUp,
  ClipboardList, Lightbulb, Plus,
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { healthApi, recommendationApi } from '../api/health'
import { Card, CardHeader, CardTitle } from '../components/common/Card'
import { Button } from '../components/common/Button'
import { Badge } from '../components/common/Badge'
import { ScoreRing } from '../components/common/ScoreRing'
import { Spinner } from '../components/common/Spinner'
import { HealthTrendChart } from '../components/charts/HealthTrendChart'
import { MetricRadarChart } from '../components/charts/MetricRadarChart'
import type { HealthLog, HealthInsightsResponse, MetricStatus } from '../types'
import { formatDate, scoreColor, statusColor, today } from '../utils'

// ─── Metric card definition ───────────────────────────────────
interface MetricDef {
  key:    keyof HealthLog
  label:  string
  icon:   React.ReactNode
  unit:   string
  color:  string
  target: string
  format: (v: number) => string
}

const METRICS: MetricDef[] = [
  {
    key:    'sleep_hours' as any,
    label:  'Sleep',
    icon:   <Moon className="h-4 w-4" />,
    unit:   'h',
    color:  '#8b5cf6',
    target: '7–9h',
    format: (v) => v.toFixed(1),
  },
  {
    key:    'steps' as any,
    label:  'Steps',
    icon:   <Footprints className="h-4 w-4" />,
    unit:   '',
    color:  '#1D9E75',
    target: '10,000',
    format: (v) => v.toLocaleString(),
  },
  {
    key:    'calories' as any,
    label:  'Calories',
    icon:   <Flame className="h-4 w-4" />,
    unit:   'kcal',
    color:  '#f97316',
    target: '1600–2400',
    format: (v) => v.toLocaleString(),
  },
  {
    key:    'water_intake_ml' as any,
    label:  'Water',
    icon:   <Droplets className="h-4 w-4" />,
    unit:   'ml',
    color:  '#0891b2',
    target: '2000–3000ml',
    format: (v) => v.toLocaleString(),
  },
  {
    key:    'stress_level' as any,
    label:  'Stress',
    icon:   <Brain className="h-4 w-4" />,
    unit:   '/10',
    color:  '#ef4444',
    target: '1–3',
    format: (v) => v.toString(),
  },
  {
    key:    'heart_rate_bpm' as any,
    label:  'Heart Rate',
    icon:   <Heart className="h-4 w-4" />,
    unit:   'bpm',
    color:  '#ec4899',
    target: '55–75',
    format: (v) => v.toString(),
  },
]

// ─── Quick stat card ──────────────────────────────────────────
function StatCard({
  label, value, unit, icon, color, target, hasData,
}: {
  label: string; value: string | null; unit: string
  icon: React.ReactNode; color: string; target: string; hasData: boolean
}) {
  return (
    <div className="card p-4 flex items-start gap-3">
      <div
        className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
        style={{ backgroundColor: `${color}18`, color }}
      >
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-health-muted font-medium mb-0.5">{label}</p>
        {hasData && value ? (
          <p className="text-lg font-bold text-health-slate leading-tight">
            {value}
            <span className="text-xs font-normal text-health-muted ml-1">{unit}</span>
          </p>
        ) : (
          <p className="text-sm text-health-muted">—</p>
        )}
        <p className="text-[10px] text-health-muted mt-0.5">Target: {target}</p>
      </div>
    </div>
  )
}

export function DashboardPage() {
  const { user } = useAuthStore()
  const [todayLog, setTodayLog]       = useState<HealthLog | null>(null)
  const [recentLogs, setRecentLogs]   = useState<HealthLog[]>([])
  const [insights, setInsights]       = useState<HealthInsightsResponse | null>(null)
  const [loading, setLoading]         = useState(true)
  const [insightsLoading, setInsightsLoading] = useState(false)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const [tLog, logs] = await Promise.all([
          healthApi.getTodayLog(),
          healthApi.listLogs({ limit: 14 }),
        ])
        setTodayLog(tLog)
        setRecentLogs(logs)

        // Auto-generate insights if today's log exists
        if (tLog) {
          setInsightsLoading(true)
          try {
            const ins = await recommendationApi.getQuick({
              sleep_hours:     tLog.sleep_hours     ?? undefined,
              steps:           tLog.steps           ?? undefined,
              calories:        tLog.calories        ?? undefined,
              water_intake_ml: tLog.water_ml        ?? undefined,  // water_ml → water_intake_ml
              stress_level:    tLog.stress_level    ?? undefined,
              heart_rate_bpm:  tLog.heart_rate_bpm  ?? undefined,
            })
            setInsights(ins)
          } finally {
            setInsightsLoading(false)
          }
        }
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  // Build trend chart data
  const trendData = [...recentLogs]
    .reverse()
    .filter((l) => (l as any).health_score != null)
    .map((l) => ({
      date:  formatDate(l.log_date ?? l.created_at),
      score: (l as any).health_score as number,
    }))

  const hour = new Date().getHours()
  const greeting =
    hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
  const firstName = user?.full_name?.split(' ')[0] ?? user?.username ?? 'there'

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" label="Loading your dashboard…" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-up">

      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-health-muted text-sm">{greeting} 👋</p>
          <h1 className="text-2xl font-bold text-health-slate mt-0.5">{firstName}</h1>
          <p className="text-health-muted text-sm mt-1">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
          </p>
        </div>
        <Link to="/health-form">
          <Button leftIcon={<Plus className="h-4 w-4" />} size="sm">
            Log Today
          </Button>
        </Link>
      </div>

      {/* ── Top row: score + radar ──────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* Health Score */}
        <Card className="flex flex-col items-center justify-center py-8 gap-4">
          {insights ? (
            <>
              <p className="section-label">Today's Health Score</p>
              <ScoreRing score={insights.health_score} size={144} strokeWidth={12} />
              <div className="text-center px-4">
                <p className="text-sm text-health-muted leading-relaxed line-clamp-3">
                  {insights.overall_summary.slice(0, 120)}…
                </p>
              </div>
              {insights.score_improvement_potential > 0 && (
                <Badge variant="info" size="md">
                  <TrendingUp className="h-3 w-3" />
                  +{insights.score_improvement_potential} pts potential
                </Badge>
              )}
            </>
          ) : (
            <div className="text-center px-6">
              <div className="w-16 h-16 bg-health-surface rounded-full flex items-center justify-center mx-auto mb-4">
                <ClipboardList className="h-7 w-7 text-health-muted" />
              </div>
              <p className="font-medium text-health-slate mb-1">No data for today</p>
              <p className="text-sm text-health-muted mb-5">
                Log your health metrics to get your personalised score and recommendations.
              </p>
              <Link to="/health-form">
                <Button size="sm">Log Today's Data</Button>
              </Link>
            </div>
          )}
        </Card>

        {/* Radar chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Metric Overview</CardTitle>
            {insights && (
              <Badge variant="muted">
                {insights.total_count} recommendations
              </Badge>
            )}
          </CardHeader>
          {insights?.metric_statuses?.length ? (
            <MetricRadarChart metrics={insights.metric_statuses} height={220} />
          ) : (
            <div className="flex items-center justify-center h-48 text-health-muted text-sm">
              Log your metrics to see the radar chart
            </div>
          )}
        </Card>
      </div>

      {/* ── 6 metric stat cards ─────────────────────────────────── */}
      <div>
        <p className="section-label mb-3">Today's Metrics</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3">
          {METRICS.map((m) => {
            const raw = todayLog ? (todayLog as any)[m.key] : null
            return (
              <StatCard
                key={m.key as string}
                label={m.label}
                value={raw != null ? m.format(raw) : null}
                unit={m.unit}
                icon={m.icon}
                color={m.color}
                target={m.target}
                hasData={raw != null}
              />
            )
          })}
        </div>
      </div>

      {/* ── Trend chart + quick recommendations ─────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* Trend */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Health Score Trend</CardTitle>
            <Badge variant="muted">Last 14 days</Badge>
          </CardHeader>
          <HealthTrendChart data={trendData} height={200} />
        </Card>

        {/* Quick recs */}
        <Card>
          <CardHeader>
            <CardTitle>Top Insights</CardTitle>
            <Link to="/recommendations">
              <button className="text-xs text-health-green hover:underline font-medium flex items-center gap-1">
                View all <ArrowRight className="h-3 w-3" />
              </button>
            </Link>
          </CardHeader>

          {insightsLoading ? (
            <div className="flex justify-center py-8"><Spinner size="md" /></div>
          ) : insights?.recommendations.length ? (
            <div className="space-y-3">
              {insights.recommendations.slice(0, 3).map((rec) => (
                <div key={rec.id} className="flex items-start gap-2.5 p-3 bg-health-surface rounded-xl">
                  <span className="text-lg shrink-0 mt-0.5">{rec.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <Badge priority={rec.priority} size="sm">
                        {rec.priority}
                      </Badge>
                    </div>
                    <p className="text-sm font-medium text-health-slate leading-tight line-clamp-2">
                      {rec.title}
                    </p>
                  </div>
                </div>
              ))}
              <Link to="/recommendations">
                <Button variant="secondary" size="sm" fullWidth
                  rightIcon={<ArrowRight className="h-3.5 w-3.5" />}
                  className="mt-2"
                >
                  See all recommendations
                </Button>
              </Link>
            </div>
          ) : (
            <div className="text-center py-8">
              <Lightbulb className="h-8 w-8 text-health-muted mx-auto mb-2" />
              <p className="text-sm text-health-muted">
                Log your health data to receive personalised recommendations.
              </p>
            </div>
          )}
        </Card>
      </div>

      {/* ── Recent logs table ─────────────────────────────────────── */}
      {recentLogs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Health Logs</CardTitle>
            <Badge variant="muted">{recentLogs.length} entries</Badge>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-health-border">
                  {['Date', 'Mood', 'Stress', 'Energy', 'Water', 'Notes'].map((h) => (
                    <th key={h} className="text-left text-xs font-medium text-health-muted py-2 px-3 first:pl-0">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-health-border">
                {recentLogs.slice(0, 7).map((log) => (
                  <tr key={log.id} className="hover:bg-health-surface/50 transition-colors">
                    <td className="py-2.5 px-3 first:pl-0 font-medium text-health-slate whitespace-nowrap">
                      {formatDate(log.log_date ?? log.created_at)}
                    </td>
                    <td className="py-2.5 px-3">
                      {log.mood_score != null ? (
                        <span className="font-medium">{log.mood_score}/10</span>
                      ) : <span className="text-health-muted">—</span>}
                    </td>
                    <td className="py-2.5 px-3">
                      {log.stress_level != null ? (
                        <span className="font-medium">{log.stress_level}/10</span>
                      ) : <span className="text-health-muted">—</span>}
                    </td>
                    <td className="py-2.5 px-3">
                      {log.energy_level != null ? (
                        <span className="font-medium">{log.energy_level}/10</span>
                      ) : <span className="text-health-muted">—</span>}
                    </td>
                    <td className="py-2.5 px-3">
                      {log.water_ml != null ? (
                        <span className="font-medium">{log.water_ml}ml</span>
                      ) : <span className="text-health-muted">—</span>}
                    </td>
                    <td className="py-2.5 px-3 max-w-[160px] truncate text-health-muted">
                      {log.notes ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
