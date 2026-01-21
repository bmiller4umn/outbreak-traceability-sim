import { useRef, useEffect, useState } from 'react'
import * as d3 from 'd3'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useMonteCarloStore, selectMonteCarloResult } from '@/store'
import StatisticsCard from './StatisticsCard'
import { CheckCircle2, XCircle, HelpCircle, Target, TrendingUp, Download, Loader2, Clock } from 'lucide-react'
import { generateMonteCarloReport } from '@/utils/pdfExport'

function RankDistributionChart({
  deterministicRanks,
  probabilisticRanks,
}: {
  deterministicRanks: Record<number, number>
  probabilisticRanks: Record<number, number>
}) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return

    const container = containerRef.current
    const svg = d3.select(svgRef.current)

    svg.selectAll('*').remove()

    // Combine and sort ranks
    const allRanks = new Set([
      ...Object.keys(deterministicRanks).map(Number),
      ...Object.keys(probabilisticRanks).map(Number),
    ])
    const ranks = Array.from(allRanks).sort((a, b) => a - b).slice(0, 10)

    if (ranks.length === 0) return

    // Dimensions
    const margin = { top: 20, right: 20, bottom: 30, left: 40 }
    const width = container.clientWidth - margin.left - margin.right
    const height = 180 - margin.top - margin.bottom

    const g = svg
      .attr('width', container.clientWidth)
      .attr('height', 180)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Scales
    const x0 = d3.scaleBand().domain(ranks.map(String)).range([0, width]).padding(0.2)
    const x1 = d3.scaleBand().domain(['det', 'prob']).range([0, x0.bandwidth()]).padding(0.05)

    const maxCount = Math.max(
      ...Object.values(deterministicRanks),
      ...Object.values(probabilisticRanks)
    )
    const y = d3.scaleLinear().domain([0, maxCount]).nice().range([height, 0])

    // X axis
    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x0).tickFormat((d) => `#${d}`))

    // Y axis
    g.append('g').call(d3.axisLeft(y).ticks(5))

    // Grouped bars
    const rankGroups = g
      .selectAll('.rank-group')
      .data(ranks)
      .join('g')
      .attr('class', 'rank-group')
      .attr('transform', (d) => `translate(${x0(String(d))},0)`)

    // Deterministic bars
    rankGroups
      .append('rect')
      .attr('x', x1('det') || 0)
      .attr('y', (d) => y(deterministicRanks[d] || 0))
      .attr('width', x1.bandwidth())
      .attr('height', (d) => height - y(deterministicRanks[d] || 0))
      .attr('fill', '#22c55e')

    // Probabilistic bars
    rankGroups
      .append('rect')
      .attr('x', x1('prob') || 0)
      .attr('y', (d) => y(probabilisticRanks[d] || 0))
      .attr('width', x1.bandwidth())
      .attr('height', (d) => height - y(probabilisticRanks[d] || 0))
      .attr('fill', '#f97316')

    // Legend
    const legend = svg
      .append('g')
      .attr('transform', `translate(${margin.left + width - 150}, 5)`)

    legend.append('rect').attr('width', 12).attr('height', 12).attr('fill', '#22c55e')
    legend.append('text').attr('x', 16).attr('y', 10).attr('font-size', '10px').text('Deterministic')

    legend.append('rect').attr('x', 80).attr('width', 12).attr('height', 12).attr('fill', '#f97316')
    legend.append('text').attr('x', 96).attr('y', 10).attr('font-size', '10px').text('Probabilistic')
  }, [deterministicRanks, probabilisticRanks])

  return (
    <div ref={containerRef} className="w-full">
      <svg ref={svgRef} />
    </div>
  )
}

