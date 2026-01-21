"""
Monte Carlo simulation service.

Manages parallel execution of many simulation iterations and aggregates results.
"""

import asyncio
import uuid
import threading
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum

import numpy as np

from ...simulation.runner import OutbreakSimulator, SimulationConfig
from ...simulation.monte_carlo import (
    MonteCarloConfig,
    MonteCarloAggregateResult,
    MetricStatistics,
    IdentificationStatistics,
)
from ...models.nodes import LotCodeAssignmentMode, CalculatedLotCodeMethod


class MonteCarloStatus(str, Enum):
    """Monte Carlo simulation status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class MonteCarloRun:
    """Tracks a Monte Carlo simulation run."""
    id: str
    config: MonteCarloConfig
    status: MonteCarloStatus = MonteCarloStatus.PENDING
    iterations_completed: int = 0
    iterations_failed: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[MonteCarloAggregateResult] = None
    error: Optional[str] = None
    cancelled: bool = False


def _run_single_iteration(args: tuple) -> Optional[dict]:
    """
    Run a single simulation iteration. Designed for ProcessPoolExecutor.

    Args:
        args: Tuple of (iteration_index, config_dict, random_seed)

    Returns:
        Dictionary of key metrics or None if failed
    """
    iteration_idx, config_dict, random_seed = args

    try:
        # Map inventory strategy to lot code assignment mode
        strategy = config_dict.get("inventory_strategy", "FIFO")
        if strategy in ("FIFO", "LIFO", "ALL_IN_WINDOW", "INVENTORY_WEIGHTED"):
            method_map = {
                "FIFO": CalculatedLotCodeMethod.FIFO_DATE_RANGE,
                "LIFO": CalculatedLotCodeMethod.LIFO_DATE_RANGE,
                "ALL_IN_WINDOW": CalculatedLotCodeMethod.ALL_IN_WINDOW,
                "INVENTORY_WEIGHTED": CalculatedLotCodeMethod.INVENTORY_WEIGHTED,
            }
            dc_method = method_map.get(strategy, CalculatedLotCodeMethod.FIFO_DATE_RANGE)
        else:
            dc_method = None

        sim_days = config_dict.get("simulation_days", 90)
        config = SimulationConfig(
            start_date=date.today() - timedelta(days=sim_days),
            end_date=date.today(),
            num_farms=config_dict.get("num_farms", 5),
            num_packers=config_dict.get("num_packers", 2),
            num_distribution_centers=config_dict.get("num_distribution_centers", 3),
            num_retailers=config_dict.get("num_retailers", 20),
            retailers_with_delis_pct=config_dict.get("retailers_with_delis_pct", 0.3),
            contamination_rate=config_dict.get("contamination_rate", 1.0),
            contamination_duration_days=config_dict.get("contamination_duration_days", 7),
            pathogen=config_dict.get("pathogen", "Salmonella"),
            interview_success_rate=config_dict.get("interview_success_rate", 0.7),
            record_collection_window_days=config_dict.get("record_collection_window_days", 14),
            random_seed=random_seed,
        )

        simulator = OutbreakSimulator(config)
        result = simulator.run_comparison()

        # Extract key metrics
        det = result["scenarios"]["deterministic"]
        calc = result["scenarios"]["calculated"]
        metrics = result["metrics"]

        # Extract investigation timing
        det_timing = det.get("investigation_timing", {})
        calc_timing = calc.get("investigation_timing", {})

        return {
            "iteration": iteration_idx,
            "random_seed": random_seed,
            "farm_scope_expansion": metrics.get("farm_scope_expansion", 1.0),
            "tlc_scope_expansion": metrics.get("tlc_scope_expansion", 1.0),
            "tlcs_location_expansion": metrics.get("tlcs_location_expansion", 1.0),
            "path_expansion": metrics.get("path_expansion", 1.0),
            "det_farms_in_scope": det.get("farms_in_scope", 0),
            "det_tlcs_in_scope": det.get("tlcs_in_scope", 0),
            "det_tlcs_locations": det.get("tlcs_locations", 0),  # TLCS - unique GLNs
            "det_identification_outcome": det.get("identification_outcome", "inconclusive"),
            "det_source_rank": det.get("source_rank", 999),
            "prob_farms_in_scope": calc.get("farms_in_scope", 0),
            "prob_tlcs_in_scope": calc.get("tlcs_in_scope", 0),
            "prob_tlcs_locations": calc.get("tlcs_locations", 0),  # TLCS - unique GLNs
            "prob_identification_outcome": calc.get("identification_outcome", "inconclusive"),
            "prob_source_rank": calc.get("source_rank", 999),
            "total_cases": det.get("cases", 0),
            # Investigation timing metrics
            "det_investigation_days": det_timing.get("total_calendar_days", 0),
            "det_investigation_work_hours": det_timing.get("total_work_hours", 0),
            "prob_investigation_days": calc_timing.get("total_calendar_days", 0),
            "prob_investigation_work_hours": calc_timing.get("total_work_hours", 0),
            "timing_expansion": metrics.get("timing_expansion", 1.0),
        }
    except Exception as e:
        return None


class MonteCarloService:
    """Service for managing Monte Carlo simulation runs."""

    # Maximum number of Monte Carlo runs to keep in memory
    MAX_STORED_RUNS = 20

    def __init__(self):
        self.runs: Dict[str, MonteCarloRun] = {}
        self._lock = threading.Lock()

    def _cleanup_old_runs(self) -> None:
        """Remove oldest completed runs if we've exceeded the limit."""
        with self._lock:
            if len(self.runs) < self.MAX_STORED_RUNS:
                return

            # Get completed runs sorted by completion time (oldest first)
            completed_runs = [
                (run_id, run) for run_id, run in self.runs.items()
                if run.status in (MonteCarloStatus.COMPLETED, MonteCarloStatus.ERROR, MonteCarloStatus.CANCELLED)
                and run.completed_at is not None
            ]
            completed_runs.sort(key=lambda x: x[1].completed_at or datetime.min)

            # Remove oldest runs to get below limit
            num_to_remove = len(self.runs) - self.MAX_STORED_RUNS + 5  # Remove 5 extra for headroom
            for run_id, run in completed_runs[:num_to_remove]:
                # Clear large result data before removing
                run.result = None
                del self.runs[run_id]

    def create_monte_carlo(self, config: dict) -> str:
        """Create a new Monte Carlo run."""
        # Clean up old runs to prevent memory growth
        self._cleanup_old_runs()

        mc_id = str(uuid.uuid4())
        mc_config = MonteCarloConfig(**config)

        run = MonteCarloRun(
            id=mc_id,
            config=mc_config,
            status=MonteCarloStatus.PENDING,
        )
        with self._lock:
            self.runs[mc_id] = run
        return mc_id

    def get_run(self, mc_id: str) -> Optional[MonteCarloRun]:
        """Get a Monte Carlo run by ID."""
        with self._lock:
            return self.runs.get(mc_id)

    def cancel_run(self, mc_id: str) -> bool:
        """Cancel a running Monte Carlo simulation."""
        with self._lock:
            run = self.runs.get(mc_id)
        if run and run.status == MonteCarloStatus.RUNNING:
            run.cancelled = True
            run.status = MonteCarloStatus.CANCELLED
            return True
        return False

    def _run_monte_carlo_sync(self, mc_id: str) -> None:
        """Execute Monte Carlo simulation synchronously (called from thread pool)."""
        with self._lock:
            run = self.runs.get(mc_id)
        if not run:
            return

        config = run.config
        num_workers = config.parallel_workers or max(1, mp.cpu_count() - 1)
        num_workers = min(num_workers, 8)  # Cap at 8 workers

        # Prepare config dict for pickling
        config_dict = {
            "num_farms": config.num_farms,
            "num_packers": config.num_packers,
            "num_distribution_centers": config.num_distribution_centers,
            "num_retailers": config.num_retailers,
            "retailers_with_delis_pct": config.retailers_with_delis_pct,
            "contamination_rate": config.contamination_rate,
            "contamination_duration_days": config.contamination_duration_days,
            "pathogen": config.pathogen,
            "simulation_days": config.simulation_days,
            "interview_success_rate": config.interview_success_rate,
            "record_collection_window_days": config.record_collection_window_days,
            "inventory_strategy": config.inventory_strategy,
        }

        # Prepare iteration arguments
        iteration_args = []
        for i in range(config.num_iterations):
            if config.base_random_seed is not None:
                seed = config.base_random_seed + i
            else:
                seed = None
            iteration_args.append((i, config_dict, seed))

        # Collect results
        results: List[dict] = []

        try:
            with ProcessPoolExecutor(max_workers=num_workers) as executor:
                # Submit all tasks
                futures = {
                    executor.submit(_run_single_iteration, args): args[0]
                    for args in iteration_args
                }

                # Process completed futures
                for future in as_completed(futures):
                    if run.cancelled:
                        executor.shutdown(wait=False, cancel_futures=True)
                        break

                    try:
                        result = future.result(timeout=300)  # 5 min timeout per iteration
                        if result is not None:
                            results.append(result)
                            run.iterations_completed += 1
                        else:
                            run.iterations_failed += 1
                    except Exception:
                        run.iterations_failed += 1

            if not run.cancelled and results:
                # Aggregate results
                run.result = self._aggregate_results(config, results)
                run.status = MonteCarloStatus.COMPLETED

        except Exception as e:
            run.status = MonteCarloStatus.ERROR
            run.error = str(e)

        run.completed_at = datetime.now()

    async def run_monte_carlo(self, mc_id: str) -> None:
        """Execute Monte Carlo simulation asynchronously."""
        run = self.runs.get(mc_id)
        if not run:
            return

        run.status = MonteCarloStatus.RUNNING
        run.started_at = datetime.now()

        # Run the blocking ProcessPoolExecutor work in a thread pool
        # to avoid blocking the asyncio event loop
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._run_monte_carlo_sync, mc_id)

    def _aggregate_results(
        self,
        config: MonteCarloConfig,
        results: List[dict]
    ) -> MonteCarloAggregateResult:
        """Aggregate individual iteration results into statistics."""

        def compute_stats(values: List[float]) -> MetricStatistics:
            arr = np.array(values)
            return MetricStatistics(
                mean=float(np.mean(arr)),
                std=float(np.std(arr)),
                min=float(np.min(arr)),
                max=float(np.max(arr)),
                median=float(np.median(arr)),
                p5=float(np.percentile(arr, 5)),
                p25=float(np.percentile(arr, 25)),
                p75=float(np.percentile(arr, 75)),
                p95=float(np.percentile(arr, 95)),
                values=values,
            )

        def compute_identification_stats(
            outcome_list: List[str],
            rank_list: List[int]
        ) -> IdentificationStatistics:
            total = len(outcome_list)
            yes_count = sum(1 for o in outcome_list if o == "yes")
            no_count = sum(1 for o in outcome_list if o == "no")
            inconclusive_count = sum(1 for o in outcome_list if o == "inconclusive")

            rank_dist: Dict[int, int] = {}
            for r in rank_list:
                rank_dist[r] = rank_dist.get(r, 0) + 1

            return IdentificationStatistics(
                yes_count=yes_count,
                no_count=no_count,
                inconclusive_count=inconclusive_count,
                total_count=total,
                yes_rate=yes_count / total if total > 0 else 0,
                no_rate=no_count / total if total > 0 else 0,
                inconclusive_rate=inconclusive_count / total if total > 0 else 0,
                rank_distribution=rank_dist,
                mean_rank=float(np.mean(rank_list)) if rank_list else 0,
                median_rank=float(np.median(rank_list)) if rank_list else 0,
            )

        # Extract metric arrays
        farm_expansion = [r["farm_scope_expansion"] for r in results]
        tlc_expansion = [r["tlc_scope_expansion"] for r in results]
        tlcs_loc_expansion = [r["tlcs_location_expansion"] for r in results]
        path_expansion = [r["path_expansion"] for r in results]

        det_farms = [r["det_farms_in_scope"] for r in results]
        det_tlcs = [r["det_tlcs_in_scope"] for r in results]
        det_tlcs_locs = [r.get("det_tlcs_locations", 0) for r in results]
        prob_farms = [r["prob_farms_in_scope"] for r in results]
        prob_tlcs = [r["prob_tlcs_in_scope"] for r in results]
        prob_tlcs_locs = [r.get("prob_tlcs_locations", 0) for r in results]

        total_cases = [r["total_cases"] for r in results]

        # Investigation timing metrics
        det_inv_days = [r.get("det_investigation_days", 0) for r in results]
        det_inv_hours = [r.get("det_investigation_work_hours", 0) for r in results]
        prob_inv_days = [r.get("prob_investigation_days", 0) for r in results]
        prob_inv_hours = [r.get("prob_investigation_work_hours", 0) for r in results]
        timing_expansion = [r.get("timing_expansion", 1.0) for r in results]

        det_outcomes = [r["det_identification_outcome"] for r in results]
        det_ranks = [r["det_source_rank"] for r in results]
        prob_outcomes = [r["prob_identification_outcome"] for r in results]
        prob_ranks = [r["prob_source_rank"] for r in results]

        # Compute 95% CI for mean farm expansion
        n = len(farm_expansion)
        mean_exp = np.mean(farm_expansion)
        se = np.std(farm_expansion) / np.sqrt(n) if n > 0 else 0
        ci_95 = (float(mean_exp - 1.96 * se), float(mean_exp + 1.96 * se))

        # McNemar's test for identification difference (yes vs not-yes)
        # Count discordant pairs where one mode got "yes" and other didn't
        b = sum(1 for d, p in zip(det_outcomes, prob_outcomes) if d == "yes" and p != "yes")
        c = sum(1 for d, p in zip(det_outcomes, prob_outcomes) if d != "yes" and p == "yes")

        pvalue = None
        if b + c > 0:
            try:
                from scipy import stats
                chi2 = (abs(b - c) - 1) ** 2 / (b + c) if (b + c) > 0 else 0
                pvalue = float(1 - stats.chi2.cdf(chi2, 1))
            except ImportError:
                # scipy not available, skip test
                pvalue = None

        return MonteCarloAggregateResult(
            config=config,
            num_iterations_completed=len(results),
            num_iterations_failed=config.num_iterations - len(results),
            farm_scope_expansion=compute_stats(farm_expansion),
            tlc_scope_expansion=compute_stats(tlc_expansion),
            tlcs_location_expansion=compute_stats(tlcs_loc_expansion),
            path_expansion=compute_stats(path_expansion),
            det_farms_in_scope=compute_stats([float(x) for x in det_farms]),
            det_tlcs_in_scope=compute_stats([float(x) for x in det_tlcs]),
            det_tlcs_locations=compute_stats([float(x) for x in det_tlcs_locs]),
            prob_farms_in_scope=compute_stats([float(x) for x in prob_farms]),
            prob_tlcs_in_scope=compute_stats([float(x) for x in prob_tlcs]),
            prob_tlcs_locations=compute_stats([float(x) for x in prob_tlcs_locs]),
            total_cases=compute_stats([float(x) for x in total_cases]),
            deterministic_identification=compute_identification_stats(det_outcomes, det_ranks),
            probabilistic_identification=compute_identification_stats(prob_outcomes, prob_ranks),
            # Investigation timing statistics
            det_investigation_days=compute_stats([float(x) for x in det_inv_days]),
            det_investigation_work_hours=compute_stats([float(x) for x in det_inv_hours]),
            prob_investigation_days=compute_stats([float(x) for x in prob_inv_days]),
            prob_investigation_work_hours=compute_stats([float(x) for x in prob_inv_hours]),
            timing_expansion=compute_stats([float(x) for x in timing_expansion]),
            expansion_confidence_interval_95=ci_95,
            identification_difference_pvalue=pvalue,
        )


# Global service instance
monte_carlo_service = MonteCarloService()
