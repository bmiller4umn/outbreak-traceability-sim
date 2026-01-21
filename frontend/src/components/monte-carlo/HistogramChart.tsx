import { useRef, useEffect } from 'react'
import * as d3 from 'd3'
import type { HistogramBin } from '@/api/types'

interface HistogramChartProps {
  data: HistogramBin[]
  xLabel?: string
  color?: string
  height?: number
}

export default function HistogramChart({
  data,
  xLabel = '',
  color = '#3b82f6',
  height = 150,
}: HistogramChartProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!svgRef.current || !containerRef.current || data.length === 0) return

    const container = containerRef.current
    const svg = d3.select(svgRef.current)

    // Clear previous content
    svg.selectAll('*').remove()

    // Dimensions
    const margin = { top: 10, right: 10, bottom: 30, left: 40 }
    const width = container.clientWidth - margin.left - margin.right
    const chartHeight = height - margin.top - margin.bottom

    // Create chart group
    const g = svg
      .attr('width', container.clientWidth)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Scales
    const x = d3
      .scaleLinear()
      .domain([data[0].binStart, data[data.length - 1].binEnd])
      .range([0, width])

    const y = d3
      .scaleLinear()
      .domain([0, d3.max(data, (d) => d.count) || 1])
      .nice()
      .range([chartHeight, 0])

    // X axis
    g.append('g')
      .attr('transform', `translate(0,${chartHeight})`)
      .call(d3.axisBottom(x).ticks(5))

    // Y axis
    g.append('g').call(d3.axisLeft(y).ticks(4))

    // X axis label
    if (xLabel) {
      g.append('text')
        .attr('x', width / 2)
        .attr('y', chartHeight + 25)
        .attr('text-anchor', 'middle')
        .attr('class', 'fill-muted-foreground text-xs')
        .text(xLabel)
    }

    // Bars
    const barWidth = width / data.length - 1

    g.selectAll('.bar')
      .data(data)
      .join('rect')
      .attr('class', 'bar')
      .attr('x', (d) => x(d.binStart))
      .attr('y', (d) => y(d.count))
      .attr('width', barWidth)
      .attr('height', (d) => chartHeight - y(d.count))
      .attr('fill', color)
      .attr('opacity', 0.8)
      .on('mouseover', function () {
        d3.select(this).attr('opacity', 1)
      })
      .on('mouseout', function () {
        d3.select(this).attr('opacity', 0.8)
      })
  }, [data, xLabel, color, height])

  if (data.length === 0) {
    return (
      <div className="h-[150px] flex items-center justify-center text-muted-foreground text-sm">
        No data
      </div>
    )
  }

  return (
    <div ref={containerRef} className="w-full">
      <svg ref={svgRef} />
    </div>
  )
}
