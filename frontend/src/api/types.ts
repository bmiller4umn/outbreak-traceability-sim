// Simulation configuration types
export type InventoryStrategy = 'FIFO' | 'LIFO' | 'ALL_IN_WINDOW' | 'INVENTORY_WEIGHTED'

export interface SimulationConfig {
  numFarms: number
  numPackers: number
  numDistributionCenters: number
  numRetailers: number
  retailersWithDelisPct: number
  contaminationRate: number
  contaminationDurationDays: number
  pathogen: string
  inventoryStrategy: InventoryStrategy
  dateWindowDays: number
  simulationDays: number
  randomSeed: number | null
  // Investigation parameters
  interviewSuccessRate: number  // Percent of cases successfully interviewed (0-100)
  recordCollectionWindowDays: number  // FDA record request window in days
  numInvestigators: number  // Number of investigators assigned to traceback (1-20)
  // Timing parameters for realistic supply chain delays
  transitSpeedFactor: number  // Multiplier for transit times (0.5-2.0, lower = faster)
  coolingHoldHours: number  // Hours product is held for cooling after harvest (0-48)
  dcInspectionHours: number  // Hours for QA inspection at distribution centers (0-24)
  retailStockingDelayHours: number  // Hours between receiving and shelf availability (0-24)
}

// Network node types
export type NodeType = 'farm' | 'packer' | 'distribution_center' | 'processor' | 'deli' | 'retailer'

export interface SupplyChainNode {
  id: string
  type: NodeType
  name: string
  city: string
  state: string
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
  isContaminated?: boolean
  isContaminationSource?: boolean
  contaminationProbability?: number
  isInScope?: boolean
  scopeProbability?: number
}

export interface SupplyChainEdge {
  id: string
  source: string
  target: string
  productCategories: string[]
  shipmentVolume: number
  isActive?: boolean
  flowDirection?: 'forward' | 'backward'
  probability?: number
}

// Lot tracking
export interface LotInfo {
  tlc: string
  createdAt: string
  createdByNodeId: string
  productCategory: string
  isContaminated: boolean
  contaminationProbability: number
  sourceTlcs: string[]
  sourceProbabilities: Record<string, number>
}

// Identification outcome type
export type IdentificationOutcome = 'yes' | 'no' | 'inconclusive'

// Investigation timing estimate
export interface InvestigationTiming {
  recordRequestHours: number
  tlcAnalysisHours: number
  tracebackHours: number
  convergenceAnalysisHours: number
  farmVerificationHours: number
  totalWorkHours: number  // Total person-hours of parallelizable work
  totalCalendarDays: number  // Actual elapsed days (accounting for team size)
  numInvestigators: number  // Team size
  directWorkHoursPerDay: number  // Hours of direct work per investigator per day
  locationsContacted: number
  tlcsAnalyzed: number
  pathsTraced: number
  farmsEvaluated: number
  farmsVerified: number
}

// Scenario results
export interface ScenarioResult {
  name: string
  dcMode: string
  cases: number
  farmsInScope: number
  tlcsInScope: number
  tlcsLocations: number  // TLCS - unique locations where TLCs were created
  tracebackPaths: number
  primarySuspect: string
  identificationOutcome: IdentificationOutcome
  sourceRank: number
  topTwoMargin: number  // Confidence gap between #1 and #2
  actualSource: string  // The actual contaminated farm for this scenario
  lotLinks?: {
    deterministic: number
    probabilistic: number
  }
  farmProbabilities?: Record<string, number>
  investigationTiming?: InvestigationTiming
}

// Simulation result
export interface SimulationResult {
  configuration: {
    simulationPeriod: { start: string; end: string }
    network: {
      farms: number
      packers: number
      distributionCenters: number
      retailers: number
    }
    pathogen: string
  }
  scenarios: {
    deterministic: ScenarioResult
    calculated: ScenarioResult
  }
  metrics: {
    sourceFarm: string
    lotsCreatedDeterministic: number
    lotsCreatedCalculated: number
    farmScopeExpansion: number
    tlcScopeExpansion: number
    tlcsLocationExpansion: number  // TLCS expansion
    pathExpansion: number
    timingExpansion?: number  // Investigation time expansion factor
  }
  conclusion: {
    deterministicCorrect: boolean
    calculatedCorrect: boolean
    farmScopeExpansion: number
    tlcScopeExpansion: number
    impactSummary: string
  }
}

// Investigation types
export interface TracebackStep {
  stepIndex: number
  currentNodeId: string
  currentTlc: string
  probability: number
  mode: 'deterministic' | 'probabilistic'
  pathSoFar: string[]
  branchingFactor: number
}

export interface ConvergenceResult {
  farmId: string
  farmName: string
  casesConverging: number
  tlcsConverging: string[]
  convergenceProbability: number
  confidenceScore: number
}

// API responses
export interface SimulationStatusResponse {
  simulationId: string
  status: 'pending' | 'running' | 'completed' | 'error'
  progress: number
  message?: string
}

export interface NetworkResponse {
  nodes: SupplyChainNode[]
  edges: SupplyChainEdge[]
}

export interface InvestigationStepsResponse {
  deterministicSteps: TracebackStep[]
  probabilisticSteps: TracebackStep[]
  actualSourceFarmId: string | null
}

export interface ConvergenceResponse {
  results: ConvergenceResult[]
  primarySuspect: {
    farmId: string
    farmName: string
    probability: number
  } | null
}

