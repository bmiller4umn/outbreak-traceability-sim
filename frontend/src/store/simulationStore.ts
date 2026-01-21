import { create } from 'zustand'
import type { SimulationConfig, SimulationResult } from '@/api/types'
import { simulationApi } from '@/api/simulation'
import { useNetworkStore } from './networkStore'

const DEFAULT_CONFIG: SimulationConfig = {
  numFarms: 5,
  numPackers: 2,
  numDistributionCenters: 3,
  numRetailers: 20,
  retailersWithDelisPct: 0.3,
  contaminationRate: 1.0,
  contaminationDurationDays: 7,
  pathogen: 'Salmonella',
  inventoryStrategy: 'FIFO',
  dateWindowDays: 7,
  simulationDays: 90,
  randomSeed: null,
  // Investigation parameters
  interviewSuccessRate: 70,  // 70% of cases successfully interviewed
  recordCollectionWindowDays: 14,  // FDA requests 2 weeks of records
  numInvestigators: 5,  // 5 investigators assigned to traceback
  // Timing parameters for realistic supply chain delays
  transitSpeedFactor: 1.0,  // 1.0 = normal speed (lower = faster)
  coolingHoldHours: 12,  // 12 hours post-harvest cooling
  dcInspectionHours: 6,  // 6 hours for DC QA inspection
  retailStockingDelayHours: 4,  // 4 hours to reach shelf after receiving
}

interface SimulationStore {
  // State
  config: SimulationConfig
  status: 'idle' | 'running' | 'completed' | 'error'
  progress: number
  result: SimulationResult | null
  error: string | null
  simulationId: string | null

  // Actions
  setConfig: (partial: Partial<SimulationConfig>) => void
  resetConfig: () => void
  startSimulation: () => Promise<void>
  pollSimulationStatus: () => Promise<void>
  setResult: (result: SimulationResult) => void
  clearResult: () => void
  setError: (error: string) => void
}

export const useSimulationStore = create<SimulationStore>((set, get) => ({
  // Initial state
  config: DEFAULT_CONFIG,
  status: 'idle',
  progress: 0,
  result: null,
  error: null,
  simulationId: null,

  // Actions
  setConfig: (partial) =>
    set((state) => ({
      config: { ...state.config, ...partial },
    })),

  resetConfig: () =>
    set({
      config: DEFAULT_CONFIG,
      status: 'idle',
      progress: 0,
      result: null,
      error: null,
      simulationId: null,
    }),

  startSimulation: async () => {
    const { config } = get()
    set({ status: 'running', progress: 0, error: null, result: null })

    try {
      const { simulationId } = await simulationApi.run(config)
      set({ simulationId })

      // Start polling
      const pollInterval = setInterval(async () => {
        try {
          const status = await simulationApi.getStatus(simulationId)
          set({ progress: status.progress })

          if (status.status === 'completed') {
            clearInterval(pollInterval)
            const result = await simulationApi.getResult(simulationId)

            // Fetch and load network data
            try {
              const networkData = await simulationApi.getNetwork(simulationId)
              useNetworkStore.getState().setNetwork(networkData.nodes, networkData.edges)
            } catch (networkErr) {
              console.error('Failed to load network data:', networkErr)
            }

            set({ status: 'completed', result, progress: 1 })
          } else if (status.status === 'error') {
            clearInterval(pollInterval)
            set({ status: 'error', error: status.message || 'Simulation failed' })
          }
        } catch (err) {
          clearInterval(pollInterval)
          set({ status: 'error', error: err instanceof Error ? err.message : 'Unknown error' })
        }
      }, 500)
    } catch (err) {
      set({ status: 'error', error: err instanceof Error ? err.message : 'Failed to start simulation' })
    }
  },

  pollSimulationStatus: async () => {
    const { simulationId } = get()
    if (!simulationId) return

    try {
      const status = await simulationApi.getStatus(simulationId)
      set({ progress: status.progress })

      if (status.status === 'completed') {
        const result = await simulationApi.getResult(simulationId)
        set({ status: 'completed', result, progress: 1 })
      } else if (status.status === 'error') {
        set({ status: 'error', error: status.message || 'Simulation failed' })
      }
    } catch (err) {
      set({ status: 'error', error: err instanceof Error ? err.message : 'Unknown error' })
    }
  },

  setResult: (result) => set({ result, status: 'completed', progress: 1 }),

  clearResult: () =>
    set({
      result: null,
      status: 'idle',
      progress: 0,
      error: null,
      simulationId: null,
    }),

  setError: (error) => set({ error, status: 'error' }),
}))

// Selectors
export const selectConfig = (state: SimulationStore) => state.config
export const selectStatus = (state: SimulationStore) => state.status
export const selectProgress = (state: SimulationStore) => state.progress
export const selectResult = (state: SimulationStore) => state.result
export const selectIsRunning = (state: SimulationStore) => state.status === 'running'
export const selectHasResult = (state: SimulationStore) => state.result !== null
