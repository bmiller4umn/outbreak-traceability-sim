import { useSimulationStore, selectResult } from '@/store'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import MetricCard from './MetricCard'
import {
  Target,
  Users,
  Boxes,
  TrendingUp,
  CheckCircle2,
  XCircle,
  HelpCircle,
} from 'lucide-react'
import type { IdentificationOutcome } from '@/api/types'

// Helper to get display info for identification outcome
function getOutcomeDisplay(outcome: IdentificationOutcome, sourceRank: number, margin: number) {
  if (outcome === 'yes') {
    return {
      label: 'Correct',
      color: 'text-green-600',
      description: 'Source identified with clear margin',
      icon: CheckCircle2,
      iconColor: 'text-green-500',
    }
  } else if (outcome === 'no') {
    return {
      label: 'Incorrect',
      color: 'text-red-600',
      description: `Wrong source identified (actual: #${sourceRank})`,
      icon: XCircle,
      iconColor: 'text-red-500',
    }
  } else {
    return {
      label: 'Inconclusive',
      color: 'text-amber-600',
      description: `Top farms too close (margin: ${margin.toFixed(3)})`,
      icon: HelpCircle,
      iconColor: 'text-amber-500',
    }
  }
}

export default function ResultsDashboard() {
  const result = useSimulationStore(selectResult)

  if (!result) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        Run a simulation to see results
      </div>
    )
  }

  const { configuration, scenarios, metrics } = result

  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          title="Source Farm"
          value={metrics.sourceFarm || 'Unknown'}
          subtitle="Contamination origin"
          icon={Target}
          variant="default"
        />
        <MetricCard
          title="Total Cases"
          value={scenarios.deterministic.cases}
          subtitle="Illness cases generated"
          icon={Users}
          variant="default"
        />
        <MetricCard
          title="Farm Scope Expansion"
          value={`${metrics.farmScopeExpansion.toFixed(1)}x`}
          subtitle="Calculated vs Deterministic"
          icon={TrendingUp}
          variant={metrics.farmScopeExpansion > 2 ? 'destructive' : 'warning'}
        />
        <MetricCard
          title="TLC Scope Expansion"
          value={`${metrics.tlcScopeExpansion.toFixed(1)}x`}
          subtitle="More lots to investigate"
          icon={Boxes}
          variant={metrics.tlcScopeExpansion > 2 ? 'destructive' : 'warning'}
        />
      </div>

      {/* Accuracy Comparison */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Deterministic Outcome</CardTitle>
          </CardHeader>
          <CardContent>
            {(() => {
              const display = getOutcomeDisplay(
                scenarios.deterministic.identificationOutcome,
                scenarios.deterministic.sourceRank,
                scenarios.deterministic.topTwoMargin
              )
              const Icon = display.icon
              return (
                <div className="flex items-center justify-between">
                  <div>
                    <div className={`text-2xl font-bold ${display.color}`}>
                      {display.label}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {display.description}
                    </div>
                  </div>
                  <Icon className={`h-10 w-10 ${display.iconColor}`} />
                </div>
              )
            })()}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Calculated Outcome</CardTitle>
          </CardHeader>
          <CardContent>
            {(() => {
              const display = getOutcomeDisplay(
                scenarios.calculated.identificationOutcome,
                scenarios.calculated.sourceRank,
                scenarios.calculated.topTwoMargin
              )
              const Icon = display.icon
              return (
                <div className="flex items-center justify-between">
                  <div>
                    <div className={`text-2xl font-bold ${display.color}`}>
                      {display.label}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {display.description}
                    </div>
                  </div>
                  <Icon className={`h-10 w-10 ${display.iconColor}`} />
                </div>
              )
            })()}
          </CardContent>
        </Card>
      </div>

      {/* Farm Probability Distribution */}
      {scenarios.calculated.farmProbabilities && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Farm Probability Distribution (Calculated)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(scenarios.calculated.farmProbabilities)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 5)
                .map(([farmName, probability]) => (
                  <div key={farmName} className="flex items-center space-x-3">
                    <div className="flex-1">
                      <div className="flex justify-between text-sm mb-1">
                        <span>{farmName}</span>
                        <span className="font-mono">{Math.round(probability * 100)}%</span>
                      </div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-orange-500"
                          style={{ width: `${probability * 100}%` }}
                        />
                      </div>
                    </div>
                    {farmName === metrics.sourceFarm && (
                      <Badge variant="default" className="bg-green-500">
                        Source
                      </Badge>
                    )}
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Configuration Summary */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Simulation Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Period:</span>
              <span className="ml-2">
                {configuration.simulationPeriod.start} to {configuration.simulationPeriod.end}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Farms:</span>
              <span className="ml-2 font-medium">{configuration.network.farms}</span>
            </div>
            <div>
              <span className="text-muted-foreground">DCs:</span>
              <span className="ml-2 font-medium">{configuration.network.distributionCenters}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Retailers:</span>
              <span className="ml-2 font-medium">{configuration.network.retailers}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
