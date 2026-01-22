import { useSimulationStore, selectConfig, selectIsRunning } from '@/store'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Play, RotateCcw, Loader2, ChevronDown, ChevronRight } from 'lucide-react'
import { useState } from 'react'
import type { InventoryStrategy } from '@/api/types'

const inventoryStrategies: { value: InventoryStrategy; label: string; description: string }[] = [
  { value: 'FIFO', label: 'FIFO', description: 'First-In-First-Out - Ship oldest inventory first' },
  { value: 'LIFO', label: 'LIFO', description: 'Last-In-First-Out - Ship newest inventory first' },
  { value: 'ALL_IN_WINDOW', label: 'All in Window', description: 'All lots in date window equally likely' },
  { value: 'INVENTORY_WEIGHTED', label: 'Inventory Weighted', description: 'Weighted by remaining inventory' },
]

export default function SimulationControls() {
  const config = useSimulationStore(selectConfig)
  const isRunning = useSimulationStore(selectIsRunning)
  const setConfig = useSimulationStore((s) => s.setConfig)
  const startSimulation = useSimulationStore((s) => s.startSimulation)
  const resetConfig = useSimulationStore((s) => s.resetConfig)
  const [timingExpanded, setTimingExpanded] = useState(false)

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      <div className="font-semibold text-lg">Configuration</div>

      {/* Run Simulation Button */}
      <div className="flex space-x-2">
        <Button
          className="flex-1"
          onClick={startSimulation}
          disabled={isRunning}
        >
          {isRunning ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Running...
            </>
          ) : (
            <>
              <Play className="mr-2 h-4 w-4" />
              Run Simulation
            </>
          )}
        </Button>
        <Button
          variant="outline"
          size="icon"
          onClick={resetConfig}
          disabled={isRunning}
        >
          <RotateCcw className="h-4 w-4" />
        </Button>
      </div>

      {/* Network Size */}
      <Card>
        <CardHeader className="py-3">
          <CardTitle className="text-sm">Network Size</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label className="text-xs">Farms</Label>
              <span className="text-xs font-mono">{config.numFarms}</span>
            </div>
            <Slider
              value={[config.numFarms]}
              onValueChange={([v]) => setConfig({ numFarms: v })}
              min={1}
              max={20}
              step={1}
              disabled={isRunning}
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label className="text-xs">Packers</Label>
              <span className="text-xs font-mono">{config.numPackers}</span>
            </div>
            <Slider
              value={[config.numPackers]}
              onValueChange={([v]) => setConfig({ numPackers: v })}
              min={1}
              max={10}
              step={1}
              disabled={isRunning}
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label className="text-xs">Distribution Centers</Label>
              <span className="text-xs font-mono">{config.numDistributionCenters}</span>
            </div>
            <Slider
              value={[config.numDistributionCenters]}
              onValueChange={([v]) => setConfig({ numDistributionCenters: v })}
              min={1}
              max={10}
              step={1}
              disabled={isRunning}
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label className="text-xs">Retailers</Label>
              <span className="text-xs font-mono">{config.numRetailers}</span>
            </div>
            <Slider
              value={[config.numRetailers]}
              onValueChange={([v]) => setConfig({ numRetailers: v })}
              min={5}
              max={100}
              step={5}
              disabled={isRunning}
            />
          </div>
        </CardContent>
      </Card>

      {/* Contamination */}
      <Card>
        <CardHeader className="py-3">
          <CardTitle className="text-sm">Contamination</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label className="text-xs">Contamination Rate</Label>
              <span className="text-xs font-mono">{Math.round(config.contaminationRate * 100)}%</span>
            </div>
            <Slider
              value={[config.contaminationRate]}
              onValueChange={([v]) => setConfig({ contaminationRate: v })}
              min={0}
              max={1}
              step={0.1}
              disabled={isRunning}
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label className="text-xs">Contamination Duration (days)</Label>
              <span className="text-xs font-mono">{config.contaminationDurationDays}</span>
            </div>
            <Slider
              value={[config.contaminationDurationDays]}
              onValueChange={([v]) => setConfig({ contaminationDurationDays: v })}
              min={1}
              max={14}
              step={1}
              disabled={isRunning}
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label className="text-xs">Simulation Days</Label>
              <span className="text-xs font-mono">{config.simulationDays}</span>
            </div>
            <Slider
              value={[config.simulationDays]}
              onValueChange={([v]) => setConfig({ simulationDays: v })}
              min={7}
              max={180}
              step={7}
              disabled={isRunning}
            />
          </div>
        </CardContent>
      </Card>

      {/* Inventory Strategy */}
      <Card>
        <CardHeader className="py-3">
          <CardTitle className="text-sm">DC Inventory Strategy</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Select
            value={config.inventoryStrategy}
            onValueChange={(v) => setConfig({ inventoryStrategy: v as InventoryStrategy })}
            disabled={isRunning}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select strategy" />
            </SelectTrigger>
            <SelectContent>
              {inventoryStrategies.map((strategy) => (
                <SelectItem key={strategy.value} value={strategy.value}>
                  <div>
                    <div className="font-medium">{strategy.label}</div>
                    <div className="text-xs text-muted-foreground">{strategy.description}</div>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label className="text-xs">Date Window (days)</Label>
              <span className="text-xs font-mono">{config.dateWindowDays}</span>
            </div>
            <Slider
              value={[config.dateWindowDays]}
              onValueChange={([v]) => setConfig({ dateWindowDays: v })}
              min={1}
              max={30}
              step={1}
              disabled={isRunning}
            />
          </div>
        </CardContent>
      </Card>

      {/* Investigation Parameters */}
      <Card>
        <CardHeader className="py-3">
          <CardTitle className="text-sm">Investigation Parameters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label className="text-xs">Cases Successfully Interviewed</Label>
              <span className="text-xs font-mono">{config.interviewSuccessRate}%</span>
            </div>
            <Slider
              value={[config.interviewSuccessRate]}
              onValueChange={([v]) => setConfig({ interviewSuccessRate: v })}
              min={10}
              max={100}
              step={5}
              disabled={isRunning}
            />
            <p className="text-xs text-muted-foreground">
              Percent of illness cases where epidemiologists successfully interview the patient
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label className="text-xs">FDA Record Collection Window</Label>
              <span className="text-xs font-mono">{config.recordCollectionWindowDays} days</span>
            </div>
            <Slider
              value={[config.recordCollectionWindowDays]}
              onValueChange={([v]) => setConfig({ recordCollectionWindowDays: v })}
              min={7}
              max={30}
              step={1}
              disabled={isRunning}
            />
            <p className="text-xs text-muted-foreground">
              Days of records FDA requests from retail locations around estimated purchase date
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label className="text-xs">Investigators Assigned</Label>
              <span className="text-xs font-mono">{config.numInvestigators}</span>
            </div>
            <Slider
              value={[config.numInvestigators]}
              onValueChange={([v]) => setConfig({ numInvestigators: v })}
              min={1}
              max={20}
              step={1}
              disabled={isRunning}
            />
            <p className="text-xs text-muted-foreground">
              Number of investigators assigned to traceback (6 hrs direct work/day each)
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Supply Chain Timing (Collapsible) */}
      <Card>
        <CardHeader
          className="py-3 cursor-pointer"
          onClick={() => setTimingExpanded(!timingExpanded)}
        >
          <CardTitle className="text-sm flex items-center justify-between">
            <span>Supply Chain Timing</span>
            {timingExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </CardTitle>
        </CardHeader>
        {timingExpanded && (
          <CardContent className="space-y-4">
            <p className="text-xs text-muted-foreground">
              Configure realistic time delays for product flow through the supply chain
            </p>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-xs">Transit Speed Factor</Label>
                <span className="text-xs font-mono">{config.transitSpeedFactor}x</span>
              </div>
              <Slider
                value={[config.transitSpeedFactor]}
                onValueChange={([v]) => setConfig({ transitSpeedFactor: v })}
                min={0.5}
                max={2}
                step={0.1}
                disabled={isRunning}
              />
              <p className="text-xs text-muted-foreground">
                Multiplier for all transit times (lower = faster delivery)
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-xs">Post-Harvest Cooling</Label>
                <span className="text-xs font-mono">{config.coolingHoldHours} hrs</span>
              </div>
              <Slider
                value={[config.coolingHoldHours]}
                onValueChange={([v]) => setConfig({ coolingHoldHours: v })}
                min={0}
                max={48}
                step={2}
                disabled={isRunning}
              />
              <p className="text-xs text-muted-foreground">
                Hours product is held for cooling after harvest before shipping
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-xs">DC QA Inspection</Label>
                <span className="text-xs font-mono">{config.dcInspectionHours} hrs</span>
              </div>
              <Slider
                value={[config.dcInspectionHours]}
                onValueChange={([v]) => setConfig({ dcInspectionHours: v })}
                min={0}
                max={24}
                step={1}
                disabled={isRunning}
              />
              <p className="text-xs text-muted-foreground">
                Hours for quality inspection before inventory is available at DCs
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-xs">Retail Stocking Delay</Label>
                <span className="text-xs font-mono">{config.retailStockingDelayHours} hrs</span>
              </div>
              <Slider
                value={[config.retailStockingDelayHours]}
                onValueChange={([v]) => setConfig({ retailStockingDelayHours: v })}
                min={0}
                max={24}
                step={1}
                disabled={isRunning}
              />
              <p className="text-xs text-muted-foreground">
                Hours between receiving and shelf availability at retail
              </p>
            </div>
          </CardContent>
        )}
      </Card>

    </div>
  )
}
