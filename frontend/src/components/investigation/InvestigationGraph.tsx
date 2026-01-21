import { useRef, useEffect } from 'react'
import * as d3 from 'd3'
import type { InvestigationScopeNode, InvestigationScopeEdge } from '@/api/types'

const NODE_COLORS: Record<string, string> = {
  farm: '#22c55e',
  packer: '#3b82f6',
  distribution_center: '#f59e0b',
  processor: '#8b5cf6',
  deli: '#ec4899',
  retailer: '#06b6d4',
}

const NODE_ICONS: Record<string, string> = {
  farm: '🌱',
  packer: '📦',
  distribution_center: '🏭',
  processor: '🔄',
  deli: '🥗',
  retailer: '🏪',
}

const LAYER_Y: Record<string, number> = {
  farm: 0.1,
  packer: 0.25,
  processor: 0.4,
  distribution_center: 0.55,
  deli: 0.75,
  retailer: 0.9,
}

interface InvestigationGraphProps {
  nodes: InvestigationScopeNode[]
  edges: InvestigationScopeEdge[]
  actualSourceFarmId: string | null
  variant: 'deterministic' | 'probabilistic'
  title: string
}

export default function InvestigationGraph({
  nodes,
  edges,
  actualSourceFarmId,
  variant,
  title,
}: InvestigationGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!svgRef.current || !containerRef.current || nodes.length === 0) return

    const svg = d3.select(svgRef.current)
    const width = containerRef.current.clientWidth
    const height = containerRef.current.clientHeight

    // Clear previous content
    svg.selectAll('*').remove()

    // Create container group for zoom
    const g = svg.append('g')

    // Initialize node positions based on layers
    const nodesWithPositions = nodes.map((node) => {
      const layerNodes = nodes.filter((n) => n.type === node.type)
      const indexInLayer = layerNodes.indexOf(node)
      const layerWidth = width / (layerNodes.length + 1)

      return {
        ...node,
        x: layerWidth * (indexInLayer + 1),
        y: height * (LAYER_Y[node.type] || 0.5),
      }
    })

    // Create edge data with source/target references
    const edgeData = edges.map((edge) => ({
      ...edge,
      source: nodesWithPositions.find((n) => n.id === edge.source) || edge.source,
      target: nodesWithPositions.find((n) => n.id === edge.target) || edge.target,
    }))

    // Create force simulation
    const simulation = d3
      .forceSimulation(nodesWithPositions as d3.SimulationNodeDatum[])
      .force(
        'link',
        d3
          .forceLink(edgeData as d3.SimulationLinkDatum<d3.SimulationNodeDatum>[])
          .id((d: any) => d.id)
          .distance(60)
          .strength(0.5)
      )
      .force('charge', d3.forceManyBody().strength(-150).distanceMax(200))
      .force('collide', d3.forceCollide(25))
      .force('x', d3.forceX(width / 2).strength(0.05))
      .force(
        'y',
        d3.forceY((d: any) => height * (LAYER_Y[d.type] || 0.5)).strength(0.8)
      )

    // Marker ID unique to this instance
    const markerId = `arrowhead-${variant}`

    // Add arrowhead marker
    svg
      .append('defs')
      .append('marker')
      .attr('id', markerId)
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 5)
      .attr('markerHeight', 5)
      .append('path')
      .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
      .attr('fill', variant === 'deterministic' ? '#22c55e' : '#f97316')

    // Draw edges
    const edgeGroup = g
      .append('g')
      .attr('class', 'edges')
      .selectAll('line')
      .data(edgeData)
      .join('line')
      .attr('stroke', variant === 'deterministic' ? '#22c55e' : '#f97316')
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.7)
      .attr('marker-end', `url(#${markerId})`)

    // Draw nodes
    const nodeGroup = g
      .append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodesWithPositions)
      .join('g')
      .attr('cursor', 'pointer')
      .call(
        d3
          .drag<SVGGElement, any>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart()
            d.fx = d.x
            d.fy = d.y
          })
          .on('drag', (event, d) => {
            d.fx = event.x
            d.fy = event.y
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0)
            d.fx = null
            d.fy = null
          }) as any
      )

    // Node circles
    nodeGroup
      .append('circle')
      .attr('r', 16)
      .attr('fill', (d: any) => NODE_COLORS[d.type] || '#6b7280')
      .attr('stroke', (d: any) => {
        if (d.id === actualSourceFarmId) return '#ef4444'
        return variant === 'deterministic' ? '#15803d' : '#c2410c'
      })
      .attr('stroke-width', (d: any) => (d.id === actualSourceFarmId ? 3 : 1.5))
      .attr('opacity', 1.0)  // Full opacity - expansion factor is shown as badge instead

    // Source indicator ring
    nodeGroup
      .filter((d: any) => d.id === actualSourceFarmId)
      .append('circle')
      .attr('r', 22)
      .attr('fill', 'none')
      .attr('stroke', '#ef4444')
      .attr('stroke-width', 3)

    // Node icons
    nodeGroup
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('font-size', '11px')
      .text((d: any) => NODE_ICONS[d.type] || '?')

    // TLC Expansion badge - only show for endpoints (deli/retailer) in probabilistic view
    // that have an expansion > 1
    const isEndpoint = (type: string) => type === 'deli' || type === 'retailer'

    nodeGroup
      .filter((d: any) => variant === 'probabilistic' && isEndpoint(d.type) && (d.probability ?? 1) > 1)
      .append('g')
      .attr('transform', 'translate(14, -14)')
      .call((g) => {
        g.append('rect')
          .attr('x', -14)
          .attr('y', -8)
          .attr('width', 28)
          .attr('height', 16)
          .attr('rx', 3)
          .attr('fill', '#dc2626')  // Red background for expansion
        g.append('text')
          .attr('text-anchor', 'middle')
          .attr('dominant-baseline', 'central')
          .attr('font-size', '8px')
          .attr('fill', 'white')
          .attr('font-weight', 'bold')
          .attr('font-family', 'monospace')
          .text((d: any) => {
            const exp = d.probability ?? 1
            return exp >= 10 ? `${Math.round(exp)}x` : `${exp.toFixed(1)}x`
          })
      })

    // Tooltips with TLC counts for endpoints
    nodeGroup
      .append('title')
      .text((d: any) => {
        const location = [d.city, d.state].filter(Boolean).join(', ')
        let tooltip = `${d.name}\n${location}`

        if (isEndpoint(d.type) && d.detTlcCount !== undefined && d.probTlcCount !== undefined) {
          tooltip += `\n\nTLC Scope:`
          tooltip += `\n  Deterministic: ${d.detTlcCount} TLCs`
          tooltip += `\n  Probabilistic: ${d.probTlcCount} TLCs`
          if (d.detTlcCount > 0) {
            tooltip += `\n  Expansion: ${(d.probTlcCount / d.detTlcCount).toFixed(1)}x`
          }
        }

        return tooltip
      })

    // Update positions on tick
    simulation.on('tick', () => {
      edgeGroup
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y)

      nodeGroup.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
    })

    // Add zoom behavior
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom)

    return () => {
      simulation.stop()
    }
  }, [nodes, edges, actualSourceFarmId, variant])

  const borderColor = variant === 'deterministic' ? 'border-green-500' : 'border-orange-500'
  const bgColor = variant === 'deterministic' ? 'bg-green-50' : 'bg-orange-50'

  return (
    <div className={`h-full w-full rounded-lg border-2 ${borderColor} overflow-hidden`}>
      <div className={`px-3 py-2 ${bgColor} border-b ${borderColor}`}>
        <div className="flex items-center justify-between">
          <span className="font-medium text-sm">{title}</span>
          <span className="text-xs text-muted-foreground">
            {nodes.length} nodes
          </span>
        </div>
      </div>
      <div className="relative h-[calc(100%-40px)] w-full" ref={containerRef}>
        <svg ref={svgRef} className="h-full w-full bg-white" />
        {nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-muted-foreground text-sm">
            No nodes in scope
          </div>
        )}
      </div>
    </div>
  )
}
