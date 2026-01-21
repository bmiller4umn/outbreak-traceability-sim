import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { useMonteCarloStore, useConfigStore, selectMaxMonteCarloIterations } from '@/store'
import { Play, Square, RotateCcw, ChevronDown, ChevronUp, Info } from 'lucide-react'

export default function MonteCarloControls() {
  const config = useMonteCarloStore((s) => s.config)
  const status = useMonteCarloStore((s) => s.status)
  const setConfig = useMonteCarloStore((s) => s.setConfig)
  const startMonteCarlo = useMonteCarloStore((s) => s.startMonteCarlo)
  const cancelMonteCarlo = useMonteCarloStore((s) => s.cancelMonteCarlo)
  const clearResult = useMonteCarloStore((s) => s.clearResult)
  const [showConfig, setShowConfig] = useState(false)

  // Fetch app config on mount
  const fetchConfig = useConfigStore((s) => s.fetchConfig)
  const maxIterations = useConfigStore(selectMaxMonteCarloIterations)

  useEffect(() => {
    fetchConfig()
  }, [fetchConfig])

  const isRunning = status === 'running'
  const hasResult = status === 'completed'

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm">Monte Carlo Configuration</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Info about synced config */}
        <div className="flex items-start gap-2 p-2 bg-blue-50 rounded text-xs text-blue-700">
          <Info className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />
          <span>
            Simulation parameters are synced from the main Configuration panel.
            Adjust sliders there to change contamination rate, interview success rate, etc.
          </span>
        </div>

        {/* Iteration count */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label className="text-xs">Iterations</Label>
            <span className="text-xs font-mono text-muted-foreground">{config.numIterations}</span>
          </div>
          <Slider
            value={[Math.min(config.numIterations, maxIterations)]}
            onValueChange={([v]) => setConfig({ numIterations: v })}
            min={10}
            max={maxIterations}
            step={10}
            disabled={isRunning}
          />
          <p className="text-xs text-muted-foreground">
            More iterations = more accurate statistics but longer runtime
          </p>
        </div>

        {/* Random seed */}
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <Label className="text-xs">Random Seed (for reproducibility)</Label>
            <span className="text-xs font-mono">
              {config.baseRandomSeed ?? 'random'}
            </span>
          </div>
          <div className="flex gap-2">
            <Slider
              value={[config.baseRandomSeed ?? 0]}
              onValueChange={([v]) => setConfig({ baseRandomSeed: v === 0 ? null : v })}
              min={0}
              max={10000}
              step={1}
              disabled={isRunning}
              className="flex-1"
            />
          </div>
          <p className="text-xs text-muted-foreground">
            Set to 0 for random seeds, or a value for reproducible results
          </p>
        </div>

        {/* Collapsible config summary */}
        <div className="border rounded">
          <button
            className="w-full flex items-center justify-between p-2 text-xs font-medium hover:bg-muted/50"
            onClick={() => setShowConfig(!showConfig)}
          >
            <span>Simulation Parameters (from Config panel)</span>
            {showConfig ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>
          {showConfig && (
            <div className="p-2 border-t bg-muted/30 space-y-1 text-xs">
              <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Farms:</span>
                  <span className="font-mono">{config.numFarms}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Retailers:</span>
                  <span className="font-mono">{config.numRetailers}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Contamination:</span>
                  <span className="font-mono">{(config.contaminationRate * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Duration:</span>
                  <span className="font-mono">{config.contaminationDurationDays}d</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Interview Rate:</span>
                  <span className="font-mono">{config.interviewSuccessRate}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Record Window:</span>
                  <span className="font-mono">{config.recordCollectionWindowDays}d</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Lot Code Strategy:</span>
                  <span className="font-mono">{config.inventoryStrategy}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Sim Days:</span>
                  <span className="font-mono">{config.simulationDays}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex gap-2 pt-2">
          {isRunning ? (
            <Button
              variant="destructive"
              className="flex-1"
              onClick={cancelMonteCarlo}
            >
              <Square className="h-4 w-4 mr-2" />
              Cancel
            </Button>
          ) : (
            <Button
              className="flex-1"
              onClick={startMonteCarlo}
              disabled={isRunning}
            >
              <Play className="h-4 w-4 mr-2" />
              Run Monte Carlo
            </Button>
          )}
          {hasResult && (
            <Button variant="outline" onClick={clearResult}>
              <RotateCcw className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
