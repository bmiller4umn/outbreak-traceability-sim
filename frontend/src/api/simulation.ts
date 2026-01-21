import { api } from './client'
import type {
  SimulationConfig,
  SimulationStatusResponse,
  SimulationResult,
  NetworkResponse,
  InvestigationStepsResponse,
  ConvergenceResponse,
  InvestigationScopeResponse,
  FarmTracebackMetricsResponse,
  FarmTracebackMetric,
  InvestigationTier,
  CaseDataResponse,
} from './types'

// Convert frontend config to API request format
function toApiConfig(config: SimulationConfig) {
  return {
    num_farms: config.numFarms,
    num_packers: config.numPackers,
    num_distribution_centers: config.numDistributionCenters,
    num_retailers: config.numRetailers,
    retailers_with_delis_pct: config.retailersWithDelisPct,
    contamination_rate: config.contaminationRate,
    contamination_duration_days: config.contaminationDurationDays,
    pathogen: config.pathogen,
    inventory_strategy: config.inventoryStrategy,
    date_window_days: config.dateWindowDays,
    simulation_days: config.simulationDays,
    random_seed: config.randomSeed,
    // Investigation parameters
    interview_success_rate: config.interviewSuccessRate / 100,  // Convert to decimal
    record_collection_window_days: config.recordCollectionWindowDays,
    num_investigators: config.numInvestigators,
    // Timing parameters for realistic supply chain delays
    transit_speed_factor: config.transitSpeedFactor,
    cooling_hold_hours: config.coolingHoldHours,
    dc_inspection_hours: config.dcInspectionHours,
    retail_stocking_delay_hours: config.retailStockingDelayHours,
  }
}

// Convert API response to frontend format
// Helper to map investigation timing from API response
function mapInvestigationTiming(timing: Record<string, unknown> | undefined) {
  if (!timing) return undefined
  return {
    recordRequestHours: timing.record_request_hours as number,
    tlcAnalysisHours: timing.tlc_analysis_hours as number,
    tracebackHours: timing.traceback_hours as number,
    convergenceAnalysisHours: timing.convergence_analysis_hours as number,
    farmVerificationHours: timing.farm_verification_hours as number,
    totalWorkHours: timing.total_work_hours as number,
    totalCalendarDays: timing.total_calendar_days as number,
    numInvestigators: timing.num_investigators as number,
    directWorkHoursPerDay: timing.direct_work_hours_per_day as number,
    locationsContacted: timing.locations_contacted as number,
    tlcsAnalyzed: timing.tlcs_analyzed as number,
    pathsTraced: timing.paths_traced as number,
    farmsEvaluated: timing.farms_evaluated as number,
    farmsVerified: timing.farms_verified as number,
  }
}

