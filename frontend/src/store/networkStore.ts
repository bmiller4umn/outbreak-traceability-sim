import { create } from 'zustand'
import type { SupplyChainNode, SupplyChainEdge, LotInfo, NodeType, NodeCaseCount } from '@/api/types'

interface NetworkStore {
  // State
  nodes: SupplyChainNode[]
  edges: SupplyChainEdge[]
  lots: Record<string, LotInfo>
  nodeCaseCounts: Record<string, NodeCaseCount>

  // Selection state
  selectedNodeId: string | null
  hoveredNodeId: string | null
  highlightedPath: string[]

  // Filters
  visibleNodeTypes: Set<NodeType>
  showContaminatedOnly: boolean
  showScopeOnly: boolean

  // Actions
  setNetwork: (nodes: SupplyChainNode[], edges: SupplyChainEdge[]) => void
  setLots: (lots: Record<string, LotInfo>) => void
  setNodeCaseCounts: (counts: NodeCaseCount[]) => void
  selectNode: (id: string | null) => void
  setHoveredNode: (id: string | null) => void
  setHighlightedPath: (path: string[]) => void
  toggleNodeTypeVisibility: (type: NodeType) => void
  setShowContaminatedOnly: (value: boolean) => void
  setShowScopeOnly: (value: boolean) => void
  updateNodePositions: (positions: Record<string, { x: number; y: number }>) => void
  markNodesInScope: (nodeIds: string[], probabilities?: Record<string, number>) => void
  markContaminatedNodes: (nodeIds: string[], probabilities?: Record<string, number>) => void
  clearScopeHighlighting: () => void
  clearNetwork: () => void
}

const ALL_NODE_TYPES: NodeType[] = ['farm', 'packer', 'distribution_center', 'processor', 'deli', 'retailer']

export const useNetworkStore = create<NetworkStore>((set) => ({
  // Initial state
  nodes: [],
  edges: [],
  lots: {},
  nodeCaseCounts: {},
  selectedNodeId: null,
  hoveredNodeId: null,
  highlightedPath: [],
  visibleNodeTypes: new Set(ALL_NODE_TYPES),
  showContaminatedOnly: false,
  showScopeOnly: false,

  // Actions
  setNetwork: (nodes, edges) => set({ nodes, edges }),

  setLots: (lots) => set({ lots }),

  setNodeCaseCounts: (counts) =>
    set({
      nodeCaseCounts: Object.fromEntries(counts.map((c) => [c.nodeId, c])),
    }),

  selectNode: (id) => set({ selectedNodeId: id }),

  setHoveredNode: (id) => set({ hoveredNodeId: id }),

  setHighlightedPath: (path) => set({ highlightedPath: path }),

  toggleNodeTypeVisibility: (type) =>
    set((state) => {
      const newTypes = new Set(state.visibleNodeTypes)
      if (newTypes.has(type)) {
        newTypes.delete(type)
      } else {
        newTypes.add(type)
      }
      return { visibleNodeTypes: newTypes }
    }),

  setShowContaminatedOnly: (value) => set({ showContaminatedOnly: value }),

  setShowScopeOnly: (value) => set({ showScopeOnly: value }),

  updateNodePositions: (positions) =>
    set((state) => ({
      nodes: state.nodes.map((node) =>
        positions[node.id] ? { ...node, ...positions[node.id] } : node
      ),
    })),

  markNodesInScope: (nodeIds, probabilities = {}) =>
    set((state) => ({
      nodes: state.nodes.map((node) => ({
        ...node,
        isInScope: nodeIds.includes(node.id),
        scopeProbability: probabilities[node.id],
      })),
    })),

  markContaminatedNodes: (nodeIds, probabilities = {}) =>
    set((state) => ({
      nodes: state.nodes.map((node) => ({
        ...node,
        isContaminated: nodeIds.includes(node.id),
        contaminationProbability: probabilities[node.id] ?? (nodeIds.includes(node.id) ? 1 : 0),
      })),
    })),

  clearScopeHighlighting: () =>
    set((state) => ({
      nodes: state.nodes.map((node) => ({
        ...node,
        isInScope: false,
        scopeProbability: undefined,
      })),
      highlightedPath: [],
    })),

  clearNetwork: () =>
    set({
      nodes: [],
      edges: [],
      lots: {},
      nodeCaseCounts: {},
      selectedNodeId: null,
      hoveredNodeId: null,
      highlightedPath: [],
    }),
}))

// Selectors
export const selectFilteredNodes = (state: NetworkStore) => {
  let nodes = state.nodes.filter((node) => state.visibleNodeTypes.has(node.type))

  if (state.showContaminatedOnly) {
    nodes = nodes.filter((node) => node.isContaminated)
  }

  if (state.showScopeOnly) {
    nodes = nodes.filter((node) => node.isInScope)
  }

  return nodes
}

export const selectFilteredEdges = (state: NetworkStore) => {
  const visibleNodeIds = new Set(selectFilteredNodes(state).map((n) => n.id))
  return state.edges.filter(
    (edge) => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)
  )
}

export const selectNodeById = (id: string) => (state: NetworkStore) =>
  state.nodes.find((node) => node.id === id)
