import { useEffect, useState } from 'react'
import { useSimulationStore } from '@/store'
import { simulationApi } from '@/api/simulation'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loader2, CheckCircle2, XCircle } from 'lucide-react'
import type { FarmTracebackMetricsResponse, FarmTracebackMetric, InvestigationTier } from '@/api/types'

function TierBadge({ tier }: { tier: InvestigationTier }) {
  const styles: Record<InvestigationTier, { bg: string; text: string }> = {
    'Primary Suspect': { bg: 'bg-red-100 dark:bg-red-900', text: 'text-red-700 dark:text-red-300' },
    'Cannot Rule Out': { bg: 'bg-yellow-100 dark:bg-yellow-900', text: 'text-yellow-700 dark:text-yellow-300' },
    'Unlikely': { bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-600 dark:text-gray-400' },
  }
  const style = styles[tier]

  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${style.bg} ${style.text}`}>
      {tier}
    </span>
  )
}

function FarmMetricsTable({
  title,
  farms,
  casesWithTraces,
}: {
  title: string
  farms: FarmTracebackMetric[]
  casesWithTraces: number
}) {
  if (farms.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-4">
        No farms found in traceback
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-sm">{title}</h4>
        <Badge variant="outline" className="text-xs">
          {casesWithTraces} cases
        </Badge>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2 px-1">Farm</th>
              <th className="text-left py-2 px-1">Tier</th>
              <th className="text-right py-2 px-1" title="Cases that ONLY trace to this farm">Excl.</th>
              <th className="text-right py-2 px-1" title="Confidence score (0-1)">Score</th>
            </tr>
          </thead>
          <tbody>
            {farms.map((farm) => (
              <tr
                key={farm.farmId}
                className={`border-b last:border-0 ${farm.isActualSource ? 'bg-green-50 dark:bg-green-950' : ''}`}
              >
                <td className="py-2 px-1">
                  <div className="flex items-center gap-1">
                    {farm.isActualSource && (
                      <span title="Actual Source">
                        <CheckCircle2 className="h-3 w-3 text-green-600" />
                      </span>
                    )}
                    <span className={farm.isActualSource ? 'font-medium' : ''}>
                      {farm.farmName}
                    </span>
                  </div>
                </td>
                <td className="py-2 px-1">
                  <TierBadge tier={farm.tier} />
                </td>
                <td className="text-right py-2 px-1 font-mono">
                  {farm.exclusiveCases}
                </td>
                <td className="text-right py-2 px-1 font-mono">
                  {farm.confidenceScore.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function FarmTracebackMetrics() {
  const simulationId = useSimulationStore((s) => s.simulationId)
  const status = useSimulationStore((s) => s.status)
  const [metrics, setMetrics] = useState<FarmTracebackMetricsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!simulationId || status !== 'completed') {
      setMetrics(null)
      return
    }

    setLoading(true)
    setError(null)

    simulationApi
      .getFarmTracebackMetrics(simulationId)
      .then(setMetrics)
      .catch((err) => setError(err.message || 'Failed to load metrics'))
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

  if (!metrics) {
    return null
  }

  const detPrimarySuspect = metrics.deterministic.farms[0]
  const probPrimarySuspect = metrics.probabilistic.farms[0]
  const actualSource = metrics.actualSource.farmName

  // Check if primary suspect matches actual source
  const detCorrect = detPrimarySuspect?.isActualSource ?? false
  const probCorrect = probPrimarySuspect?.isActualSource ?? false

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center justify-between">
          <span>Farm Traceback Analysis</span>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              Source: {actualSource}
            </Badge>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary */}
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div className="p-2 rounded bg-muted/50">
            <div className="font-medium mb-1">Deterministic Result</div>
            <div className="flex items-center gap-1">
              {detCorrect ? (
                <CheckCircle2 className="h-3 w-3 text-green-600" />
              ) : (
                <XCircle className="h-3 w-3 text-red-500" />
              )}
              <span>{detPrimarySuspect?.farmName || 'None'}</span>
              {detPrimarySuspect && <TierBadge tier={detPrimarySuspect.tier} />}
            </div>
          </div>
          <div className="p-2 rounded bg-muted/50">
            <div className="font-medium mb-1">Probabilistic Result</div>
            <div className="flex items-center gap-1">
              {probCorrect ? (
                <CheckCircle2 className="h-3 w-3 text-green-600" />
              ) : (
                <XCircle className="h-3 w-3 text-red-500" />
              )}
              <span>{probPrimarySuspect?.farmName || 'None'}</span>
              {probPrimarySuspect && <TierBadge tier={probPrimarySuspect.tier} />}
            </div>
          </div>
        </div>

        {/* Side by side tables */}
        <div className="grid grid-cols-2 gap-4">
          <FarmMetricsTable
            title="Deterministic Traceback"
            farms={metrics.deterministic.farms}
            casesWithTraces={metrics.deterministic.casesWithTraces}
          />
          <FarmMetricsTable
            title="Probabilistic Traceback"
            farms={metrics.probabilistic.farms}
            casesWithTraces={metrics.probabilistic.casesWithTraces}
          />
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground pt-2 border-t">
          <div className="flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3 text-green-600" />
            <span>Actual Source</span>
          </div>
          <div className="flex items-center gap-1">
            <TierBadge tier="Cannot Rule Out" />
            <span>Insufficient evidence to exclude</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="font-medium">Excl:</span>
            <span>Cases ONLY tracing to this farm</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
