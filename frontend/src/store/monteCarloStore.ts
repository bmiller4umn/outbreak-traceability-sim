import { create } from 'zustand'
import type { MonteCarloConfig, MonteCarloResult, SimulationConfig } from '@/api/types'
import { monteCarloApi } from '@/api/monteCarlo'

const DEFAULT_MC_CONFIG: MonteCarloConfig = {
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
  interviewSuccessRate: 70,
  recordCollectionWindowDays: 14,
  numIterations: 1000,
  baseRandomSeed: null,
}

// Helper to convert simulation config to monte carlo config
function simConfigToMcConfig(simConfig: SimulationConfig): Partial<MonteCarloConfig> {
  return {
    numFarms: simConfig.numFarms,
    numPackers: simConfig.numPackers,
    numDistributionCenters: simConfig.numDistributionCenters,
    numRetailers: simConfig.numRetailers,
    retailersWithDelisPct: simConfig.retailersWithDelisPct,
    contaminationRate: simConfig.contaminationRate,
    contaminationDurationDays: simConfig.contaminationDurationDays,
    pathogen: simConfig.pathogen,
    inventoryStrategy: simConfig.inventoryStrategy,
    dateWindowDays: simConfig.dateWindowDays,
    simulationDays: simConfig.simulationDays,
    interviewSuccessRate: simConfig.interviewSuccessRate,
    recordCollectionWindowDays: simConfig.recordCollectionWindowDays,
  }
}

interface MonteCarloStore {
  // State
  config: MonteCarloConfig
  status: 'idle' | 'running' | 'completed' | 'cancelled' | 'error'
  iterationsCompleted: number
  iterationsTotal: number
  progress: number
  estimatedTimeRemaining: number | null
  result: MonteCarloResult | null
  error: string | null
  monteCarloId: string | null

  // Actions
  setConfig: (partial: Partial<MonteCarloConfig>) => void
  syncFromSimulationConfig: (simConfig: SimulationConfig) => void
  startMonteCarlo: () => Promise<void>
  cancelMonteCarlo: () => Promise<void>
  clearResult: () => void
}

export const useMonteCarloStore = create<MonteCarloStore>((set, get) => ({
  // Initial state
  config: DEFAULT_MC_CONFIG,
  status: 'idle',
  iterationsCompleted: 0,
  iterationsTotal: 0,
  progress: 0,
  estimatedTimeRemaining: null,
  result: null,
  error: null,
  monteCarloId: null,

  // Actions
  setConfig: (partial) =>
    set((state) => ({
      config: { ...state.config, ...partial },
    })),

  syncFromSimulationConfig: (simConfig) =>
    set((state) => ({
      config: { ...state.config, ...simConfigToMcConfig(simConfig) },
    })),

  startMonteCarlo: async () => {
    const { config } = get()
    set({
      status: 'running',
      progress: 0,
      iterationsCompleted: 0,
      iterationsTotal: config.numIterations,
      error: null,
      result: null,
      estimatedTimeRemaining: null,
    })

    try {
      const { monteCarloId } = await monteCarloApi.run(config)
      set({ monteCarloId })

      // Poll for status
      const pollInterval = setInterval(async () => {
        try {
          const status = await monteCarloApi.getStatus(monteCarloId)
          set({
            iterationsCompleted: status.iterationsCompleted,
            progress: status.progress,
            estimatedTimeRemaining: status.estimatedTimeRemaining,
          })

          if (status.status === 'completed') {
            clearInterval(pollInterval)
            const result = await monteCarloApi.getResult(monteCarloId)
            set({ status: 'completed', result, progress: 1 })
          } else if (status.status === 'error') {
            clearInterval(pollInterval)
            set({ status: 'error', error: status.message || 'Simulation failed' })
          } else if (status.status === 'cancelled') {
            clearInterval(pollInterval)
            set({ status: 'cancelled' })
          }
        } catch (err) {
          clearInterval(pollInterval)
          set({ status: 'error', error: err instanceof Error ? err.message : 'Unknown error' })
        }
      }, 1000) // Poll every second for Monte Carlo
    } catch (err) {
      set({ status: 'error', error: err instanceof Error ? err.message : 'Failed to start' })
    }
  },

  cancelMonteCarlo: async () => {
    const { monteCarloId } = get()
    if (monteCarloId) {
      try {
        await monteCarloApi.cancel(monteCarloId)
        set({ status: 'cancelled' })
      } catch (err) {
        console.error('Failed to cancel:', err)
      }
    }
  },

  clearResult: () =>
    set({
      result: null,
      status: 'idle',
      progress: 0,
      iterationsCompleted: 0,
      error: null,
      monteCarloId: null,
      estimatedTimeRemaining: null,
    }),
}))

// Selectors
export const selectMonteCarloStatus = (state: MonteCarloStore) => state.status
export const selectMonteCarloProgress = (state: MonteCarloStore) => ({
  progress: state.progress,
  iterationsCompleted: state.iterationsCompleted,
  iterationsTotal: state.iterationsTotal,
  estimatedTimeRemaining: state.estimatedTimeRemaining,
})
export const selectMonteCarloResult = (state: MonteCarloStore) => state.result
export const selectHasMonteCarloResult = (state: MonteCarloStore) => state.result !== null