export default function MonteCarloResults() {
  const result = useMonteCarloStore(selectMonteCarloResult)
  const chartsRef = useRef<HTMLDivElement>(null)
  const [isExporting, setIsExporting] = useState(false)

  const handleExport = async () => {
    if (!result) return
    setIsExporting(true)
    try {
      await generateMonteCarloReport(result, chartsRef.current)
    } finally {
      setIsExporting(false)
    }
  }

  if (!result) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        Run a Monte Carlo simulation to see statistical results
      </div>
    )
  }

  const detId = result.deterministicIdentification
  const probId = result.probabilisticIdentification

  return (
    <div className="space-y-4">
      {/* Summary header */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center justify-between">
            <span>Monte Carlo Results</span>
            <div className="flex items-center gap-2">
              <Badge variant="outline">
                {result.iterationsCompleted} iterations
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExport}
                disabled={isExporting}
                className="h-7 text-xs"
              >
                {isExporting ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Download className="h-3.5 w-3.5 mr-1" />
                    Export PDF
                  </>
                )}
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            {/* Identification accuracy comparison */}
            <div className="col-span-2 p-3 rounded-lg bg-muted/50">
              <div className="flex items-center gap-2 mb-2">
                <Target className="h-4 w-4" />
                <span className="text-sm font-medium">Source Identification Outcomes</span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs font-medium mb-1 text-green-700">Deterministic</div>
                  <div className="flex items-center gap-3 text-xs">
                    <div className="flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3 text-green-600" />
                      <span className="font-mono">{(detId.yesRate * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <HelpCircle className="h-3 w-3 text-amber-500" />
                      <span className="font-mono">{(detId.inconclusiveRate * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <XCircle className="h-3 w-3 text-red-500" />
                      <span className="font-mono">{(detId.noRate * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
                <div>
                  <div className="text-xs font-medium mb-1 text-orange-700">Probabilistic</div>
                  <div className="flex items-center gap-3 text-xs">
                    <div className="flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3 text-green-600" />
                      <span className="font-mono">{(probId.yesRate * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <HelpCircle className="h-3 w-3 text-amber-500" />
                      <span className="font-mono">{(probId.inconclusiveRate * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <XCircle className="h-3 w-3 text-red-500" />
                      <span className="font-mono">{(probId.noRate * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Mean expansion */}
            <div className="p-3 rounded-lg bg-muted/50">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4" />
                <span className="text-sm font-medium">Mean Expansion</span>
              </div>
              <div className="text-lg font-bold">
                {result.farmScopeExpansion.mean.toFixed(2)}x
              </div>
              <div className="text-xs text-muted-foreground">
                95% CI: [{result.meanExpansion95CI[0].toFixed(2)}, {result.meanExpansion95CI[1].toFixed(2)}]
              </div>
            </div>

            {/* Statistical significance */}
            <div className="p-3 rounded-lg bg-muted/50">
              <div className="text-sm font-medium mb-2">Statistical Test</div>
              {result.identificationPValue !== null ? (
                <>
                  <div className="flex items-center gap-1">
                    {result.identificationDifferenceSignificant ? (
                      <>
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                        <span className="text-sm font-medium text-green-600">Significant</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Not Significant</span>
                      </>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    p = {result.identificationPValue.toFixed(4)}
                  </div>
                </>
              ) : (
                <div className="text-xs text-muted-foreground">Not computed</div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Charts container for PDF export */}
      <div ref={chartsRef} className="space-y-4">
        {/* Expansion metrics */}
        <div className="grid grid-cols-3 gap-4">
          <StatisticsCard
            title="Farm Scope Expansion"
            stats={result.farmScopeExpansion}
            format="multiplier"
            color="#ef4444"
          />
          <StatisticsCard
            title="TLC Scope Expansion"
            stats={result.tlcScopeExpansion}
            format="multiplier"
            color="#f97316"
          />
          <StatisticsCard
            title="Path Expansion"
            stats={result.pathExpansion}
            format="multiplier"
            color="#eab308"
          />
        </div>

        {/* Investigation timing metrics */}
        {result.detInvestigationDays && result.probInvestigationDays && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Estimated Investigation Time
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-4">
                <div className="text-center p-2 rounded bg-green-50">
                  <div className="text-lg font-bold text-green-700">
                    {result.detInvestigationDays.mean.toFixed(1)}
                  </div>
                  <div className="text-xs text-green-600">Det. Days</div>
                  <div className="text-xs text-muted-foreground">
                    ({result.detInvestigationDays.p5.toFixed(0)}-{result.detInvestigationDays.p95.toFixed(0)})
                  </div>
                </div>
                <div className="text-center p-2 rounded bg-orange-50">
                  <div className="text-lg font-bold text-orange-700">
                    {result.probInvestigationDays.mean.toFixed(1)}
                  </div>
                  <div className="text-xs text-orange-600">Prob. Days</div>
                  <div className="text-xs text-muted-foreground">
                    ({result.probInvestigationDays.p5.toFixed(0)}-{result.probInvestigationDays.p95.toFixed(0)})
                  </div>
                </div>
                {result.timingExpansion && (
                  <div className="text-center p-2 rounded bg-red-50">
                    <div className="text-lg font-bold text-red-700">
                      {result.timingExpansion.mean.toFixed(2)}x
                    </div>
                    <div className="text-xs text-red-600">Time Expansion</div>
                    <div className="text-xs text-muted-foreground">
                      ({result.timingExpansion.p5.toFixed(1)}-{result.timingExpansion.p95.toFixed(1)}x)
                    </div>
                  </div>
                )}
                {result.detInvestigationWorkHours && result.probInvestigationWorkHours && (
                  <div className="text-center p-2 rounded bg-blue-50">
                    <div className="text-lg font-bold text-blue-700">
                      {result.probInvestigationWorkHours.mean.toFixed(0)}
                    </div>
                    <div className="text-xs text-blue-600">Prob. Work Hours</div>
                    <div className="text-xs text-muted-foreground">
                      vs {result.detInvestigationWorkHours.mean.toFixed(0)} det.
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Case metrics */}
        <div className="grid grid-cols-2 gap-4">
          <StatisticsCard
            title="Total Cases per Simulation"
            stats={result.totalCases}
            format="number"
            color="#3b82f6"
          />

          {/* Rank distribution */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Source Rank Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <RankDistributionChart
                deterministicRanks={detId.rankDistribution}
                probabilisticRanks={probId.rankDistribution}
              />
              <div className="grid grid-cols-2 gap-4 mt-2 text-xs">
                <div>
                  <span className="text-muted-foreground">Det. Mean Rank: </span>
                  <span className="font-mono">{detId.meanRank.toFixed(1)}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Prob. Mean Rank: </span>
                  <span className="font-mono">{probId.meanRank.toFixed(1)}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Absolute scope metrics */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Absolute Scope Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-6 gap-4">
              <div className="text-center p-2 rounded bg-green-50">
                <div className="text-lg font-bold text-green-700">
                  {result.detFarmsInScope.mean.toFixed(1)}
                </div>
                <div className="text-xs text-green-600">Det. Farms</div>
              </div>
              <div className="text-center p-2 rounded bg-orange-50">
                <div className="text-lg font-bold text-orange-700">
                  {result.probFarmsInScope.mean.toFixed(1)}
                </div>
                <div className="text-xs text-orange-600">Prob. Farms</div>
              </div>
              <div className="text-center p-2 rounded bg-green-50">
                <div className="text-lg font-bold text-green-700">
                  {result.detTlcsInScope.mean.toFixed(1)}
                </div>
                <div className="text-xs text-green-600">Det. TLCs</div>
              </div>
              <div className="text-center p-2 rounded bg-orange-50">
                <div className="text-lg font-bold text-orange-700">
                  {result.probTlcsInScope.mean.toFixed(1)}
                </div>
                <div className="text-xs text-orange-600">Prob. TLCs</div>
              </div>
              <div className="text-center p-2 rounded bg-green-50">
                <div className="text-lg font-bold text-green-700">
                  {result.detTlcsLocations.mean.toFixed(1)}
                </div>
                <div className="text-xs text-green-600">Det. TLCS</div>
              </div>
              <div className="text-center p-2 rounded bg-orange-50">
                <div className="text-lg font-bold text-orange-700">
                  {result.probTlcsLocations.mean.toFixed(1)}
                </div>
                <div className="text-xs text-orange-600">Prob. TLCS</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
