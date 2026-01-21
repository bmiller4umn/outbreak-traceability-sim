import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Loader2, Users, Cross, MessageSquare, MapPin, Calendar, Clock } from 'lucide-react'
import { useSimulationStore } from '@/store'
import { simulationApi } from '@/api/simulation'
import type { CaseSummary } from '@/api/types'
import MetricCard from './MetricCard'

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export default function CaseSummaryDashboard() {
  const simulationId = useSimulationStore((s) => s.simulationId)
  const status = useSimulationStore((s) => s.status)

  const [summary, setSummary] = useState<CaseSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!simulationId || status !== 'completed') {
      setSummary(null)
      return
    }

    setLoading(true)
    setError(null)

    simulationApi
      .getCaseData(simulationId)
      .then((data) => setSummary(data.summary))
      .catch((err) => setError(err.message || 'Failed to load case summary'))
      .finally(() => setLoading(false))
  }, [simulationId, status])

  if (!simulationId || status !== 'completed') {
    return null
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="py-8 flex items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-4 text-center text-destructive text-sm">
          {error}
        </CardContent>
      </Card>
    )
  }

  if (!summary) {
    return null
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Case Summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Primary metrics row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <MetricCard
            title="Total Cases"
            value={summary.totalCases}
            icon={Users}
            variant="destructive"
          />
          <MetricCard
            title="Hospitalized"
            value={summary.hospitalizedCases}
            subtitle={`${summary.hospitalizationRate}%`}
            icon={Cross}
            variant="warning"
          />
          <MetricCard
            title="Interviewed"
            value={summary.interviewedCases}
            subtitle={`${summary.interviewRate}%`}
            icon={MessageSquare}
            variant="default"
          />
          <MetricCard
            title="Location Known"
            value={summary.casesWithExposureLocation}
            subtitle={`${summary.exposureLocationRate}%`}
            icon={MapPin}
            variant="success"
          />
        </div>

        {/* Timeline info */}
        <div className="grid grid-cols-3 gap-3 text-xs">
          <div className="p-3 rounded-lg bg-muted/50 space-y-1">
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <Calendar className="h-3.5 w-3.5" />
              <span>First Case</span>
            </div>
            <div className="font-medium">{formatDate(summary.earliestOnset)}</div>
          </div>
          <div className="p-3 rounded-lg bg-muted/50 space-y-1">
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <Calendar className="h-3.5 w-3.5" />
              <span>Latest Case</span>
            </div>
            <div className="font-medium">{formatDate(summary.latestOnset)}</div>
          </div>
          <div className="p-3 rounded-lg bg-muted/50 space-y-1">
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <Clock className="h-3.5 w-3.5" />
              <span>Duration</span>
            </div>
            <div className="font-medium">{summary.outbreakDurationDays} days</div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
