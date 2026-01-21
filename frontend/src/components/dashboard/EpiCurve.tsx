import { useRef, useEffect, useState } from 'react'
import * as d3 from 'd3'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Loader2 } from 'lucide-react'
import { useSimulationStore } from '@/store'
import { simulationApi } from '@/api/simulation'
import type { EpiCurveDataPoint } from '@/api/types'

export default function EpiCurve() {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const simulationId = useSimulationStore((s) => s.simulationId)
  const status = useSimulationStore((s) => s.status)

  const [epiCurve, setEpiCurve] = useState<EpiCurveDataPoint[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch case data
  useEffect(() => {
    if (!simulationId || status !== 'completed') {
      setEpiCurve([])
      return
    }

    setLoading(true)
    setError(null)

    simulationApi
      .getCaseData(simulationId)
      .then((data) => setEpiCurve(data.epiCurve))
      .catch((err) => setError(err.message || 'Failed to load epi curve'))
      .finally(() => setLoading(false))
  }, [simulationId, status])

  // Render D3 chart
  useEffect(() => {
    if (!svgRef.current || !containerRef.current || epiCurve.length === 0) return

    const container = containerRef.current
    const svg = d3.select(svgRef.current)

    // Clear previous content
    svg.selectAll('*').remove()

    // Dimensions
    const margin = { top: 20, right: 20, bottom: 40, left: 40 }
    const width = container.clientWidth - margin.left - margin.right
    const height = 200 - margin.top - margin.bottom

    // Create chart group
    const g = svg
      .attr('width', container.clientWidth)
      .attr('height', 200)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Parse dates
    const data = epiCurve.map((d) => ({
      date: new Date(d.date),
      count: d.count,
    }))

    // Scales
    const x = d3
      .scaleBand()
      .domain(data.map((d) => d.date.toISOString()))
      .range([0, width])
      .padding(0.2)

    const y = d3
      .scaleLinear()
      .domain([0, d3.max(data, (d) => d.count) || 1])
      .nice()
      .range([height, 0])

    // X axis
    const xAxis = g
      .append('g')
      .attr('transform', `translate(0,${height})`)
      .call(
        d3.axisBottom(x).tickFormat((d) => {
          const date = new Date(d)
          return `${date.getMonth() + 1}/${date.getDate()}`
        })
      )

    // Rotate x labels if too many
    if (data.length > 10) {
      xAxis
        .selectAll('text')
        .attr('transform', 'rotate(-45)')
        .style('text-anchor', 'end')
        .attr('dx', '-0.5em')
        .attr('dy', '0.15em')
    }

    // Y axis
    g.append('g').call(d3.axisLeft(y).ticks(5))

    // Y axis label
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', -35)
      .attr('x', -height / 2)
      .attr('text-anchor', 'middle')
      .attr('class', 'fill-muted-foreground text-xs')
      .text('Cases')

    // Bars
    g.selectAll('.bar')
      .data(data)
      .join('rect')
      .attr('class', 'bar')
      .attr('x', (d) => x(d.date.toISOString()) || 0)
      .attr('y', (d) => y(d.count))
      .attr('width', x.bandwidth())
      .attr('height', (d) => height - y(d.count))
      .attr('fill', '#f97316')
      .attr('rx', 2)
      .on('mouseover', function (_event, d) {
        d3.select(this).attr('fill', '#ea580c')

        // Show tooltip
        const tooltip = g
          .append('g')
          .attr('class', 'tooltip')
          .attr('transform', `translate(${(x(d.date.toISOString()) || 0) + x.bandwidth() / 2}, ${y(d.count) - 10})`)

        tooltip
          .append('rect')
          .attr('x', -25)
          .attr('y', -15)
          .attr('width', 50)
          .attr('height', 20)
          .attr('fill', 'rgba(0,0,0,0.8)')
          .attr('rx', 4)

        tooltip
          .append('text')
          .attr('text-anchor', 'middle')
          .attr('y', -1)
          .attr('fill', 'white')
          .attr('font-size', '11px')
          .text(`${d.count} cases`)
      })
      .on('mouseout', function () {
        d3.select(this).attr('fill', '#f97316')
        g.selectAll('.tooltip').remove()
      })
  }, [epiCurve])

  if (!simulationId || status !== 'completed') {
    return null
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="py-8 flex items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-4 text-center text-destructive text-sm">
          {error}
        </CardContent>
      </Card>
    )
  }

  if (epiCurve.length === 0) {
    return (
      <Card>
        <CardContent className="py-4 text-center text-muted-foreground text-sm">
          No case data available
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Epidemic Curve (Cases by Onset Date)</CardTitle>
      </CardHeader>
      <CardContent>
        <div ref={containerRef} className="w-full">
          <svg ref={svgRef} />
        </div>
      </CardContent>
    </Card>
  )
}
