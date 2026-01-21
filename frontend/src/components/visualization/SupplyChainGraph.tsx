import { useRef, useEffect } from 'react'
import * as d3 from 'd3'
import { useNetworkStore, selectFilteredNodes, selectFilteredEdges } from '@/store'
import { useUIStore, selectGraphSettings } from '@/store'
import type { NodeType } from '@/api/types'
import GraphLegend from './GraphLegend'
import GraphControls from './GraphControls'

const NODE_COLORS: Record<NodeType, string> = {
  farm: '#22c55e',
  packer: '#3b82f6',
  distribution_center: '#f59e0b',
  processor: '#8b5cf6',
  deli: '#ec4899',
  retailer: '#06b6d4',
}

const NODE_ICONS: Record<NodeType, string> = {
  farm: '🌱',
  packer: '📦',
  distribution_center: '🏭',
  processor: '🔄',
  deli: '🥗',
  retailer: '🏪',
}

const LAYER_Y: Record<NodeType, number> = {
  farm: 0.08,
  packer: 0.22,
  processor: 0.38,  // Processors come AFTER packers but BEFORE DCs
  distribution_center: 0.54,
  deli: 0.72,
  retailer: 0.88,
}

interface SupplyChainGraphProps {
  highlightMode?: 'none' | 'contaminated' | 'scope'
  scenarioMode?: 'deterministic' | 'probabilistic'
  showCaseCounts?: boolean
}

