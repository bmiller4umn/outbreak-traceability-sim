import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { NodeType } from '@/api/types'

const legendItems: { type: NodeType; label: string; icon: string }[] = [
  { type: 'farm', label: 'Farm', icon: '🌱' },
  { type: 'packer', label: 'Packer', icon: '📦' },
  { type: 'distribution_center', label: 'DC', icon: '🏭' },
  { type: 'processor', label: 'Processor', icon: '🔄' },
  { type: 'deli', label: 'Deli', icon: '🥗' },
  { type: 'retailer', label: 'Retailer', icon: '🏪' },
]

export default function GraphLegend() {
  return (
    <Card className="bg-background/90 backdrop-blur">
      <CardContent className="p-3">
        <div className="text-xs font-semibold mb-2">Node Types</div>
        <div className="grid grid-cols-2 gap-1">
          {legendItems.map(({ type, label, icon }) => (
            <div key={type} className="flex items-center space-x-1">
              <Badge variant={type === 'distribution_center' ? 'dc' : type} className="h-5 w-5 p-0 justify-center">
                <span className="text-[10px]">{icon}</span>
              </Badge>
              <span className="text-[10px]">{label}</span>
            </div>
          ))}
        </div>
        <div className="border-t mt-2 pt-2">
          <div className="text-xs font-semibold mb-1">Contamination</div>
          <div className="flex items-center space-x-2 text-[10px]">
            <div className="w-3 h-3 rounded-full border-[3px] border-red-500" />
            <span>Source Farm</span>
          </div>
          <div className="flex items-center space-x-2 text-[10px] mt-1">
            <div className="w-3 h-3 rounded-full border-2 border-orange-500" />
            <span>Received Contaminated</span>
          </div>
          <div className="flex items-center space-x-2 text-[10px] mt-1">
            <div className="w-3 h-3 rounded-full border-2 border-dashed border-orange-500" />
            <span>Possibly Contaminated</span>
          </div>
          <div className="flex items-center space-x-2 text-[10px] mt-1">
            <div className="w-3 h-3 rounded-full border-2 border-yellow-400" />
            <span>Selected/Path</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
