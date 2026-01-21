import { Link, useLocation } from 'react-router-dom'
import { useSimulationStore, selectStatus, selectProgress } from '@/store'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Activity, GitCompare, Search, BarChart3, BookOpen, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { path: '/', label: 'Simulate', icon: Activity },
  { path: '/compare', label: 'Compare', icon: GitCompare },
  { path: '/investigate', label: 'Investigate', icon: Search },
  { path: '/monte-carlo', label: 'Monte Carlo', icon: BarChart3 },
  { path: '/guide', label: 'User Guide', icon: BookOpen },
  { path: '/about', label: 'About', icon: Info },
]

export default function Header() {
  const location = useLocation()
  const status = useSimulationStore(selectStatus)
  const progress = useSimulationStore(selectProgress)

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center px-4">
        {/* Logo */}
        <div className="mr-4 flex items-center space-x-2">
          <span className="text-xl">🥒</span>
          <span className="font-bold">Outbreak Traceability</span>
        </div>

        {/* Navigation */}
        <nav className="flex items-center space-x-1">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={cn(
                'flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                location.pathname === path
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{label}</span>
            </Link>
          ))}
        </nav>

        {/* Simulation Status */}
        <div className="ml-auto flex items-center space-x-4">
          {status === 'running' && (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-muted-foreground">Running...</span>
              <Progress value={progress * 100} className="w-24 h-2" />
              <span className="text-sm font-mono">{Math.round(progress * 100)}%</span>
            </div>
          )}
          {status === 'completed' && (
            <Badge variant="default" className="bg-green-500">
              Completed
            </Badge>
          )}
          {status === 'error' && (
            <Badge variant="destructive">Error</Badge>
          )}
        </div>
      </div>
    </header>
  )
}
