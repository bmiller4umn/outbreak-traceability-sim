import { useEffect } from 'react'
import MonteCarloControls from '@/components/monte-carlo/MonteCarloControls'
import MonteCarloProgress from '@/components/monte-carlo/MonteCarloProgress'
import MonteCarloResults from '@/components/monte-carlo/MonteCarloResults'
import { useSimulationStore, useMonteCarloStore } from '@/store'

export default function MonteCarloPage() {
  const simConfig = useSimulationStore((s) => s.config)
  const syncFromSimulationConfig = useMonteCarloStore((s) => s.syncFromSimulationConfig)

  // Sync Monte Carlo config with main simulation config when page loads
  useEffect(() => {
    syncFromSimulationConfig(simConfig)
  }, [simConfig, syncFromSimulationConfig])

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-6xl mx-auto space-y-4">
        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-1 space-y-4">
            <MonteCarloControls />
            <MonteCarloProgress />
          </div>
          <div className="col-span-2">
            <MonteCarloResults />
          </div>
        </div>
      </div>
    </div>
  )
}
