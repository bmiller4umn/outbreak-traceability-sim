import { create } from 'zustand'
import type { TracebackStep, ConvergenceResult } from '@/api/types'

type AnimationMode = 'deterministic' | 'probabilistic' | 'split'

interface InvestigationStore {
  // Animation state
  isPlaying: boolean
  currentStep: number
  totalSteps: number
  playbackSpeed: number // ms between steps

  // Traceback data
  deterministicSteps: TracebackStep[]
  probabilisticSteps: TracebackStep[]
  activeMode: AnimationMode

  // Convergence results
  convergenceResults: ConvergenceResult[]

  // Ground truth
  actualSourceFarmId: string | null

  // Actions
  loadInvestigationData: (data: {
    deterministicSteps: TracebackStep[]
    probabilisticSteps: TracebackStep[]
    actualSourceFarmId: string | null
  }) => void
  setConvergenceResults: (results: ConvergenceResult[]) => void
  play: () => void
  pause: () => void
  stepForward: () => void
  stepBackward: () => void
  goToStep: (step: number) => void
  setPlaybackSpeed: (speed: number) => void
  setActiveMode: (mode: AnimationMode) => void
  reset: () => void
  clear: () => void
}

export const useInvestigationStore = create<InvestigationStore>((set) => ({
  // Initial state
  isPlaying: false,
  currentStep: 0,
  totalSteps: 0,
  playbackSpeed: 500,
  deterministicSteps: [],
  probabilisticSteps: [],
  activeMode: 'split',
  convergenceResults: [],
  actualSourceFarmId: null,

  // Actions
  loadInvestigationData: (data) =>
    set({
      deterministicSteps: data.deterministicSteps,
      probabilisticSteps: data.probabilisticSteps,
      actualSourceFarmId: data.actualSourceFarmId,
      totalSteps: Math.max(data.deterministicSteps.length, data.probabilisticSteps.length),
      currentStep: 0,
      isPlaying: false,
    }),

  setConvergenceResults: (results) =>
    set({
      convergenceResults: results.sort((a, b) => b.confidenceScore - a.confidenceScore),
    }),

  play: () => set({ isPlaying: true }),

  pause: () => set({ isPlaying: false }),

  stepForward: () =>
    set((state) => ({
      currentStep: Math.min(state.currentStep + 1, state.totalSteps - 1),
    })),

  stepBackward: () =>
    set((state) => ({
      currentStep: Math.max(state.currentStep - 1, 0),
    })),

  goToStep: (step) =>
    set((state) => ({
      currentStep: Math.max(0, Math.min(step, state.totalSteps - 1)),
    })),

  setPlaybackSpeed: (speed) => set({ playbackSpeed: speed }),

  setActiveMode: (mode) => set({ activeMode: mode }),

  reset: () =>
    set({
      currentStep: 0,
      isPlaying: false,
    }),

  clear: () =>
    set({
      isPlaying: false,
      currentStep: 0,
      totalSteps: 0,
      deterministicSteps: [],
      probabilisticSteps: [],
      convergenceResults: [],
      actualSourceFarmId: null,
    }),
}))

// Selectors
export const selectCurrentDeterministicStep = (state: InvestigationStore) =>
  state.deterministicSteps[state.currentStep] ?? null

export const selectCurrentProbabilisticStep = (state: InvestigationStore) =>
  state.probabilisticSteps[state.currentStep] ?? null

export const selectDeterministicPath = (state: InvestigationStore) => {
  const step = state.deterministicSteps[state.currentStep]
  return step?.pathSoFar ?? []
}

export const selectProbabilisticPath = (state: InvestigationStore) => {
  const step = state.probabilisticSteps[state.currentStep]
  return step?.pathSoFar ?? []
}

export const selectCurrentProbability = (state: InvestigationStore) => {
  if (state.activeMode === 'deterministic') {
    return state.deterministicSteps[state.currentStep]?.probability ?? 1
  }
  return state.probabilisticSteps[state.currentStep]?.probability ?? 1
}

export const selectTopConvergenceResult = (state: InvestigationStore) =>
  state.convergenceResults[0] ?? null
