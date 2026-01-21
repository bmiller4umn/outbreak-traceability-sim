import { useInvestigationStore } from '@/store'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Target, CheckCircle2 } from 'lucide-react'

export default function ConvergenceDisplay() {
  const { convergenceResults, actualSourceFarmId } = useInvestigationStore()

  if (convergenceResults.length === 0) {
    return null
  }

  const maxConfidence = Math.max(...convergenceResults.map((r) => r.confidenceScore))

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center">
          <Target className="h-4 w-4 mr-2" />
          Convergence Analysis
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {convergenceResults.slice(0, 5).map((result, index) => {
          const isActualSource = result.farmId === actualSourceFarmId
          const normalizedConfidence = (result.confidenceScore / maxConfidence) * 100

          return (
            <div
              key={result.farmId}
              className={`p-3 rounded-lg border ${
                isActualSource ? 'bg-green-50 border-green-200' : 'bg-muted/50'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium">#{index + 1}</span>
                  <span className="text-sm">{result.farmName}</span>
                  {isActualSource && (
                    <Badge variant="default" className="bg-green-500 text-[10px]">
                      <CheckCircle2 className="h-3 w-3 mr-1" />
                      Actual Source
                    </Badge>
                  )}
                </div>
                <span className="text-sm font-mono font-bold">
                  {Math.round(result.confidenceScore * 100)}%
                </span>
              </div>

              <Progress value={normalizedConfidence} className="h-2" />

              <div className="flex justify-between mt-2 text-[10px] text-muted-foreground">
                <span>{result.casesConverging} cases converging</span>
                <span>{result.tlcsConverging.length} TLCs</span>
              </div>
            </div>
          )
        })}

        {convergenceResults.length > 5 && (
          <div className="text-center text-xs text-muted-foreground">
            +{convergenceResults.length - 5} more farms in scope
          </div>
        )}
      </CardContent>
    </Card>
  )
}