export default function SupplyChainGraph({
  highlightMode = 'none',
  showCaseCounts = false,
}: SupplyChainGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const nodes = useNetworkStore(selectFilteredNodes)
  const edges = useNetworkStore(selectFilteredEdges)
  const selectedNodeId = useNetworkStore((s) => s.selectedNodeId)
  const highlightedPath = useNetworkStore((s) => s.highlightedPath)
  const nodeCaseCounts = useNetworkStore((s) => s.nodeCaseCounts)
  const selectNode = useNetworkStore((s) => s.selectNode)
  const setHoveredNode = useNetworkStore((s) => s.setHoveredNode)
  const updateNodePositions = useNetworkStore((s) => s.updateNodePositions)

  const { showLabels, showFlowAnimation } = useUIStore(selectGraphSettings)

  // Create simulation
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
    const nodesWithPositions = nodes.map((node) => ({
      ...node,
      x: node.x ?? Math.random() * width,
      y: node.y ?? height * LAYER_Y[node.type],
    }))

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
          .distance(100)
          .strength(0.3)
      )
      .force('charge', d3.forceManyBody().strength(-200).distanceMax(300))
      .force('collide', d3.forceCollide(35))
      .force('x', d3.forceX(width / 2).strength(0.05))
      .force(
        'y',
        d3.forceY((d: any) => height * LAYER_Y[d.type as NodeType]).strength(0.8)
      )

    // Draw edges
    const edgeGroup = g
      .append('g')
      .attr('class', 'edges')
      .selectAll('line')
      .data(edgeData)
      .join('line')
      .attr('stroke', (d: any) => {
        const isHighlighted =
          highlightedPath.includes(d.source.id) && highlightedPath.includes(d.target.id)
        return isHighlighted ? '#fbbf24' : '#9ca3af'
      })
      .attr('stroke-width', (d: any) => {
        const isHighlighted =
          highlightedPath.includes(d.source.id) && highlightedPath.includes(d.target.id)
        return isHighlighted ? 3 : 1.5
      })
      .attr('stroke-opacity', (d: any) => d.probability ?? 0.5)
      .attr('marker-end', 'url(#arrowhead)')

    // Add animated flow effect
    if (showFlowAnimation) {
      edgeGroup
        .attr('stroke-dasharray', '8 4')
        .attr('class', 'animate-flow')
    }

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
      .attr('r', (d: any) => (d.id === selectedNodeId ? 26 : 20))
      .attr('fill', (d: any) => NODE_COLORS[d.type as NodeType])
      .attr('stroke', (d: any) => {
        if (d.id === selectedNodeId) return '#fbbf24'
        if (highlightedPath.includes(d.id)) return '#fbbf24'
        if (d.isContaminationSource) return '#ef4444'  // Red for source
        if (d.isContaminated) return '#f97316'  // Orange for received contaminated
        return '#1f2937'
      })
      .attr('stroke-width', (d: any) => {
        if (d.id === selectedNodeId || highlightedPath.includes(d.id)) return 3
        if (d.isContaminationSource) return 3
        if (d.isContaminated) return 2
        return 1
      })
      .attr('opacity', (d: any) => {
        if (highlightMode === 'scope' && d.isInScope) {
          return 0.3 + (d.scopeProbability ?? 1) * 0.7
        }
        if (highlightMode === 'contaminated' && !d.isContaminated) {
          return 0.3
        }
        return 1
      })

    // Contamination source ring (red, solid) - for the original contaminated farm
    nodeGroup
      .filter((d: any) => d.isContaminationSource)
      .append('circle')
      .attr('r', 28)
      .attr('fill', 'none')
      .attr('stroke', '#ef4444')
      .attr('stroke-width', 3)

    // Received contaminated product ring (orange, dashed based on probability)
    nodeGroup
      .filter((d: any) => d.isContaminated && !d.isContaminationSource)
      .append('circle')
      .attr('r', 28)
      .attr('fill', 'none')
      .attr('stroke', '#f97316')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', (d: any) =>
        d.contaminationProbability < 1 ? '4,2' : 'none'
      )

    // Node icons
    nodeGroup
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('font-size', '14px')
      .text((d: any) => NODE_ICONS[d.type as NodeType])

    // Node labels
    if (showLabels) {
      nodeGroup
        .append('text')
        .attr('y', 35)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('fill', '#6b7280')
        .text((d: any) => (d.name.length > 12 ? d.name.slice(0, 12) + '...' : d.name))
    }

    // Probability badge for scope mode
    if (highlightMode === 'scope') {
      nodeGroup
        .filter((d: any) => d.isInScope && d.scopeProbability !== undefined && d.scopeProbability < 1)
        .append('g')
        .attr('transform', 'translate(15, -15)')
        .call((g) => {
          g.append('circle').attr('r', 12).attr('fill', '#1f2937')
          g.append('text')
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'central')
            .attr('font-size', '9px')
            .attr('fill', 'white')
            .attr('font-family', 'monospace')
            .text((d: any) => `${Math.round((d.scopeProbability ?? 1) * 100)}%`)
        })
    }

    // Case count badge
    if (showCaseCounts) {
      nodeGroup
        .filter((d: any) => nodeCaseCounts[d.id] && nodeCaseCounts[d.id].caseCount > 0)
        .append('g')
        .attr('transform', 'translate(-15, -15)')
        .call((g) => {
          g.append('rect')
            .attr('x', -14)
            .attr('y', -10)
            .attr('width', 28)
            .attr('height', 20)
            .attr('rx', 4)
            .attr('fill', '#dc2626')
          g.append('text')
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'central')
            .attr('font-size', '10px')
            .attr('fill', 'white')
            .attr('font-weight', 'bold')
            .text((d: any) => nodeCaseCounts[d.id]?.caseCount || 0)
        })
    }

    // Event handlers
    nodeGroup
      .on('click', (_event, d: any) => {
        selectNode(d.id === selectedNodeId ? null : d.id)
      })
      .on('mouseenter', (_event, d: any) => {
        setHoveredNode(d.id)
      })
      .on('mouseleave', () => {
        setHoveredNode(null)
      })

    // Update positions on each tick
    simulation.on('tick', () => {
      edgeGroup
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y)

      nodeGroup.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
    })

    // Save positions when simulation ends
    simulation.on('end', () => {
      const positions: Record<string, { x: number; y: number }> = {}
      nodesWithPositions.forEach((n: any) => {
        positions[n.id] = { x: n.x, y: n.y }
      })
      updateNodePositions(positions)
    })

    // Add zoom behavior
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom)

    // Add arrowhead marker
    svg
      .append('defs')
      .append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 30)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .append('path')
      .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
      .attr('fill', '#9ca3af')

    return () => {
      simulation.stop()
    }
  }, [nodes, edges, selectedNodeId, highlightedPath, showLabels, showFlowAnimation, highlightMode, showCaseCounts, nodeCaseCounts])

  return (
    <div className="relative h-full w-full" ref={containerRef}>
      <svg ref={svgRef} className="h-full w-full bg-slate-50 rounded-lg" />
      <div className="absolute top-4 left-4">
        <GraphLegend />
      </div>
      <div className="absolute top-4 right-4">
        <GraphControls />
      </div>
      {nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="max-w-2xl mx-auto px-6 py-8 text-center">
            <h2 className="text-xl font-semibold text-slate-700 mb-4">
              Run a simulation to visualize the supply chain network
            </h2>
            <div className="text-xs text-slate-500 space-y-3 text-left border-t pt-4 mt-6">
              <p className="font-medium text-slate-600">About This Simulation</p>
              <p>
                This simulation was developed by Ben Miller, PhD, MPH, based on the FDA's
                "FSMA Final Rule on Requirements for Additional Traceability Records for Certain Foods"
                regulation and Dr. Miller's subject matter expertise. This tool was developed using Claude Code.
              </p>
              <p className="font-medium text-slate-600 pt-2">Purpose</p>
              <p>
                This simulation is designed to demonstrate the impact of traceability record-keeping practices
                on foodborne illness outbreak investigations. It models a simplified food supply chain for
                fresh cucumbers and cucumber salad products, simulating contamination events and subsequent
                traceback investigations. The simulation compares two scenarios: (1) deterministic tracking,
                where supply chain participants maintain exact lot code records as required by FSMA 204, and
                (2) probabilistic tracking, where distribution centers use calculated lot codes based on
                inventory date windows rather than exact traceability records.
              </p>
              <p>
                Users can explore how differences in traceability practices affect investigation scope,
                the ability to identify contamination sources, and the number of products and facilities
                that must be examined during an outbreak response. This tool is intended for educational
                purposes, policy analysis, and to support discussions about food traceability requirements.
              </p>
              <p className="font-medium text-slate-600 pt-2">Disclaimer</p>
              <p>
                This simulation is provided for informational and educational purposes only.
                This tool may produce outputs that are inaccurate or contain errors.
                The simulation is provided "AS IS" without warranty of any kind, express or implied,
                including but not limited to the warranties of merchantability, fitness for a particular
                purpose, and noninfringement. In no event shall the authors or copyright holders be
                liable for any claim, damages, or other liability arising from the use of this simulation.
              </p>
              <p>
                Users should independently verify any outputs and should not rely solely on this
                simulation for regulatory compliance, food safety decisions, or any other critical purposes.
                This simulation does not constitute legal, regulatory, or professional advice.
              </p>
              <p className="pt-2">
                Questions about this simulation can be directed to Dr. Miller at{' '}
                <a href="mailto:mill1543@umn.edu" className="text-blue-600 hover:underline">
                  mill1543@umn.edu
                </a>
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
