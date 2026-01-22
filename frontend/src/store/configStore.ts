import { create } from 'zustand'
import { configApi, type AppConfig } from '@/api/config'

interface ConfigStore {
  config: AppConfig | null
  isLoading: boolean
  error: string | null
  fetchConfig: () => Promise<void>
}

const DEFAULT_CONFIG: AppConfig = {
  maxMonteCarloIterations: 10000,
  defaultMonteCarloIterations: 1000,
  monteCarloEnabled: true,
}

export const useConfigStore = create<ConfigStore>((set, get) => ({
  config: null,
  isLoading: false,
  error: null,

  fetchConfig: async () => {
    if (get().config) return // Already loaded

    set({ isLoading: true, error: null })
    try {
      const config = await configApi.getConfig()
      set({ config, isLoading: false })
    } catch (err) {
      console.warn('Failed to fetch config, using defaults:', err)
      set({ config: DEFAULT_CONFIG, isLoading: false })
    }
  },
}))

// Selector for max Monte Carlo iterations
export const selectMaxMonteCarloIterations = (state: ConfigStore) =>
  state.config?.maxMonteCarloIterations ?? DEFAULT_CONFIG.maxMonteCarloIterations

// Selector for Monte Carlo enabled
export const selectMonteCarloEnabled = (state: ConfigStore) =>
  state.config?.monteCarloEnabled ?? DEFAULT_CONFIG.monteCarloEnabled
