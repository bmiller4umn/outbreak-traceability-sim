import { useEffect, useState } from 'react'
import { useSimulationStore, useNetworkStore, selectHasResult } from '@/store'
import { simulationApi } from '@/api/simulation'
import { exportApi } from '@/api/export'
import SupplyChainGraph from '@/components/visualization/SupplyChainGraph'
import ResultsDashboard from '@/components/dashboard/ResultsDashboard'
import EpiCurve from '@/components/dashboard/EpiCurve'
import CaseSummaryDashboard from '@/components/dashboard/CaseSummaryDashboard'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Network, BarChart3, Users, Download, Loader2 } from 'lucide-react'

export default function SimulationPage() {
  const hasResult = useSimulationStore(selectHasResult)
  const simulationId = useSimulationStore((s) => s.simulationId)
  const status = useSimulationStore((s) => s.status)
  const setNodeCaseCounts = useNetworkStore((s) => s.setNodeCaseCounts)

  const [showCaseCounts, setShowCaseCounts] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  const handleExport = async () => {
    if (!simulationId) return

    setIsExporting(true)
    setExportError(null)

    try {
      await exportApi.exportToExcel(simulationId)
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'Export failed')
      console.error('Export failed:', err)
    } finally {
      setIsExporting(false)
    }
  }

  // Load case data when simulation completes
  useEffect(() => {
    if (!simulationId || status !== 'completed') {
      return
    }

    simulationApi
      .getCaseData(simulationId)
      .then((data) => {
        setNodeCaseCounts(data.nodeCaseCounts)
      })
      .catch((err) => {
        console.error('Failed to load case data:', err)
      })
  }, [simulationId, status, setNodeCaseCounts])

  return (
    <div className="h-full flex flex-col">
      <Tabs defaultValue="graph" className="flex-1 flex flex-col">
        <div className="flex items-center justify-between">
          <TabsList className="w-fit">
            <TabsTrigger value="graph" className="flex items-center space-x-2">
              <Network className="h-4 w-4" />
              <span>Network Graph</span>
            </TabsTrigger>
            <TabsTrigger value="cases" className="flex items-center space-x-2" disabled={!hasResult}>
              <Users className="h-4 w-4" />
              <span>Cases</span>
            </TabsTrigger>
            <TabsTrigger value="dashboard" className="flex items-center space-x-2" disabled={!hasResult}>
              <BarChart3 className="h-4 w-4" />
              <span>Results Dashboard</span>
            </TabsTrigger>
          </TabsList>

          {hasResult && (
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-case-counts"
                  checked={showCaseCounts}
                  onCheckedChange={setShowCaseCounts}
                />
                <Label htmlFor="show-case-counts" className="text-sm">
                  Show case counts on graph
                </Label>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={handleExport}
                disabled={isExporting}
              >
                {isExporting ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Download className="h-4 w-4 mr-2" />
                )}
                Export to Excel
              </Button>

              {exportError && (
                <span className="text-sm text-destructive">{exportError}</span>
              )}
            </div>
          )}
        </div>

        <TabsContent value="graph" className="flex-1 mt-4">
          <div className="h-full border rounded-lg overflow-hidden">
            <SupplyChainGraph showCaseCounts={showCaseCounts} />
          </div>
        </TabsContent>

        <TabsContent value="cases" className="flex-1 mt-4 overflow-auto">
          <div className="space-y-4">
            <CaseSummaryDashboard />
            <EpiCurve />
          </div>
        </TabsContent>

        <TabsContent value="dashboard" className="flex-1 mt-4 overflow-auto">
          <ResultsDashboard />
        </TabsContent>
      </Tabs>
    </div>
  )
}
