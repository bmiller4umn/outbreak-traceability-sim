import { create } from 'zustand'

type ActiveTab = 'simulate' | 'compare' | 'investigate'
type ComparisonLayout = 'side-by-side' | 'overlay' | 'toggle'

interface UIStore {
  // Panel states
  sidebarCollapsed: boolean
  activeTab: ActiveTab

  // Graph view settings
  graphZoom: number
  graphPan: { x: number; y: number }
  showLabels: boolean
  showFlowAnimation: boolean

  // Comparison view
  comparisonLayout: ComparisonLayout
  syncGraphViews: boolean
  comparisonActiveScenario: 'deterministic' | 'calculated'

  // Actions
  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
  setActiveTab: (tab: ActiveTab) => void
  setGraphZoom: (zoom: number) => void
  setGraphPan: (pan: { x: number; y: number }) => void
  toggleLabels: () => void
  toggleFlowAnimation: () => void
  setComparisonLayout: (layout: ComparisonLayout) => void
  toggleSyncGraphViews: () => void
  setComparisonActiveScenario: (scenario: 'deterministic' | 'calculated') => void
}

export const useUIStore = create<UIStore>((set) => ({
  // Initial state
  sidebarCollapsed: false,
  activeTab: 'simulate',
  graphZoom: 1,
  graphPan: { x: 0, y: 0 },
  showLabels: true,
  showFlowAnimation: true,
  comparisonLayout: 'side-by-side',
  syncGraphViews: true,
  comparisonActiveScenario: 'deterministic',

  // Actions
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

  setActiveTab: (tab) => set({ activeTab: tab }),

  setGraphZoom: (zoom) => set({ graphZoom: Math.max(0.1, Math.min(4, zoom)) }),

  setGraphPan: (pan) => set({ graphPan: pan }),

  toggleLabels: () => set((state) => ({ showLabels: !state.showLabels })),

  toggleFlowAnimation: () => set((state) => ({ showFlowAnimation: !state.showFlowAnimation })),

  setComparisonLayout: (layout) => set({ comparisonLayout: layout }),

  toggleSyncGraphViews: () => set((state) => ({ syncGraphViews: !state.syncGraphViews })),

  setComparisonActiveScenario: (scenario) => set({ comparisonActiveScenario: scenario }),
}))

// Selectors
export const selectSidebarCollapsed = (state: UIStore) => state.sidebarCollapsed
export const selectActiveTab = (state: UIStore) => state.activeTab
export const selectGraphSettings = (state: UIStore) => ({
  zoom: state.graphZoom,
  pan: state.graphPan,
  showLabels: state.showLabels,
  showFlowAnimation: state.showFlowAnimation,
})
