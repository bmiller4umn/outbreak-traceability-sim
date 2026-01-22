import { api } from './client'

export interface AppConfig {
  maxMonteCarloIterations: number
  defaultMonteCarloIterations: number
  monteCarloEnabled: boolean
}

export const configApi = {
  getConfig: async (): Promise<AppConfig> => {
    return api.get<AppConfig>('/config')
  },
}
