import { useEffect, useState } from 'react'
import {
  Lightbulb, RefreshCw, ChevronDown, ChevronUp,
  CheckCircle2, Target, Filter, TrendingUp, AlertTriangle,
} from 'lucide-react'
import { recommendationApi, healthApi } from '../api/health'
import { Card, CardHeader, CardTitle } from '../components/common/Card'
import { Button } from '../components/common/Button'
import { Badge } from '../components/common/Badge'
import { ScoreRing } from '../components/common/ScoreRing'
import { Alert } from '../components/common/Alert'
import { Spinner } from '../components/common/Spinner'
import { MetricRadarChart } from '../components/charts/MetricRadarChart'
import type { HealthInsightsResponse, Recommendation, Priority, Category } from '../types'
import {
  categoryIcon, categoryLabel, getApiError, statusColor,
} from '../utils'

// ─── Single Recommendation Card ───────────────────────────────
function RecCard({ rec }: { rec: Recommendation }) {
  const [expanded, setExpanded] = useState(false)
  const [done, setDone]         = useState<Set<number>>(new Set())

  const priorityColors: Record<Priority, { bg: string; border: string; badge: string }> = {
    critical: { bg: 'bg-red-50',    border: 'border-red-200',    badge: 'bg-red-100 text-red-700' },
    high:     { bg: 'bg-orange-50', border: 'border-orange-200', badge: 'bg-orange-100 text-orange-700' },
    medium:   { bg: 'bg-yellow-50', border: 'border-yellow-200', badge: 'bg-yellow-100 text-yellow-700' },
    low:      { bg: 'bg-teal-50',   border: 'border-teal-200',   badge: 'bg-teal-100 text-teal-700' },
  }
  const colors = priorityColors[rec.priority]

  const toggleDone = (order: number) => {
    setDone((prev) => {
      const next = new Set(prev)
      next.has(order) ? next.delete(order) : next.add(order)
      return next
    })
  }

  return (
    <div className={`card border ${colors.border} overflow-hidden transition-all duration-200`}>
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left p-5"
        aria-expanded={expanded}
      >
        <div className="flex items-start gap-3">
          <span className="text-2xl shrink-0 mt-0.5">{rec.icon}</span>
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${colors.badge}`}>
                {rec.priority.toUpperCase()}
              </span>
              <span className="text-xs text-health-muted">
                {categoryIcon(rec.category)} {categoryLabel(rec.category)}
              </span>
              {rec.score_impact > 0 && (
                <span className="text-xs text-teal-600 font-medium flex items-center gap-0.5">
                  <TrendingUp className="h-3 w-3" />
                  +{rec.score_impact} pts
                </span>
              )}
            </div>
            <h3 className="font-semibold text-health-slate text-sm leading-snug">{rec.title}</h3>
            <p className="text-xs text-health-muted mt-1 leading-relaxed line-clamp-2">
              {rec.summary}
            </p>
          </div>
          <div className="shrink-0 mt-1 text-health-muted">
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </div>
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className={`px-5 pb-5 border-t ${colors.border} ${colors.bg} pt-4`}>
          {/* Detail */}
          <p className="text-sm text-health-slate leading-relaxed mb-4">{rec.detail}</p>

          {/* Metric context */}
          {rec.metric_value != null && rec.target_value && (
            <div className="flex items-center gap-4 mb-4 p-3 bg-white rounded-xl border border-health-border text-sm">
              <div>
                <span className="text-health-muted text-xs">Current</span>
                <p className="font-semibold text-health-slate">{rec.metric_value}</p>
              </div>
              <div className="h-6 w-px bg-health-border" />
              <div>
                <span className="text-health-muted text-xs">Target</span>
                <p className="font-semibold text-teal-600">{rec.target_value}</p>
              </div>
              <Target className="h-4 w-4 text-health-muted ml-auto" />
            </div>
          )}

          {/* Action steps */}
          {rec.actions.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-health-muted uppercase tracking-wider mb-3">
                Action Steps
              </p>
              <div className="space-y-2.5">
                {rec.actions.map((action) => (
                  <button
                    key={action.order}
                    onClick={() => toggleDone(action.order)}
                    className="w-full flex items-start gap-3 text-left group"
                  >
                    <div className={`mt-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-all ${
                      done.has(action.order)
                        ? 'bg-teal-500 border-teal-500'
                        : 'border-health-border group-hover:border-teal-400'
                    }`}>
                      {done.has(action.order) && (
                        <CheckCircle2 className="h-3 w-3 text-white" />
                      )}
                    </div>
                    <div className={`flex-1 transition-opacity ${done.has(action.order) ? 'opacity-50' : ''}`}>
                      <p className={`text-sm leading-snug ${done.has(action.order) ? 'line-through text-health-muted' : 'text-health-slate'}`}>
                        {action.description}
                      </p>
                      <div className="flex flex-wrap gap-x-3 mt-1">
                        {action.duration && (
                          <span className="text-xs text-health-muted">⏱ {action.duration}</span>
                        )}
                        {action.frequency && (
                          <span className="text-xs text-health-muted">🔁 {action.frequency}</span>
                        )}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Tags */}
          {rec.tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-4 pt-4 border-t border-health-border">
              {rec.tags.map((tag) => (
                <span key={tag} className="text-[10px] px-2 py-0.5 bg-white border border-health-border rounded-full text-health-muted">
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Metric status row ─────────────────────────────────────────
function MetricRow({ name, value, unit, status, status_label, target, score }: {
  name: string; value: number | null; unit: string
  status: string; status_label: string; target: string; score: number
}) {
  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-health-border last:border-0">
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="text-sm font-medium text-health-slate">{name}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColor(status)}`}>
            {status_label}
          </span>
        </div>
        <div className="flex items-center gap-3 mt-1">
          <span className="text-xs text-health-muted">
            {value != null ? `${value} ${unit}` : 'No data'}
          </span>
          <span className="text-xs text-health-muted">→ target: {target}</span>
        </div>
        <div className="mt-1.5 h-1.5 bg-health-surface rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${score}%`,
              backgroundColor: score >= 85 ? '#1D9E75' : score >= 70 ? '#14b8a6'
                : score >= 55 ? '#eab308' : score >= 40 ? '#f97316' : '#ef4444',
            }}
          />
        </div>
      </div>
    </div>
  )
}

