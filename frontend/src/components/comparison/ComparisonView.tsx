import { useSimulationStore, selectResult } from '@/store'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import MetricsComparison from './MetricsComparison'
import ScopeChart from './ScopeChart'
import { CheckCircle2, XCircle, AlertTriangle, HelpCircle, Clock } from 'lucide-react'
import type { IdentificationOutcome } from '@/api/types'

// Helper component for displaying identification outcome
function IdentificationBadge({ outcome, sourceRank, margin }: {
  outcome: IdentificationOutcome
  sourceRank: number
  margin: number
}) {
  if (outcome === 'yes') {
    return (
      <div className="flex items-center text-green-600">
        <CheckCircle2 className="h-4 w-4 mr-1" />
        <span className="font-medium">Yes</span>
      </div>
    )
  } else if (outcome === 'no') {
    return (
      <div className="flex items-center text-red-600">
        <XCircle className="h-4 w-4 mr-1" />
        <span className="font-medium">No (Rank: {sourceRank})</span>
      </div>
    )
  } else {
    return (
      <div className="flex items-center text-amber-600">
        <HelpCircle className="h-4 w-4 mr-1" />
        <span className="font-medium">Inconclusive</span>
        <span className="text-xs text-muted-foreground ml-1">(margin: {margin.toFixed(3)})</span>
      </div>
    )
  }
}

