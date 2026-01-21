import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface CertaintyIndicatorProps {
  title: string
  probability: number
  branchingFactor: number
  mode: 'deterministic' | 'probabilistic'
}

export default function CertaintyIndicator({
  title,
  probability,
  branchingFactor,
  mode,
}: CertaintyIndicatorProps) {
  const probabilityPercent = Math.round(probability * 100)

  const getColor = (prob: number) => {
    if (prob >= 0.8) return 'bg-green-500'
    if (prob >= 0.5) return 'bg-yellow-500'
    if (prob >= 0.2) return 'bg-orange-500'
    return 'bg-red-500'
  }

  const getLabel = (prob: number) => {
    if (prob >= 0.8) return 'High Confidence'
    if (prob >= 0.5) return 'Medium Confidence'
    if (prob >= 0.2) return 'Low Confidence'
    return 'Very Low Confidence'
  }

  return (
    <Card className={cn(
      'border-l-4',
      mode === 'deterministic' ? 'border-l-green-500' : 'border-l-orange-500'
    )}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Probability */}
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-muted-foreground">Path Certainty</span>
            <span className="font-mono font-bold">{probabilityPercent}%</span>
          </div>
          <div className="relative h-3 w-full overflow-hidden rounded-full bg-secondary">
            <div
              className={cn('h-full transition-all duration-300', getColor(probability))}
              style={{ width: `${probabilityPercent}%` }}
            />
          </div>
          <div className="text-[10px] text-muted-foreground mt-1">{getLabel(probability)}</div>
        </div>

        {/* Branching Factor */}
        <div className="flex justify-between items-center pt-2 border-t">
          <span className="text-xs text-muted-foreground">Possible Paths:</span>
          <span className={cn(
            'text-lg font-bold',
            branchingFactor > 1 ? 'text-orange-600' : 'text-green-600'
          )}>
            {branchingFactor}
          </span>
        </div>

        {/* Interpretation */}
        <div className="text-[10px] text-muted-foreground p-2 bg-muted rounded">
          {mode === 'deterministic' ? (
            probability === 1 ? (
              <span>Exact lot code tracking - single definite path</span>
            ) : (
              <span>Some uncertainty in lot linkage</span>
            )
          ) : (
            probability < 0.5 ? (
              <span>Multiple possible source lots - investigation scope expands significantly</span>
            ) : (
              <span>Calculated lot codes introduce traceability uncertainty</span>
            )
          )}
        </div>
      </CardContent>
    </Card>
  )
}