// ─── Main page ─────────────────────────────────────────────────
export function RecommendationsPage() {
  const [data, setData]         = useState<HealthInsightsResponse | null>(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState<string | null>(null)
  const [filter, setFilter]     = useState<Priority | Category | 'all'>('all')
  const [noMetrics, setNoMetrics] = useState(false)

  const fetchInsights = async () => {
    setLoading(true)
    setError(null)
    setNoMetrics(false)
    try {
      const log = await healthApi.getTodayLog()
      if (!log) {
        setNoMetrics(true)
        return
      }
      const result = await recommendationApi.generate({
        sleep_hours:     (log as any).sleep_hours     ?? undefined,
        steps:           (log as any).steps           ?? undefined,
        calories:        (log as any).calories        ?? undefined,
        water_intake_ml: (log as any).water_ml        ?? undefined,
        stress_level:    log.stress_level             ?? undefined,
        heart_rate_bpm:  (log as any).heart_rate_bpm  ?? undefined,
      })
      setData(result)
    } catch (err) {
      setError(getApiError(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchInsights() }, [])

  const priorities: Priority[]  = ['critical', 'high', 'medium', 'low']
  const categories: Category[]  = ['sleep', 'activity', 'nutrition', 'hydration', 'stress', 'heart_rate']

  const filtered = data?.recommendations.filter((r) => {
    if (filter === 'all') return true
    if (priorities.includes(filter as Priority)) return r.priority === filter
    if (categories.includes(filter as Category)) return r.category === filter
    return true
  }) ?? []

  return (
    <div className="space-y-6 animate-fade-up">

      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-health-slate">Recommendations</h1>
          <p className="text-health-muted text-sm mt-1">
            Personalised health insights based on your logged metrics.
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          leftIcon={<RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />}
          onClick={fetchInsights}
          loading={loading}
        >
          Refresh
        </Button>
      </div>

      {/* ── No data state ──────────────────────────────────────── */}
      {noMetrics && !loading && (
        <Card className="text-center py-12">
          <Lightbulb className="h-10 w-10 text-health-muted mx-auto mb-3" />
          <h2 className="font-semibold text-health-slate mb-1">No health data for today</h2>
          <p className="text-sm text-health-muted mb-5 max-w-sm mx-auto">
            Log your health metrics first to receive personalised recommendations.
          </p>
          <a href="/health-form">
            <Button>Log Today's Metrics</Button>
          </a>
        </Card>
      )}

      {error && <Alert variant="error" message={error} onDismiss={() => setError(null)} />}

      {loading && (
        <div className="flex justify-center py-16">
          <Spinner size="lg" label="Generating your personalised insights…" />
        </div>
      )}

      {data && !loading && (
        <>
          {/* ── Score + summary ──────────────────────────────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            <Card className="flex flex-col items-center justify-center py-7 gap-3">
              <p className="section-label">Overall Health Score</p>
              <ScoreRing score={data.health_score} size={144} strokeWidth={12} />
              {data.score_improvement_potential > 0 && (
                <div className="flex items-center gap-1.5 text-sm text-teal-600 font-medium">
                  <TrendingUp className="h-4 w-4" />
                  Up to +{data.score_improvement_potential} pts possible
                </div>
              )}
              <div className="flex gap-3 text-center mt-1">
                {data.critical_count > 0 && (
                  <div>
                    <p className="text-xl font-bold text-red-600">{data.critical_count}</p>
                    <p className="text-xs text-health-muted">Critical</p>
                  </div>
                )}
                {data.high_count > 0 && (
                  <div>
                    <p className="text-xl font-bold text-orange-500">{data.high_count}</p>
                    <p className="text-xs text-health-muted">High</p>
                  </div>
                )}
                <div>
                  <p className="text-xl font-bold text-health-slate">{data.total_count}</p>
                  <p className="text-xs text-health-muted">Total</p>
                </div>
              </div>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Summary</CardTitle>
                <Badge variant={
                  data.health_score_label === 'Excellent' ? 'success'
                  : data.health_score_label === 'Good'    ? 'success'
                  : data.health_score_label === 'Fair'    ? 'warning'
                  : 'danger'
                }>
                  {data.health_score_label}
                </Badge>
              </CardHeader>
              <p className="text-sm text-health-muted leading-relaxed mb-5">
                {data.overall_summary}
              </p>
              <div className="divide-y divide-health-border">
                {data.metric_statuses.map((ms) => (
                  <MetricRow key={ms.name} {...ms} />
                ))}
              </div>
            </Card>
          </div>

          {/* ── Radar ────────────────────────────────────────────── */}
          <Card>
            <CardHeader>
              <CardTitle>Metric Scores Breakdown</CardTitle>
            </CardHeader>
            <MetricRadarChart metrics={data.metric_statuses} height={260} />
          </Card>

          {/* ── Filter bar ───────────────────────────────────────── */}
          <div className="flex items-center gap-2 flex-wrap">
            <Filter className="h-4 w-4 text-health-muted shrink-0" />
            {(['all', ...priorities, ...categories] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`text-xs px-3 py-1.5 rounded-full font-medium border transition-all ${
                  filter === f
                    ? 'bg-health-green text-white border-health-green'
                    : 'bg-white text-health-muted border-health-border hover:border-health-green hover:text-health-green'
                }`}
              >
                {f === 'all'
                  ? `All (${data.recommendations.length})`
                  : categories.includes(f as Category)
                    ? `${categoryIcon(f as Category)} ${categoryLabel(f as Category)}`
                    : f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>

          {/* ── Warning banner ─────────────────────────────────── */}
          {data.critical_count > 0 && filter === 'all' && (
            <Alert
              variant="error"
              title={`${data.critical_count} critical issue${data.critical_count > 1 ? 's' : ''} detected`}
              message="Please address the critical recommendations below first — they have the biggest impact on your health."
            />
          )}

          {/* ── Recommendation cards ──────────────────────────── */}
          <div className="space-y-3">
            {filtered.length > 0 ? (
              filtered.map((rec) => <RecCard key={rec.id} rec={rec} />)
            ) : (
              <Card className="text-center py-10">
                <p className="text-health-muted text-sm">
                  No recommendations found for the selected filter.
                </p>
              </Card>
            )}
          </div>

          <p className="text-xs text-health-muted text-center pb-4">
            Generated {new Date(data.generated_at).toLocaleString()} · Based on today's logged metrics
          </p>
        </>
      )}
    </div>
  )
}