export default function ComparisonView() {
  const result = useSimulationStore(selectResult)

  if (!result) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        Run a simulation to see comparison results
      </div>
    )
  }

  const { scenarios, metrics, conclusion } = result

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4">
        {/* Deterministic Scenario */}
        <Card className="border-l-4 border-l-green-500">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Full Compliance</CardTitle>
              <Badge variant="outline" className="bg-green-50">
                Deterministic
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold">{scenarios.deterministic.farmsInScope}</div>
                  <div className="text-xs text-muted-foreground">Farms in Scope</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">{scenarios.deterministic.tlcsInScope}</div>
                  <div className="text-xs text-muted-foreground">TLCs in Scope</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">{scenarios.deterministic.tlcsLocations}</div>
                  <div className="text-xs text-muted-foreground">TLCS (Locations)</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">{scenarios.deterministic.tracebackPaths}</div>
                  <div className="text-xs text-muted-foreground">Traceback Paths</div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t">
                <span className="text-sm">Actual Source:</span>
                <span className="font-medium text-red-600">{scenarios.deterministic.actualSource || 'Unknown'}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm">Primary Suspect:</span>
                <span className="font-medium">{scenarios.deterministic.primarySuspect || 'Unknown'}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm">Source Identified:</span>
                <IdentificationBadge
                  outcome={scenarios.deterministic.identificationOutcome}
                  sourceRank={scenarios.deterministic.sourceRank}
                  margin={scenarios.deterministic.topTwoMargin}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Calculated Scenario */}
        <Card className="border-l-4 border-l-orange-500">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Calculated Lot Codes</CardTitle>
              <Badge variant="outline" className="bg-orange-50">
                Probabilistic
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-orange-600">{scenarios.calculated.farmsInScope}</div>
                  <div className="text-xs text-muted-foreground">Farms in Scope</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-orange-600">{scenarios.calculated.tlcsInScope}</div>
                  <div className="text-xs text-muted-foreground">TLCs in Scope</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-orange-600">{scenarios.calculated.tlcsLocations}</div>
                  <div className="text-xs text-muted-foreground">TLCS (Locations)</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-orange-600">{scenarios.calculated.tracebackPaths}</div>
                  <div className="text-xs text-muted-foreground">Traceback Paths</div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t">
                <span className="text-sm">Actual Source:</span>
                <span className="font-medium text-red-600">{scenarios.calculated.actualSource || 'Unknown'}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm">Primary Suspect:</span>
                <span className="font-medium">{scenarios.calculated.primarySuspect || 'Unknown'}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm">Source Identified:</span>
                <IdentificationBadge
                  outcome={scenarios.calculated.identificationOutcome}
                  sourceRank={scenarios.calculated.sourceRank}
                  margin={scenarios.calculated.topTwoMargin}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Expansion Metrics */}
      <MetricsComparison
        farmExpansion={metrics.farmScopeExpansion}
        tlcExpansion={metrics.tlcScopeExpansion}
        tlcsLocationExpansion={metrics.tlcsLocationExpansion}
        pathExpansion={metrics.pathExpansion}
      />

      {/* Investigation Timing Comparison */}
      {(scenarios.deterministic.investigationTiming || scenarios.calculated.investigationTiming) && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center">
              <Clock className="h-5 w-5 mr-2 text-blue-500" />
              Estimated Investigation Time
            </CardTitle>
            {scenarios.deterministic.investigationTiming && (
              <p className="text-xs text-muted-foreground mt-1">
                Based on {scenarios.deterministic.investigationTiming.numInvestigators} investigators × {scenarios.deterministic.investigationTiming.directWorkHoursPerDay}h direct work/day
              </p>
            )}
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-6">
              {/* Deterministic Timing */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-green-600">Full Compliance</span>
                  {scenarios.deterministic.investigationTiming && (
                    <Badge variant="outline" className="bg-green-50">
                      {scenarios.deterministic.investigationTiming.totalCalendarDays.toFixed(1)} days
                    </Badge>
                  )}
                </div>
                {scenarios.deterministic.investigationTiming && (
                  <div className="text-xs space-y-1 text-muted-foreground">
                    <div className="flex justify-between">
                      <span>Record Requests:</span>
                      <span>{(scenarios.deterministic.investigationTiming.recordRequestHours / 24).toFixed(1)}d wait ({scenarios.deterministic.investigationTiming.locationsContacted} locations)</span>
                    </div>
                    <div className="flex justify-between">
                      <span>TLC Analysis:</span>
                      <span>{scenarios.deterministic.investigationTiming.tlcAnalysisHours.toFixed(1)}h ({scenarios.deterministic.investigationTiming.tlcsAnalyzed} TLCs)</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Traceback:</span>
                      <span>{scenarios.deterministic.investigationTiming.tracebackHours.toFixed(1)}h ({scenarios.deterministic.investigationTiming.pathsTraced} paths)</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Convergence Analysis:</span>
                      <span>{scenarios.deterministic.investigationTiming.convergenceAnalysisHours.toFixed(0)}h</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Farm Verification:</span>
                      <span>{scenarios.deterministic.investigationTiming.farmVerificationHours.toFixed(0)}h ({scenarios.deterministic.investigationTiming.farmsVerified} farms)</span>
                    </div>
                    <div className="flex justify-between font-medium pt-1 border-t">
                      <span>Work Hours:</span>
                      <span>{scenarios.deterministic.investigationTiming.totalWorkHours.toFixed(0)} person-hours</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Probabilistic Timing */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-orange-600">Calculated Lot Codes</span>
                  {scenarios.calculated.investigationTiming && (
                    <Badge variant="outline" className="bg-orange-50">
                      {scenarios.calculated.investigationTiming.totalCalendarDays.toFixed(1)} days
                    </Badge>
                  )}
                </div>
                {scenarios.calculated.investigationTiming && (
                  <div className="text-xs space-y-1 text-muted-foreground">
                    <div className="flex justify-between">
                      <span>Record Requests:</span>
                      <span>{(scenarios.calculated.investigationTiming.recordRequestHours / 24).toFixed(1)}d wait ({scenarios.calculated.investigationTiming.locationsContacted} locations)</span>
                    </div>
                    <div className="flex justify-between">
                      <span>TLC Analysis:</span>
                      <span>{scenarios.calculated.investigationTiming.tlcAnalysisHours.toFixed(1)}h ({scenarios.calculated.investigationTiming.tlcsAnalyzed} TLCs)</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Traceback:</span>
                      <span>{scenarios.calculated.investigationTiming.tracebackHours.toFixed(1)}h ({scenarios.calculated.investigationTiming.pathsTraced} paths)</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Convergence Analysis:</span>
                      <span>{scenarios.calculated.investigationTiming.convergenceAnalysisHours.toFixed(0)}h</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Farm Verification:</span>
                      <span>{scenarios.calculated.investigationTiming.farmVerificationHours.toFixed(0)}h ({scenarios.calculated.investigationTiming.farmsVerified} farms)</span>
                    </div>
                    <div className="flex justify-between font-medium pt-1 border-t">
                      <span>Work Hours:</span>
                      <span>{scenarios.calculated.investigationTiming.totalWorkHours.toFixed(0)} person-hours</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Timing Expansion */}
            {metrics.timingExpansion && metrics.timingExpansion > 1 && (
              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <div className="text-sm text-blue-800">
                  Investigation with calculated lot codes takes approximately{' '}
                  <span className="font-bold">{metrics.timingExpansion.toFixed(1)}x longer</span>{' '}
                  due to the expanded scope of TLCs and traceback paths that must be analyzed.
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Chart Comparison */}
      <ScopeChart
        deterministic={scenarios.deterministic}
        calculated={scenarios.calculated}
      />

      {/* Conclusion */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2 text-amber-500" />
            Impact Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed">{conclusion.impactSummary}</p>

          <div className="mt-4 p-4 bg-muted rounded-lg">
            <div className="text-sm font-medium mb-2">Key Finding:</div>
            <p className="text-sm text-muted-foreground">
              When distribution centers use calculated lot codes instead of exact TLC tracking,
              the investigation scope expands by{' '}
              <span className="font-bold text-orange-600">
                {metrics.farmScopeExpansion.toFixed(1)}x
              </span>{' '}
              for farms and{' '}
              <span className="font-bold text-orange-600">
                {metrics.tlcScopeExpansion.toFixed(1)}x
              </span>{' '}
              for TLCs, potentially leading to larger recalls and more wasted product.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
