import { useUIStore, selectSidebarCollapsed } from '@/store'
import SimulationControls from '@/components/simulation/SimulationControls'
import { Button } from '@/components/ui/button'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function Sidebar() {
  const collapsed = useUIStore(selectSidebarCollapsed)
  const toggleSidebar = useUIStore((s) => s.toggleSidebar)

  return (
    <aside
      className={cn(
        'relative border-r bg-muted/30 transition-all duration-300',
        collapsed ? 'w-12' : 'w-80'
      )}
    >
      {/* Toggle button */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute -right-3 top-4 z-10 h-6 w-6 rounded-full border bg-background"
        onClick={toggleSidebar}
      >
        {collapsed ? (
          <ChevronRight className="h-4 w-4" />
        ) : (
          <ChevronLeft className="h-4 w-4" />
        )}
      </Button>

      {/* Content */}
      <div
        className={cn(
          'h-full overflow-hidden transition-opacity duration-300',
          collapsed ? 'opacity-0' : 'opacity-100'
        )}
      >
        <SimulationControls />
      </div>
    </aside>
  )
}
