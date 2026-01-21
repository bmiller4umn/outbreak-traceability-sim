import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { useMonteCarloStore, selectMonteCarloProgress } from '@/store'
import { Loader2, Clock } from 'lucide-react'

function formatTime(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`
  }
  const minutes = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return `${minutes}m ${secs}s`
}

export default function MonteCarloProgress() {
  const status = useMonteCarloStore((s) => s.status)
  const { progress, iterationsCompleted, iterationsTotal, estimatedTimeRemaining } =
    useMonteCarloStore(selectMonteCarloProgress)

  if (status !== 'running') {
    return null
  }

  return (
    <Card>
      <CardContent className="py-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            <span className="text-sm font-medium">Running Monte Carlo Simulation</span>
          </div>
          <span className="text-sm font-mono">
            {iterationsCompleted} / {iterationsTotal}
          </span>
        </div>

        <Progress value={progress * 100} className="h-2" />

        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{Math.round(progress * 100)}% complete</span>
          {estimatedTimeRemaining !== null && (
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>~{formatTime(estimatedTimeRemaining)} remaining</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