function fromApiResult(data: Record<string, unknown>): SimulationResult {
  const d = data as {
    configuration: {
      simulation_period: { start: string; end: string }
      network: {
        farms: number
        packers: number
        distribution_centers: number
        retailers: number
      }
      pathogen: string
    }
    scenarios: {
      deterministic: Record<string, unknown>
      calculated: Record<string, unknown>
    }
    metrics: Record<string, unknown>
    conclusion: Record<string, unknown>
  }

  return {
    configuration: {
      simulationPeriod: d.configuration.simulation_period,
      network: {
        farms: d.configuration.network.farms,
        packers: d.configuration.network.packers,
        distributionCenters: d.configuration.network.distribution_centers,
        retailers: d.configuration.network.retailers,
      },
      pathogen: d.configuration.pathogen,
    },
    scenarios: {
      deterministic: {
        name: d.scenarios.deterministic.name as string,
        dcMode: d.scenarios.deterministic.dc_mode as string,
        cases: d.scenarios.deterministic.cases as number,
        farmsInScope: d.scenarios.deterministic.farms_in_scope as number,
        tlcsInScope: d.scenarios.deterministic.tlcs_in_scope as number,
        tlcsLocations: d.scenarios.deterministic.tlcs_locations as number,
        tracebackPaths: d.scenarios.deterministic.traceback_paths as number,
        primarySuspect: d.scenarios.deterministic.primary_suspect as string,
        identificationOutcome: d.scenarios.deterministic.identification_outcome as 'yes' | 'no' | 'inconclusive',
        sourceRank: d.scenarios.deterministic.source_rank as number,
        topTwoMargin: d.scenarios.deterministic.top_two_margin as number,
        actualSource: d.scenarios.deterministic.actual_source as string,
        lotLinks: d.scenarios.deterministic.lot_links as { deterministic: number; probabilistic: number },
        investigationTiming: mapInvestigationTiming(d.scenarios.deterministic.investigation_timing as Record<string, unknown> | undefined),
      },
      calculated: {
        name: d.scenarios.calculated.name as string,
        dcMode: d.scenarios.calculated.dc_mode as string,
        cases: d.scenarios.calculated.cases as number,
        farmsInScope: d.scenarios.calculated.farms_in_scope as number,
        tlcsInScope: d.scenarios.calculated.tlcs_in_scope as number,
        tlcsLocations: d.scenarios.calculated.tlcs_locations as number,
        tracebackPaths: d.scenarios.calculated.traceback_paths as number,
        primarySuspect: d.scenarios.calculated.primary_suspect as string,
        identificationOutcome: d.scenarios.calculated.identification_outcome as 'yes' | 'no' | 'inconclusive',
        sourceRank: d.scenarios.calculated.source_rank as number,
        topTwoMargin: d.scenarios.calculated.top_two_margin as number,
        actualSource: d.scenarios.calculated.actual_source as string,
        lotLinks: d.scenarios.calculated.lot_links as { deterministic: number; probabilistic: number },
        farmProbabilities: d.scenarios.calculated.farm_probabilities as Record<string, number>,
        investigationTiming: mapInvestigationTiming(d.scenarios.calculated.investigation_timing as Record<string, unknown> | undefined),
      },
    },
    metrics: {
      sourceFarm: d.metrics.source_farm as string,
      lotsCreatedDeterministic: d.metrics.lots_created_deterministic as number,
      lotsCreatedCalculated: d.metrics.lots_created_calculated as number,
      farmScopeExpansion: d.metrics.farm_scope_expansion as number,
      tlcScopeExpansion: d.metrics.tlc_scope_expansion as number,
      tlcsLocationExpansion: d.metrics.tlcs_location_expansion as number,
      pathExpansion: d.metrics.path_expansion as number,
      timingExpansion: d.metrics.timing_expansion as number | undefined,
    },
    conclusion: {
      deterministicCorrect: d.conclusion.deterministic_correct as boolean,
      calculatedCorrect: d.conclusion.calculated_correct as boolean,
      farmScopeExpansion: d.conclusion.farm_scope_expansion as number,
      tlcScopeExpansion: d.conclusion.tlc_scope_expansion as number,
      impactSummary: d.conclusion.impact_summary as string,
    },
  }
}

