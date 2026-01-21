import { useNetworkStore, useUIStore } from '@/store'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Eye, EyeOff, Tag, Play, Pause } from 'lucide-react'
import type { NodeType } from '@/api/types'

const nodeTypes: { type: NodeType; label: string }[] = [
  { type: 'farm', label: 'Farms' },
  { type: 'packer', label: 'Packers' },
  { type: 'distribution_center', label: 'DCs' },
  { type: 'retailer', label: 'Retailers' },
]

export default function GraphControls() {
  const visibleNodeTypes = useNetworkStore((s) => s.visibleNodeTypes)
  const toggleNodeTypeVisibility = useNetworkStore((s) => s.toggleNodeTypeVisibility)
  const showContaminatedOnly = useNetworkStore((s) => s.showContaminatedOnly)
  const setShowContaminatedOnly = useNetworkStore((s) => s.setShowContaminatedOnly)

  const showLabels = useUIStore((s) => s.showLabels)
  const toggleLabels = useUIStore((s) => s.toggleLabels)
  const showFlowAnimation = useUIStore((s) => s.showFlowAnimation)
  const toggleFlowAnimation = useUIStore((s) => s.toggleFlowAnimation)

  return (
    <Card className="bg-background/90 backdrop-blur">
      <CardContent className="p-3 space-y-3">
        <div className="text-xs font-semibold">Filters</div>

        {/* Node type toggles */}
        <div className="flex flex-wrap gap-1">
          {nodeTypes.map(({ type, label }) => (
            <Button
              key={type}
              variant={visibleNodeTypes.has(type) ? 'default' : 'outline'}
              size="sm"
              className="h-6 text-[10px] px-2"
              onClick={() => toggleNodeTypeVisibility(type)}
            >
              {label}
            </Button>
          ))}
        </div>

        {/* View options */}
        <div className="flex gap-1">
          <Button
            variant={showContaminatedOnly ? 'destructive' : 'outline'}
            size="sm"
            className="h-6 text-[10px] px-2"
            onClick={() => setShowContaminatedOnly(!showContaminatedOnly)}
          >
            {showContaminatedOnly ? <EyeOff className="h-3 w-3 mr-1" /> : <Eye className="h-3 w-3 mr-1" />}
            Contaminated
          </Button>
        </div>

        {/* Display options */}
        <div className="flex gap-1">
          <Button
            variant={showLabels ? 'default' : 'outline'}
            size="sm"
            className="h-6 text-[10px] px-2"
            onClick={toggleLabels}
          >
            <Tag className="h-3 w-3 mr-1" />
            Labels
          </Button>
          <Button
            variant={showFlowAnimation ? 'default' : 'outline'}
            size="sm"
            className="h-6 text-[10px] px-2"
            onClick={toggleFlowAnimation}
          >
            {showFlowAnimation ? <Pause className="h-3 w-3 mr-1" /> : <Play className="h-3 w-3 mr-1" />}
            Flow
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
