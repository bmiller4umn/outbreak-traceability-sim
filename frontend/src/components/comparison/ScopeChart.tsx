import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { ScenarioResult } from '@/api/types'

interface ScopeChartProps {
  deterministic: ScenarioResult
  calculated: ScenarioResult
}

export default function ScopeChart({ deterministic, calculated }: ScopeChartProps) {
  const data = [
    {
      name: 'Farms in Scope',
      Deterministic: deterministic.farmsInScope,
      Calculated: calculated.farmsInScope,
    },
    {
      name: 'TLCs in Scope',
      Deterministic: deterministic.tlcsInScope,
      Calculated: calculated.tlcsInScope,
    },
    {
      name: 'TLCS (Locations)',
      Deterministic: deterministic.tlcsLocations,
      Calculated: calculated.tlcsLocations,
    },
    {
      name: 'Traceback Paths',
      Deterministic: deterministic.tracebackPaths,
      Calculated: calculated.tracebackPaths,
    },
  ]

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Scope Comparison</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={120} fontSize={12} />
              <Tooltip />
              <Legend />
              <Bar dataKey="Deterministic" fill="#22c55e" name="Full Compliance" />
              <Bar dataKey="Calculated" fill="#f97316" name="Calculated Lot Codes" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
