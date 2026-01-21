import { Card, CardContent } from '@/components/ui/card'
import { TrendingUp } from 'lucide-react'

interface MetricsComparisonProps {
  farmExpansion: number
  tlcExpansion: number
  tlcsLocationExpansion: number
  pathExpansion: number
}

export default function MetricsComparison({
  farmExpansion,
  tlcExpansion,
  tlcsLocationExpansion,
  pathExpansion,
}: MetricsComparisonProps) {
  const metrics = [
    {
      label: 'Farm Scope Expansion',
      value: farmExpansion,
      description: 'More farms must be investigated',
      color: 'text-red-600',
      bgColor: 'bg-red-50',
    },
    {
      label: 'TLC Scope Expansion',
      value: tlcExpansion,
      description: 'More lot codes in traceback scope',
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
    {
      label: 'TLCS Expansion',
      value: tlcsLocationExpansion,
      description: 'More TLC source locations',
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
    },
    {
      label: 'Path Expansion',
      value: pathExpansion,
      description: 'More possible contamination paths',
      color: 'text-amber-600',
      bgColor: 'bg-amber-50',
    },
  ]

  return (
    <div className="grid grid-cols-4 gap-4">
      {metrics.map((metric) => (
        <Card key={metric.label} className={metric.bgColor}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">{metric.label}</p>
                <p className={`text-3xl font-bold ${metric.color}`}>
                  {metric.value.toFixed(1)}x
                </p>
                <p className="text-xs text-muted-foreground mt-1">{metric.description}</p>
              </div>
              <div className={`p-3 rounded-full ${metric.bgColor}`}>
                <TrendingUp className={`h-6 w-6 ${metric.color}`} />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
