import { api } from './client'
import type {
  MonteCarloConfig,
  MonteCarloStatusResponse,
  MonteCarloResult,
  MetricStatistics,
  IdentificationStatistics,
} from './types'

function toApiConfig(config: MonteCarloConfig) {
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
    interview_success_rate: config.interviewSuccessRate / 100, // Convert to decimal
    record_collection_window_days: config.recordCollectionWindowDays,
    num_iterations: config.numIterations,
    base_random_seed: config.baseRandomSeed,
  }
}

function parseMetricStats(data: Record<string, unknown>): MetricStatistics {
  return {
    mean: data.mean as number,
    std: data.std as number,
    min: data.min as number,
    max: data.max as number,
    median: data.median as number,
    p5: data.p5 as number,
    p25: data.p25 as number,
    p75: data.p75 as number,
    p95: data.p95 as number,
    histogram: (data.histogram as Array<{ bin_start: number; bin_end: number; count: number }>).map(
      (b) => ({
        binStart: b.bin_start,
        binEnd: b.bin_end,
        count: b.count,
      })
    ),
  }
}

function parseIdentificationStats(data: Record<string, unknown>): IdentificationStatistics {
  return {
    yesRate: data.yes_rate as number,
    noRate: data.no_rate as number,
    inconclusiveRate: data.inconclusive_rate as number,
    yesCount: data.yes_count as number,
    noCount: data.no_count as number,
    inconclusiveCount: data.inconclusive_count as number,
    totalCount: data.total_count as number,
    rankDistribution: data.rank_distribution as Record<number, number>,
    meanRank: data.mean_rank as number,
    medianRank: data.median_rank as number,
  }
}

export const monteCarloApi = {
  run: async (config: MonteCarloConfig): Promise<{ monteCarloId: string }> => {
    const data = await api.post<{ monte_carlo_id: string }>(
      '/monte-carlo/run',
      toApiConfig(config)
    )
    return { monteCarloId: data.monte_carlo_id }
  },

  getStatus: async (mcId: string): Promise<MonteCarloStatusResponse> => {
    const data = await api.get<Record<string, unknown>>(`/monte-carlo/${mcId}/status`)
    return {
      monteCarloId: data.monte_carlo_id as string,
      status: data.status as MonteCarloStatusResponse['status'],
      iterationsCompleted: data.iterations_completed as number,
      iterationsTotal: data.iterations_total as number,
      progress: data.progress as number,
      estimatedTimeRemaining: data.estimated_time_remaining_seconds as number | null,
      message: data.message as string | undefined,
      startedAt: data.started_at as string | undefined,
      completedAt: data.completed_at as string | undefined,
    }
  },

  cancel: async (mcId: string): Promise<void> => {
    await api.post(`/monte-carlo/${mcId}/cancel`, {})
  },

  getResult: async (mcId: string): Promise<MonteCarloResult> => {
    const data = await api.get<Record<string, unknown>>(`/monte-carlo/${mcId}/result`)
    const config = data.config as Record<string, unknown>

    return {
      monteCarloId: data.monte_carlo_id as string,
      config: {
        numFarms: config.num_farms as number,
        numPackers: config.num_packers as number,
        numDistributionCenters: config.num_distribution_centers as number,
        numRetailers: config.num_retailers as number,
        retailersWithDelisPct: config.retailers_with_delis_pct as number,
        contaminationRate: config.contamination_rate as number,
        contaminationDurationDays: config.contamination_duration_days as number,
        pathogen: config.pathogen as string,
        inventoryStrategy: config.inventory_strategy as MonteCarloResult['config']['inventoryStrategy'],
        dateWindowDays: config.date_window_days as number,
        simulationDays: config.simulation_days as number,
        interviewSuccessRate: (config.interview_success_rate as number) * 100,
        recordCollectionWindowDays: config.record_collection_window_days as number,
        numIterations: config.num_iterations as number,
        baseRandomSeed: config.base_random_seed as number | null,
      },
      iterationsCompleted: data.iterations_completed as number,
      iterationsFailed: data.iterations_failed as number,
      farmScopeExpansion: parseMetricStats(data.farm_scope_expansion as Record<string, unknown>),
      tlcScopeExpansion: parseMetricStats(data.tlc_scope_expansion as Record<string, unknown>),
      tlcsLocationExpansion: parseMetricStats(data.tlcs_location_expansion as Record<string, unknown>),
      pathExpansion: parseMetricStats(data.path_expansion as Record<string, unknown>),
      detFarmsInScope: parseMetricStats(data.det_farms_in_scope as Record<string, unknown>),
      detTlcsInScope: parseMetricStats(data.det_tlcs_in_scope as Record<string, unknown>),
      detTlcsLocations: parseMetricStats(data.det_tlcs_locations as Record<string, unknown>),
      probFarmsInScope: parseMetricStats(data.prob_farms_in_scope as Record<string, unknown>),
      probTlcsInScope: parseMetricStats(data.prob_tlcs_in_scope as Record<string, unknown>),
      probTlcsLocations: parseMetricStats(data.prob_tlcs_locations as Record<string, unknown>),
      totalCases: parseMetricStats(data.total_cases as Record<string, unknown>),
      deterministicIdentification: parseIdentificationStats(
        data.deterministic_identification as Record<string, unknown>
      ),
      probabilisticIdentification: parseIdentificationStats(
        data.probabilistic_identification as Record<string, unknown>
      ),
      // Investigation timing metrics
      detInvestigationDays: data.det_investigation_days
        ? parseMetricStats(data.det_investigation_days as Record<string, unknown>)
        : undefined,
      detInvestigationWorkHours: data.det_investigation_work_hours
        ? parseMetricStats(data.det_investigation_work_hours as Record<string, unknown>)
        : undefined,
      probInvestigationDays: data.prob_investigation_days
        ? parseMetricStats(data.prob_investigation_days as Record<string, unknown>)
        : undefined,
      probInvestigationWorkHours: data.prob_investigation_work_hours
        ? parseMetricStats(data.prob_investigation_work_hours as Record<string, unknown>)
        : undefined,
      timingExpansion: data.timing_expansion
        ? parseMetricStats(data.timing_expansion as Record<string, unknown>)
        : undefined,
      meanExpansion95CI: data.mean_expansion_95ci as [number, number],
      identificationDifferenceSignificant: data.identification_difference_significant as boolean,
      identificationPValue: data.identification_pvalue as number | null,
    }
  },
}