export const simulationApi = {
  // Start a new simulation
  run: async (config: SimulationConfig): Promise<{ simulationId: string }> => {
    const data = await api.post<{ simulation_id: string }>('/simulation/run', toApiConfig(config))
    return { simulationId: data.simulation_id }
  },

  // Poll simulation status
  getStatus: async (simulationId: string): Promise<SimulationStatusResponse> => {
    const data = await api.get<Record<string, unknown>>(`/simulation/${simulationId}/status`)
    return {
      simulationId: data.simulation_id as string,
      status: data.status as SimulationStatusResponse['status'],
      progress: data.progress as number,
      message: data.message as string | undefined,
    }
  },

  // Get simulation results
  getResult: async (simulationId: string): Promise<SimulationResult> => {
    const data = await api.get<Record<string, unknown>>(`/simulation/${simulationId}/result`)
    return fromApiResult(data)
  },

  // Get network graph data
  getNetwork: async (simulationId: string): Promise<NetworkResponse> => {
    const data = await api.get<{
      nodes: Array<{
        id: string
        type: string
        name: string
        city: string
        state: string
        is_contaminated: boolean
        is_contamination_source: boolean
        contamination_probability: number
      }>
      edges: Array<{
        id: string
        source: string
        target: string
        product_categories: string[]
        shipment_volume: number
      }>
    }>(`/network/${simulationId}`)

    return {
      nodes: data.nodes.map((n) => ({
        id: n.id,
        type: n.type as NetworkResponse['nodes'][0]['type'],
        name: n.name,
        city: n.city,
        state: n.state,
        isContaminated: n.is_contaminated,
        isContaminationSource: n.is_contamination_source,
        contaminationProbability: n.contamination_probability,
      })),
      edges: data.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        productCategories: e.product_categories,
        shipmentVolume: e.shipment_volume,
      })),
    }
  },

  // Get investigation steps for animation
  getInvestigationSteps: async (simulationId: string): Promise<InvestigationStepsResponse> => {
    const data = await api.get<Record<string, unknown>>(`/investigation/${simulationId}/steps`)
    return {
      deterministicSteps: data.deterministic_steps as InvestigationStepsResponse['deterministicSteps'],
      probabilisticSteps: data.probabilistic_steps as InvestigationStepsResponse['probabilisticSteps'],
      actualSourceFarmId: data.actual_source_farm_id as string | null,
    }
  },

  // Get convergence analysis
  getConvergence: async (simulationId: string): Promise<ConvergenceResponse> => {
    const data = await api.get<Record<string, unknown>>(`/investigation/${simulationId}/convergence`)
    return {
      results: data.results as ConvergenceResponse['results'],
      primarySuspect: data.primary_suspect as ConvergenceResponse['primarySuspect'],
    }
  },

  // Get investigation scope for both modes
  getInvestigationScope: async (simulationId: string): Promise<InvestigationScopeResponse> => {
    const data = await api.get<{
      deterministic: {
        nodes: Array<{ id: string; name: string; type: string; probability: number; city?: string; state?: string }>
        edges: Array<{ id: string; source: string; target: string; probability: number }>
        farms_count: number
        tlcs_count: number
        paths_count: number
      }
      probabilistic: {
        nodes: Array<{ id: string; name: string; type: string; probability: number; city?: string; state?: string }>
        edges: Array<{ id: string; source: string; target: string; probability: number }>
        farms_count: number
        tlcs_count: number
        paths_count: number
      }
      actual_source_farm_id: string | null
    }>(`/investigation/${simulationId}/scope`)

    return {
      deterministic: {
        nodes: data.deterministic.nodes,
        edges: data.deterministic.edges || [],
        farmsCount: data.deterministic.farms_count,
        tlcsCount: data.deterministic.tlcs_count,
        pathsCount: data.deterministic.paths_count,
      },
      probabilistic: {
        nodes: data.probabilistic.nodes,
        edges: data.probabilistic.edges || [],
        farmsCount: data.probabilistic.farms_count,
        tlcsCount: data.probabilistic.tlcs_count,
        pathsCount: data.probabilistic.paths_count,
      },
      actualSourceFarmId: data.actual_source_farm_id,
    }
  },

  // Get farm traceback metrics for both investigation modes
  getFarmTracebackMetrics: async (simulationId: string): Promise<FarmTracebackMetricsResponse> => {
    const data = await api.get<{
      deterministic: {
        mode: string
        farms: Array<{
          farm_id: string
          farm_name: string
          rank: number
          tier: string
          cases_converging: number
          exclusive_cases: number
          total_cases_analyzed: number
          case_coverage_pct: number
          exclusive_case_pct: number
          tlcs_converging: number
          retail_locations: number
          convergence_probability: number
          confidence_score: number
          is_actual_source: boolean
        }>
        total_cases: number
        cases_with_traces: number
        has_clear_leader: boolean
      }
      probabilistic: {
        mode: string
        farms: Array<{
          farm_id: string
          farm_name: string
          rank: number
          tier: string
          cases_converging: number
          exclusive_cases: number
          total_cases_analyzed: number
          case_coverage_pct: number
          exclusive_case_pct: number
          tlcs_converging: number
          retail_locations: number
          convergence_probability: number
          confidence_score: number
          is_actual_source: boolean
        }>
        total_cases: number
        cases_with_traces: number
        has_clear_leader: boolean
      }
      actual_source: {
        farm_id: string | null
        farm_name: string
      }
    }>(`/investigation/${simulationId}/farm-traceback-metrics`)

    const mapFarm = (f: typeof data.deterministic.farms[0]): FarmTracebackMetric => ({
      farmId: f.farm_id,
      farmName: f.farm_name,
      rank: f.rank,
      tier: f.tier as InvestigationTier,
      casesConverging: f.cases_converging,
      exclusiveCases: f.exclusive_cases,
      totalCasesAnalyzed: f.total_cases_analyzed,
      caseCoveragePct: f.case_coverage_pct,
      exclusiveCasePct: f.exclusive_case_pct,
      tlcsConverging: f.tlcs_converging,
      retailLocations: f.retail_locations,
      convergenceProbability: f.convergence_probability,
      confidenceScore: f.confidence_score,
      isActualSource: f.is_actual_source,
    })

    return {
      deterministic: {
        mode: 'deterministic',
        farms: data.deterministic.farms.map(mapFarm),
        totalCases: data.deterministic.total_cases,
        casesWithTraces: data.deterministic.cases_with_traces,
        hasClearLeader: data.deterministic.has_clear_leader,
      },
      probabilistic: {
        mode: 'probabilistic',
        farms: data.probabilistic.farms.map(mapFarm),
        totalCases: data.probabilistic.total_cases,
        casesWithTraces: data.probabilistic.cases_with_traces,
        hasClearLeader: data.probabilistic.has_clear_leader,
      },
      actualSource: {
        farmId: data.actual_source.farm_id,
        farmName: data.actual_source.farm_name,
      },
    }
  },

  // Get case data for visualizations
  getCaseData: async (simulationId: string): Promise<CaseDataResponse> => {
    const data = await api.get<{
      epi_curve: Array<{ date: string; count: number }>
      summary: {
        total_cases: number
        hospitalized_cases: number
        hospitalization_rate: number
        interviewed_cases: number
        interview_rate: number
        cases_with_exposure_location: number
        exposure_location_rate: number
        earliest_onset: string | null
        latest_onset: string | null
        outbreak_duration_days: number
      }
      node_case_counts: Array<{
        node_id: string
        node_name: string
        node_type: string
        case_count: number
        hospitalized_count: number
      }>
    }>(`/investigation/${simulationId}/cases`)

    return {
      epiCurve: data.epi_curve.map((p) => ({
        date: p.date,
        count: p.count,
      })),
      summary: {
        totalCases: data.summary.total_cases,
        hospitalizedCases: data.summary.hospitalized_cases,
        hospitalizationRate: data.summary.hospitalization_rate,
        interviewedCases: data.summary.interviewed_cases,
        interviewRate: data.summary.interview_rate,
        casesWithExposureLocation: data.summary.cases_with_exposure_location,
        exposureLocationRate: data.summary.exposure_location_rate,
        earliestOnset: data.summary.earliest_onset,
        latestOnset: data.summary.latest_onset,
        outbreakDurationDays: data.summary.outbreak_duration_days,
      },
      nodeCaseCounts: data.node_case_counts.map((n) => ({
        nodeId: n.node_id,
        nodeName: n.node_name,
        nodeType: n.node_type,
        caseCount: n.case_count,
        hospitalizedCount: n.hospitalized_count,
      })),
    }
  },
}
