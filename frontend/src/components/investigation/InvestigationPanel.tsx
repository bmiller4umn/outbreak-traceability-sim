import { useEffect } from 'react'
import { useInvestigationStore, useNetworkStore } from '@/store'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Badge } from '@/components/ui/badge'
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  RotateCcw,
  Gauge,
} from 'lucide-react'
import CertaintyIndicator from './CertaintyIndicator'
import ConvergenceDisplay from './ConvergenceDisplay'
import ScopeComparison from './ScopeComparison'
import FarmTracebackMetrics from './FarmTracebackMetrics'

export default function InvestigationPanel() {
  const {
    isPlaying,
    currentStep,
    totalSteps,
    playbackSpeed,
    activeMode,
    deterministicSteps,
    probabilisticSteps,
    play,
    pause,
    stepForward,
    stepBackward,
    goToStep,
    setPlaybackSpeed,
    setActiveMode,
    reset,
  } = useInvestigationStore()

  const { setHighlightedPath, markNodesInScope, clearScopeHighlighting } = useNetworkStore()

  // Animation loop
  useEffect(() => {
    if (!isPlaying) return

    const interval = setInterval(() => {
      const store = useInvestigationStore.getState()
      if (store.currentStep >= store.totalSteps - 1) {
        store.pause()
      } else {
        store.stepForward()
      }
    }, playbackSpeed)

    return () => clearInterval(interval)
  }, [isPlaying, playbackSpeed])

  // Update visualization on step change
  useEffect(() => {
    if (totalSteps === 0) return

    const steps = activeMode === 'deterministic' ? deterministicSteps : probabilisticSteps
    const currentStepData = steps[currentStep]

    if (currentStepData) {
      setHighlightedPath(currentStepData.pathSoFar)

      const nodesInScope = steps.slice(0, currentStep + 1).map((s) => s.currentNodeId)
      const probabilities = Object.fromEntries(
        steps.slice(0, currentStep + 1).map((s) => [s.currentNodeId, s.probability])
      )
      markNodesInScope(nodesInScope, probabilities)
    }
  }, [currentStep, activeMode, deterministicSteps, probabilisticSteps])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearScopeHighlighting()
    }
  }, [])

  const currentDetStep = deterministicSteps[currentStep]
  const currentProbStep = probabilisticSteps[currentStep]

  if (totalSteps === 0) {
    return (
      <div className="space-y-4">
        {/* Farm Traceback Metrics - main investigation results */}
        <FarmTracebackMetrics />
        {/* Show scope comparison even without animation steps */}
        <ScopeComparison />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Farm Traceback Metrics - main investigation results */}
      <FarmTracebackMetrics />

      {/* Mode Selection */}
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-center space-x-2">
            <Button
              variant={activeMode === 'deterministic' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveMode('deterministic')}
            >
              Deterministic
            </Button>
            <Button
              variant={activeMode === 'split' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveMode('split')}
            >
              Side by Side
            </Button>
            <Button
              variant={activeMode === 'probabilistic' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveMode('probabilistic')}
            >
              Probabilistic
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Animation Controls */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center justify-between">
            <span>Traceback Animation</span>
            <Badge variant="outline">
              Step {currentStep + 1} / {totalSteps}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Progress */}
          <Slider
            value={[currentStep]}
            onValueChange={([v]) => goToStep(v)}
            min={0}
            max={totalSteps - 1}
            step={1}
          />

          {/* Playback Controls */}
          <div className="flex items-center justify-center space-x-2">
            <Button variant="outline" size="icon" onClick={reset}>
              <RotateCcw className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" onClick={stepBackward} disabled={currentStep === 0}>
              <SkipBack className="h-4 w-4" />
            </Button>
            <Button size="icon" onClick={isPlaying ? pause : play}>
              {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={stepForward}
              disabled={currentStep >= totalSteps - 1}
            >
              <SkipForward className="h-4 w-4" />
            </Button>
          </div>

          {/* Speed Control */}
          <div className="flex items-center space-x-2">
            <Gauge className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">Speed:</span>
            <Slider
              value={[1000 - playbackSpeed]}
              onValueChange={([v]) => setPlaybackSpeed(1000 - v)}
              min={0}
              max={900}
              step={100}
              className="w-24"
            />
          </div>
        </CardContent>
      </Card>

      {/* Certainty Comparison */}
      {activeMode === 'split' ? (
        <div className="grid grid-cols-2 gap-4">
          <CertaintyIndicator
            title="Deterministic"
            probability={currentDetStep?.probability ?? 1}
            branchingFactor={currentDetStep?.branchingFactor ?? 1}
            mode="deterministic"
          />
          <CertaintyIndicator
            title="Probabilistic"
            probability={currentProbStep?.probability ?? 1}
            branchingFactor={currentProbStep?.branchingFactor ?? 1}
            mode="probabilistic"
          />
        </div>
      ) : (
        <CertaintyIndicator
          title={activeMode === 'deterministic' ? 'Deterministic' : 'Probabilistic'}
          probability={
            activeMode === 'deterministic'
              ? currentDetStep?.probability ?? 1
              : currentProbStep?.probability ?? 1
          }
          branchingFactor={
            activeMode === 'deterministic'
              ? currentDetStep?.branchingFactor ?? 1
              : currentProbStep?.branchingFactor ?? 1
          }
          mode={activeMode}
        />
      )}

      {/* Convergence Results */}
      <ConvergenceDisplay />

      {/* Scope Comparison */}
      <ScopeComparison />
    </div>
  )
}
