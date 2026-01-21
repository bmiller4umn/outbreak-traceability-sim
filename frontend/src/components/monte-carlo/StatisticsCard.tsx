import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import type { MetricStatistics } from '@/api/types'
import HistogramChart from './HistogramChart'

interface StatisticsCardProps {
  title: string
  stats: MetricStatistics
  format?: 'number' | 'multiplier' | 'percent'
  color?: string
  showHistogram?: boolean
}

function formatValue(value: number, format: 'number' | 'multiplier' | 'percent'): string {
  switch (format) {
    case 'multiplier':
      return `${value.toFixed(2)}x`
    case 'percent':
      return `${(value * 100).toFixed(1)}%`
    default:
      return value.toFixed(2)
  }
}

export default function StatisticsCard({
  title,
  stats,
  format = 'number',
  color = '#3b82f6',
  showHistogram = true,
}: StatisticsCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Main value */}
        <div className="text-center">
          <div className="text-2xl font-bold" style={{ color }}>
            {formatValue(stats.mean, format)}
          </div>
          <div className="text-xs text-muted-foreground">
            mean (SD: {stats.std.toFixed(2)})
          </div>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-4 gap-2 text-xs">
          <div className="text-center">
            <div className="font-medium">{formatValue(stats.min, format)}</div>
            <div className="text-muted-foreground">Min</div>
          </div>
          <div className="text-center">
            <div className="font-medium">{formatValue(stats.p25, format)}</div>
            <div className="text-muted-foreground">25th</div>
          </div>
          <div className="text-center">
            <div className="font-medium">{formatValue(stats.p75, format)}</div>
            <div className="text-muted-foreground">75th</div>
          </div>
          <div className="text-center">
            <div className="font-medium">{formatValue(stats.max, format)}</div>
            <div className="text-muted-foreground">Max</div>
          </div>
        </div>

        {/* Histogram */}
        {showHistogram && stats.histogram.length > 0 && (
          <HistogramChart data={stats.histogram} color={color} height={120} />
        )}
      </CardContent>
    </Card>
  )
}
