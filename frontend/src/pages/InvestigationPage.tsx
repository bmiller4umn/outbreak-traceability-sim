import { useSimulationStore, selectHasResult } from '@/store'
import SupplyChainGraph from '@/components/visualization/SupplyChainGraph'
import InvestigationPanel from '@/components/investigation/InvestigationPanel'
import { ResizablePanel } from '@/components/ui/resizable-panel'

export default function InvestigationPage() {
  const hasResult = useSimulationStore(selectHasResult)

  return (
    <div className="h-full flex gap-4">
      {/* Graph View */}
      <div className="flex-1 border rounded-lg overflow-hidden min-w-0">
        <SupplyChainGraph highlightMode="scope" />
      </div>

      {/* Investigation Panel - Resizable */}
      <ResizablePanel
        defaultWidth={450}
        minWidth={350}
        maxWidth={900}
      >
        {hasResult ? (
          <InvestigationPanel />
        ) : (
          <div className="flex items-center justify-center h-64 text-muted-foreground border rounded-lg">
            Run a simulation to investigate
          </div>
        )}
      </ResizablePanel>
    </div>
  )
}