export interface InvestigationScopeNode {
  id: string
  name: string
  type: string
  probability: number  // For endpoints, this is the TLC expansion factor (prob TLCs / det TLCs)
  city?: string
  state?: string
  detTlcCount?: number  // Number of TLCs in deterministic mode
  probTlcCount?: number  // Number of TLCs in probabilistic mode
}

export interface InvestigationScopeEdge {
  id: string
  source: string
  target: string
  probability: number
}

export interface InvestigationScopeData {
  nodes: InvestigationScopeNode[]
  edges: InvestigationScopeEdge[]
  farmsCount: number
  tlcsCount: number
  pathsCount: number
}

export interface InvestigationScopeResponse {
  deterministic: InvestigationScopeData
  probabilistic: InvestigationScopeData
  actualSourceFarmId: string | null
}

// Farm traceback metrics
export type InvestigationTier = 'Primary Suspect' | 'Cannot Rule Out' | 'Unlikely'

export interface FarmTracebackMetric {
  farmId: string
  farmName: string
  rank: number
  tier: InvestigationTier
  casesConverging: number
  exclusiveCases: number
  totalCasesAnalyzed: number
  caseCoveragePct: number
  exclusiveCasePct: number
  tlcsConverging: number
  retailLocations: number
  convergenceProbability: number
  confidenceScore: number
  isActualSource: boolean
}

export interface FarmTracebackModeMetrics {
  mode: 'deterministic' | 'probabilistic'
  farms: FarmTracebackMetric[]
  totalCases: number
  casesWithTraces: number
  hasClearLeader: boolean
}

export interface FarmTracebackMetricsResponse {
  deterministic: FarmTracebackModeMetrics
  probabilistic: FarmTracebackModeMetrics
  actualSource: {
    farmId: string | null
    farmName: string
  }
}

// Case data types
export interface EpiCurveDataPoint {
  date: string
  count: number
}

export interface CaseSummary {
  totalCases: number
  hospitalizedCases: number
  hospitalizationRate: number
  interviewedCases: number
  interviewRate: number
  casesWithExposureLocation: number
  exposureLocationRate: number
  earliestOnset: string | null
  latestOnset: string | null
  outbreakDurationDays: number
}

export interface NodeCaseCount {
  nodeId: string
  nodeName: string
  nodeType: string
  caseCount: number
  hospitalizedCount: number
}

export interface CaseDataResponse {
  epiCurve: EpiCurveDataPoint[]
  summary: CaseSummary
  nodeCaseCounts: NodeCaseCount[]
}

// Monte Carlo types
export interface MonteCarloConfig {
  numFarms: number
  numPackers: number
  numDistributionCenters: number
  numRetailers: number
  retailersWithDelisPct: number
  contaminationRate: number
  contaminationDurationDays: number
  pathogen: string
  inventoryStrategy: InventoryStrategy
  dateWindowDays: number
  simulationDays: number
  interviewSuccessRate: number
  recordCollectionWindowDays: number
  numIterations: number
  baseRandomSeed: number | null
}

export interface HistogramBin {
  binStart: number
  binEnd: number
  count: number
}

export interface MetricStatistics {
  mean: number
  std: number
  min: number
  max: number
  median: number
  p5: number
  p25: number
  p75: number
  p95: number
  histogram: HistogramBin[]
}

export interface IdentificationStatistics {
  yesRate: number  // Rate of correct identifications with clear margin
  noRate: number  // Rate of incorrect identifications with clear margin
  inconclusiveRate: number  // Rate of inconclusive results (top farms too close)
  yesCount: number
  noCount: number
  inconclusiveCount: number
  totalCount: number
  rankDistribution: Record<number, number>
  meanRank: number
  medianRank: number
}

export interface MonteCarloStatusResponse {
  monteCarloId: string
  status: 'pending' | 'running' | 'completed' | 'cancelled' | 'error'
  iterationsCompleted: number
  iterationsTotal: number
  progress: number
  estimatedTimeRemaining: number | null
  message?: string
  startedAt?: string
  completedAt?: string
}

export interface MonteCarloResult {
  monteCarloId: string
  config: MonteCarloConfig
  iterationsCompleted: number
  iterationsFailed: number

  // Expansion metrics
  farmScopeExpansion: MetricStatistics
  tlcScopeExpansion: MetricStatistics
  tlcsLocationExpansion: MetricStatistics
  pathExpansion: MetricStatistics

  // Absolute scope metrics
  detFarmsInScope: MetricStatistics
  detTlcsInScope: MetricStatistics
  detTlcsLocations: MetricStatistics  // TLCS - unique GLNs where TLCs were assigned (deterministic)
  probFarmsInScope: MetricStatistics
  probTlcsInScope: MetricStatistics
  probTlcsLocations: MetricStatistics  // TLCS - unique GLNs where TLCs were assigned (probabilistic)

  // Case metrics
  totalCases: MetricStatistics

  // Identification accuracy
  deterministicIdentification: IdentificationStatistics
  probabilisticIdentification: IdentificationStatistics

  // Investigation timing metrics
  detInvestigationDays?: MetricStatistics
  detInvestigationWorkHours?: MetricStatistics
  probInvestigationDays?: MetricStatistics
  probInvestigationWorkHours?: MetricStatistics
  timingExpansion?: MetricStatistics

  // Statistical tests
  meanExpansion95CI: [number, number]
  identificationDifferenceSignificant: boolean
  identificationPValue: number | null
}
