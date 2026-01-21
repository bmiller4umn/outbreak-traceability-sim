import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { useSimulationStore } from '@/store'
import { simulationApi } from '@/api/simulation'
import type { InvestigationScopeResponse } from '@/api/types'
import InvestigationGraph from './InvestigationGraph'

export default function ScopeComparison() {
  const simulationId = useSimulationStore((s) => s.simulationId)
  const [scopeData, setScopeData] = useState<InvestigationScopeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!simulationId) {
      setScopeData(null)
      return
    }

    const fetchScope = async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await simulationApi.getInvestigationScope(simulationId)
        setScopeData(data)
      } catch (err) {
        setError('Failed to load investigation scope')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchScope()
  }, [simulationId])

  if (!simulationId) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Run a simulation to see investigation scope comparison
        </CardContent>
      </Card>
    )
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Loading investigation scope...
        </CardContent>
      </Card>
    )
  }

  if (error || !scopeData) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          {error || 'No scope data available'}
        </CardContent>
      </Card>
    )
  }

  // Count retail endpoints (delis + retailers) for comparison
  const detEndpoints = scopeData.deterministic.nodes.filter(
    (n) => n.type === 'deli' || n.type === 'retailer'
  ).length
  const probEndpoints = scopeData.probabilistic.nodes.filter(
    (n) => n.type === 'deli' || n.type === 'retailer'
  ).length
  const expansionFactor = probEndpoints / Math.max(1, detEndpoints)

  return (
    <div className="space-y-4">
      {/* Summary Header */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Contamination Spread Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            Compare which retail locations could have received contaminated product.
            With calculated lot codes, investigators must examine{' '}
            <span className="font-bold text-orange-600">{expansionFactor.toFixed(1)}x</span> more
            retail endpoints because the DC cannot definitively track which products went where.
          </p>
          {/* Stats comparison */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-green-50 rounded-lg p-3 border border-green-200">
              <div className="text-sm font-medium text-green-800 mb-2">Deterministic (Full Compliance)</div>
              <div className="grid grid-cols-2 gap-2 text-center">
                <div>
                  <div className="text-lg font-bold text-green-700">{detEndpoints}</div>
                  <div className="text-xs text-green-600">Endpoints</div>
                </div>
                <div>
                  <div className="text-lg font-bold text-green-700">{scopeData.deterministic.nodes.length}</div>
                  <div className="text-xs text-green-600">Total Nodes</div>
                </div>
              </div>
              <div className="text-xs text-green-600 mt-2 text-center">
                Exact locations that received contaminated product
              </div>
            </div>
            <div className="bg-orange-50 rounded-lg p-3 border border-orange-200">
              <div className="text-sm font-medium text-orange-800 mb-2">Probabilistic (Calculated)</div>
              <div className="grid grid-cols-2 gap-2 text-center">
                <div>
                  <div className="text-lg font-bold text-orange-700">{probEndpoints}</div>
                  <div className="text-xs text-orange-600">Endpoints</div>
                </div>
                <div>
                  <div className="text-lg font-bold text-orange-700">{scopeData.probabilistic.nodes.length}</div>
                  <div className="text-xs text-orange-600">Total Nodes</div>
                </div>
              </div>
              <div className="text-xs text-orange-600 mt-2 text-center">
                All locations that COULD have received contaminated product
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Network Graphs - stacked vertically for narrow panels */}
      <div className="space-y-4">
        <div className="h-[350px]">
          <InvestigationGraph
            nodes={scopeData.deterministic.nodes}
            edges={scopeData.deterministic.edges}
            actualSourceFarmId={scopeData.actualSourceFarmId}
            variant="deterministic"
            title={`Confirmed Contaminated (${detEndpoints} endpoints)`}
          />
        </div>
        <div className="h-[350px]">
          <InvestigationGraph
            nodes={scopeData.probabilistic.nodes}
            edges={scopeData.probabilistic.edges}
            actualSourceFarmId={scopeData.actualSourceFarmId}
            variant="probabilistic"
            title={`Possible Contamination (${probEndpoints} endpoints)`}
          />
        </div>
      </div>
    </div>
  )
}
