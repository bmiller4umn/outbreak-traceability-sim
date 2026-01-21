import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { LucideIcon } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: LucideIcon
  variant?: 'default' | 'success' | 'warning' | 'destructive'
}

const variantStyles = {
  default: {
    bg: 'bg-slate-50',
    icon: 'text-slate-600',
    value: 'text-slate-900',
  },
  success: {
    bg: 'bg-green-50',
    icon: 'text-green-600',
    value: 'text-green-700',
  },
  warning: {
    bg: 'bg-amber-50',
    icon: 'text-amber-600',
    value: 'text-amber-700',
  },
  destructive: {
    bg: 'bg-red-50',
    icon: 'text-red-600',
    value: 'text-red-700',
  },
}

export default function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'default',
}: MetricCardProps) {
  const styles = variantStyles[variant]

  return (
    <Card className={cn('overflow-hidden', styles.bg)}>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className={cn('text-2xl font-bold', styles.value)}>{value}</p>
            {subtitle && (
              <p className="text-xs text-muted-foreground">{subtitle}</p>
            )}
          </div>
          <div className={cn('p-2 rounded-lg', styles.bg)}>
            <Icon className={cn('h-5 w-5', styles.icon)} />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
